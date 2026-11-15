"""Export the whole body from the Z-Anatomy .blend as web-ready region bundles.

Runs with plain Python + the `bpy` package (pip install bpy). No Blender app needed.

Usage:
    python export.py --blend Startup.blend --out ../build/body --tags depth_tags.csv --ta2 TA2.csv
    python export.py ... --only upper_limb_r            # one bundle

Outputs in --out:
    manifest.json            the bundles, their labels and files
    metadata.json            one entry per structure, all bundles
    <bundle>.raw.glb         one node per structure, named by structure id (compress next)
    <bundle>.content.json    description text for the structures in that bundle
    report.txt               counts, gaps and missing text, for the reviewers
"""
import argparse
import csv
import json
import os
import re
import sys
import tempfile
from collections import Counter

import bpy

# ---------------------------------------------------------------- regions
BUNDLES = [  # (id, label) in loading order
    ("thorax", "Thorax"),
    ("abdomen", "Abdomen"),
    ("pelvis", "Pelvis and perineum"),
    ("neck", "Neck"),
    ("head", "Head"),
    ("upper_limb_r", "Right upper limb"),
    ("upper_limb_l", "Left upper limb"),
    ("lower_limb_r", "Right lower limb"),
    ("lower_limb_l", "Left lower limb"),
    ("brain", "Brain and spinal cord"),
]
DIVISION_TO_REGION = {
    "Head": "head", "Neck": "neck", "Trunk": "trunk",
    "Right upper limb": "upper_limb_r", "Right hand": "upper_limb_r",
    "Left upper limb": "upper_limb_l", "Left hand": "upper_limb_l",
    "Right lower limb": "lower_limb_r", "Right foot": "lower_limb_r",
    "Left lower limb": "lower_limb_l", "Left foot": "lower_limb_l",
}
# Heights (metres, model is standing, feet at 0) measured from the data:
# diaphragm dome 1.26, xiphoid 1.22, iliac crest 1.01, hyoid 1.49-1.51.
Z_HEAD, Z_NECK, Z_THORAX, Z_ABDOMEN = 1.515, 1.40, 1.20, 0.99

KNOWN_GAPS = [
    "Lateral cord of brachial plexus: not modelled in Z-Anatomy",
    "Medial cord of brachial plexus: not modelled in Z-Anatomy",
    "Trunk is split into thorax/abdomen/pelvis by height of each structure's centre, so long structures "
    "(aorta, oesophagus, erector spinae) land in one region only",
]

# ---------------------------------------------------------------- tissue rules
DEFAULT_DEPTH = {
    "skin": 1, "fascia": 3, "muscle": 5, "bursa": 5, "tendon_sheath": 5,
    "nerve": 6, "artery": 6, "vein": 6, "lymph_node": 6,
    "bone": 7, "cartilage": 7, "ligament": 7, "capsule": 7,
    "organ": 7, "heart": 7, "cns": 7, "sense_organ": 7,
}
SYSTEM_OF = {
    "skin": "skin", "fascia": "muscular", "muscle": "muscular", "bursa": "muscular",
    "tendon_sheath": "muscular", "nerve": "nervous", "cns": "nervous", "artery": "vascular",
    "vein": "vascular", "lymph_node": "vascular", "heart": "vascular", "bone": "skeletal",
    "cartilage": "skeletal", "ligament": "skeletal", "capsule": "skeletal", "organ": "organs",
    "sense_organ": "organs",
}
# Flat colours per material kind (sRGB 0..1, alpha).
PALETTE = {
    "skin": (0.87, 0.67, 0.55, 1.0), "skin_inner": (0.80, 0.45, 0.40, 1.0),
    "fascia": (0.85, 0.88, 0.90, 0.55), "muscle": (0.72, 0.20, 0.18, 1.0),
    "tendon": (0.93, 0.89, 0.82, 1.0), "bursa": (0.55, 0.75, 0.85, 0.5),
    "tendon_sheath": (0.75, 0.80, 0.90, 0.7), "nerve": (0.98, 0.85, 0.25, 1.0),
    "artery": (0.85, 0.10, 0.10, 1.0), "vein": (0.20, 0.30, 0.85, 1.0),
    "lymph_node": (0.45, 0.75, 0.35, 1.0), "bone": (0.93, 0.90, 0.82, 1.0),
    "tooth": (0.97, 0.96, 0.92, 1.0), "cartilage": (0.70, 0.80, 0.90, 1.0),
    "ligament": (0.80, 0.85, 0.80, 1.0), "capsule": (0.78, 0.75, 0.88, 1.0),
    "heart": (0.62, 0.14, 0.15, 1.0), "organ": (0.76, 0.46, 0.40, 1.0),
    "lung": (0.88, 0.62, 0.64, 1.0), "intestine": (0.84, 0.62, 0.52, 1.0),
    "liver": (0.50, 0.20, 0.17, 1.0), "gland": (0.86, 0.70, 0.42, 1.0),
    "mucosa": (0.90, 0.55, 0.56, 1.0), "peritoneum": (0.90, 0.86, 0.78, 0.45),
    "sense_organ": (0.86, 0.83, 0.78, 1.0), "cornea": (0.80, 0.90, 0.95, 0.4),
    "cns": (0.88, 0.76, 0.74, 1.0), "cns_white": (0.95, 0.93, 0.88, 1.0),
    "cns_nucleus": (0.66, 0.50, 0.62, 1.0), "cns_frontal": (0.90, 0.72, 0.62, 1.0),
    "cns_parietal": (0.72, 0.80, 0.90, 1.0), "cns_temporal": (0.74, 0.86, 0.70, 1.0),
    "cns_occipital": (0.92, 0.84, 0.58, 1.0), "cns_limbic": (0.86, 0.70, 0.86, 1.0),
    "cns_insula": (0.70, 0.84, 0.84, 1.0), "cns_cerebellum": (0.82, 0.66, 0.60, 1.0),
}

# Muscles drawn at layer 4. Everything else is layer 5 unless depth_tags.csv says otherwise.
SUPERFICIAL_MUSCLE = re.compile(
    r"platysma|sternocleidomastoid|trapezius|latissimus dorsi|pectoralis major|deltoid muscle|part of deltoid|"
    r"external abdominal oblique|rectus abdominis|pyramidalis|gluteus maximus|tensor fasciae latae|sartorius|"
    r"gracilis|rectus femoris|vastus lateralis|vastus medialis|adductor longus|pectineus|long head of biceps femoris|"
    r"semitendinosus|gastrocnemius|tibialis anterior|extensor digitorum longus|fibularis longus|abductor hallucis|"
    r"abductor digiti minimi|flexor digitorum brevis|brachioradialis|biceps brachii|long head of triceps|"
    r"lateral head of triceps|pronator teres|flexor carpi|palmaris longus|extensor carpi|extensor digitorum$|"
    r"extensor digiti minimi|anconeus|abductor pollicis brevis|superficial head|flexor digiti minimi of hand|"
    r"occipitofrontalis|frontalis|orbicularis|zygomaticus|risorius|depressor|levator labii|nasalis|procerus|"
    r"mentalis|temporoparietalis|auricular muscle|masseter"
)
# Nerves, veins and nodes that run in the superficial fascia: layer 2.
SUPERFICIAL_NV = re.compile(
    r"cutaneous|cephalic vein|basilic vein|median cubital|median antebrachial|saphenous|dorsal venous|"
    r"digital veins|external jugular|anterior jugular|superficial .*vein|superficial .*nodes|"
    r"supratrochlear nodes|cubital nodes|dorsal digital branches|palmar branch of|dorsal branch of ulnar|"
    r"superficial branch of radial|superficial fibular nerve|sural nerve"
)
MAX_PARAGRAPHS = 30

# Catch-all groups whose text is too general to use as a structure's description.
GENERIC_GROUPS = {
    "Nerves", "Systemic arteries", "Systemic veins", "Tendon sheaths", "Joints of hand", "Muscles",
    "Bonus collection", "Peripheral nervous system", "Superficial muscles", "Ligaments", "Bursae",
    "Fasciae", "Central nervous system", "Sense organs", "Lymphoid system", "Digestive system",
}


def tissue_of(obj, top_system, in_cns, in_sense):
    mats = [m.name.lower() for m in getattr(obj.data, "materials", []) if m]
    has = lambda p: any(m.startswith(p) for m in mats)  # noqa: E731
    sysn = top_system[:1]
    if sysn == "9":
        return "skin" if has("skin") else None
    if sysn == "7":
        if obj.type == "CURVE" or has("nerve"):
            return "nerve"
        return "cns" if in_cns else "sense_organ"
    if sysn == "8":
        return "organ"
    if sysn == "6":
        return "lymph_node" if has("lymph") else "organ"
    if sysn == "5":
        if has("artery") or has("pulmonary artery"):
            return "artery"
        if has("vein"):
            return "vein"
        return "heart" if obj.type == "MESH" else "artery"
    if has("skin"):
        return "skin"
    if has("fascia"):
        return "fascia"
    if has("bursa"):
        return "bursa"
    if has("articular capsule"):
        return "tendon_sheath" if sysn == "4" else "capsule"
    if sysn == "4":
        return "muscle"
    if has("bone") or has("teeth"):
        return "bone"
    if has("cartilage"):
        return "cartilage"
    return "ligament" if sysn == "3" else "bone"


LOBES = ["frontal", "parietal", "temporal", "occipital", "limbic", "insula", "cerebellum"]


def material_kind(mat_name, tissue):
    n = mat_name.lower()
    if n.startswith("tendon"):
        return "tendon"
    if n == "skin-in":
        return "skin_inner"
    if tissue in ("bone", "cartilage"):
        if n.startswith("teeth"):
            return "tooth"
        return "cartilage" if n.startswith("cartilage") else "bone"
    if tissue == "cns":
        if n.startswith("white matter"):
            return "cns_white"
        if n.startswith("nucleus"):
            return "cns_nucleus"
        for lobe in LOBES:
            if n.startswith(lobe):
                return "cns_" + lobe
        return "cns"
    if tissue in ("organ", "sense_organ"):
        for k in ("lung", "intestine", "liver", "gland", "mucosa", "peritoneum", "cornea"):
            if n.startswith(k):
                return k
        return tissue
    return tissue


# ---------------------------------------------------------------- helpers
SIDE_RE = re.compile(r"\.(r|l)$")


def display_name(blender_name):
    n = SIDE_RE.sub("", blender_name).strip().rstrip("'*").strip()
    if n.startswith("(") and n.endswith(")") and n.count("(") == 1:
        n = n[1:-1].strip()  # Z-Anatomy wraps some names in brackets; keep "(VII)" style suffixes
    return n


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def parse_text(raw):
    lines = [l.rstrip() for l in raw.splitlines()]
    url, body, title = None, [], None
    for l in lines:
        s = l.strip()
        if not s:
            body.append("")
            continue
        if s.startswith("http"):
            url = s
            continue
        if title is None and s.upper() == s and any(c.isalpha() for c in s):
            title = s
            continue
        m = re.match(r"^=+\s*(.*?)\s*=+$", s)
        body.append(f"## {m.group(1)}" if m else s)
    paras = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(body)) if p.strip()]
    # long Wikipedia articles: keep the opening, link to the rest
    return {"title": title, "paragraphs": paras[:MAX_PARAGRAPHS], "truncated": len(paras) > MAX_PARAGRAPHS,
            "source_url": url}


def read_tags(path):
    """depth_tags.csv; names may carry .r/.l, tags apply to both sides."""
    tags = {}
    with open(path, newline="") as f:
        rows = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    for row in csv.DictReader(rows):
        tags[display_name(row["name"].strip()).lower()] = (int(row["depth"]), (row.get("note") or "").strip())
    return tags


def read_ta2(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            parts = line.strip().strip('"').split(";")
            if len(parts) >= 3 and parts[0].isdigit():
                out.setdefault(parts[1].strip().lower(), (parts[0], parts[2].strip()))
    return out


def find_text(disp, groups):
    """Own text, else the parent structure (a muscle head -> the muscle), else the closest group."""
    t = bpy.data.texts.get(disp) or bpy.data.texts.get(f"({disp})")
    if t is not None:
        return t, slug(disp), None
    cands = []
    m = re.match(r"^.*?\b(?:head|part|belly|branch(?:es)?) of (?:the )?(.+)$", disp, re.I)
    if m:
        parent = m.group(1)[0].upper() + m.group(1)[1:]
        cands += [parent, parent + " muscle", re.sub(r" muscle$", "", parent)]
    low = disp.lower()
    cands += sorted((g for g in groups if g not in GENERIC_GROUPS),
                    key=lambda g: re.sub(r" muscle$", "", g.lower()) not in low)
    for c in cands:
        t = bpy.data.texts.get(c)
        if t is not None:
            return t, slug(c), c
    return None, None, None


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tags", required=True)
    ap.add_argument("--ta2")
    ap.add_argument("--only", help="comma-separated bundle ids to export")
    ap.add_argument("--curve-bevel", type=int, default=2, help="tube roundness for nerves/vessels (source: 4)")
    ap.add_argument("--curve-res", type=int, default=5, help="tube smoothness along length (source: 12)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tags = read_tags(a.tags)
    ta2 = read_ta2(a.ta2) if a.ta2 else {}
    only = set(a.only.split(",")) if a.only else None

    bpy.ops.wm.open_mainfile(filepath=a.blend)
    scene = bpy.context.scene
    top = [c for c in scene.collection.children if re.match(r"^\d:", c.name)]
    top_of = {}
    for c in top:
        for o in c.all_objects:
            top_of.setdefault(o.name, c.name)
    division_of = {}
    for d in bpy.data.collections["Main divisions"].children:
        for o in d.all_objects:
            division_of.setdefault(o.name, d.name)
    cns = {o.name for o in bpy.data.collections["Central nervous system"].all_objects}
    sense = {o.name for o in bpy.data.collections["Sense organs"].all_objects}

    # lighter tubes for nerves and vessels
    for cu in bpy.data.curves:
        cu.bevel_resolution = min(cu.bevel_resolution, a.curve_bevel)
        cu.resolution_u = min(cu.resolution_u, a.curve_res)

    simple = {}
    for kind, rgba in PALETTE.items():
        m = bpy.data.materials.new(f"atlas_{kind}")
        m.diffuse_color = rgba
        m.use_nodes = True
        bsdf = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*rgba[:3], 1.0)
        bsdf.inputs["Alpha"].default_value = rgba[3]
        bsdf.inputs["Roughness"].default_value = 0.6
        simple[kind] = m

    dg = bpy.context.evaluated_depsgraph_get()
    per_bundle = {b: [] for b, _ in BUNDLES}
    meta, contents, report, seen = [], {b: {} for b, _ in BUNDLES}, [], set()

    for o in sorted(bpy.data.objects, key=lambda x: x.name):
        if o.type not in ("MESH", "CURVE") or o.name not in top_of:
            continue
        if not (SIDE_RE.search(o.name) or "." not in o.name):
            continue  # labels (.j .i .t ...), attachment areas (.er .or ...)
        top_sys = top_of[o.name]
        tissue = tissue_of(o, top_sys, o.name in cns, o.name in sense)
        if tissue is None:
            continue
        side = {"r": "right", "l": "left"}.get((SIDE_RE.search(o.name) or [None, None])[1], "midline")

        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=dg)
        if me is None or len(me.polygons) == 0:
            report.append(f"EMPTY geometry, skipped: {o.name}")
            continue
        me.transform(o.matrix_world)
        xs = [v.co for v in me.vertices]
        cz = (min(v.z for v in xs) + max(v.z for v in xs)) / 2
        cx = (min(v.x for v in xs) + max(v.x for v in xs)) / 2

        # region
        if tissue == "cns":
            region = "brain"
        else:
            region = DIVISION_TO_REGION.get(division_of.get(o.name, ""), None)
            if region is None:
                region = "head" if cz >= Z_HEAD else "neck" if cz >= Z_NECK else "trunk"
            if region == "trunk":
                region = "thorax" if cz >= Z_THORAX else "abdomen" if cz >= Z_ABDOMEN else "pelvis"
            if region.endswith(("_r", "_l")):  # Z-Anatomy files a few left parts under right groups
                want = "_r" if side == "right" else "_l" if side == "left" else ("_r" if cx < 0 else "_l")
                region = region[:-2] + want
        if only and region not in only:
            bpy.data.meshes.remove(me)
            continue

        for i, slot_mat in enumerate(me.materials):
            me.materials[i] = simple[material_kind(slot_mat.name if slot_mat else "", tissue)]
        if len(me.materials) == 0:
            me.materials.append(simple[material_kind("", tissue)])

        disp = display_name(o.name)
        sid = slug(disp) + {"right": "_r", "left": "_l", "midline": ""}[side]
        if sid in seen or not sid:
            report.append(f"DUPLICATE id {sid} from {o.name}, skipped")
            bpy.data.meshes.remove(me)
            continue
        seen.add(sid)
        me.name = sid
        per_bundle[region].append(bpy.data.objects.new(sid, me))

        groups = [c.name for c in o.users_collection if not re.match(r"^\d:", c.name)
                  and c.name not in DIVISION_TO_REGION and c.name != "Main divisions"]
        low = disp.lower()
        if low in tags:
            depth, note = tags[low]
        elif tissue == "muscle":
            depth, note = (4 if SUPERFICIAL_MUSCLE.search(low) or "Superficial muscles" in groups else 5), ""
        elif tissue in ("nerve", "vein", "lymph_node") and SUPERFICIAL_NV.search(low):
            depth, note = 2, ""
        else:
            depth, note = DEFAULT_DEPTH[tissue], ""
        txt, cref, shared = find_text(disp, groups)
        innervation = [g for g in groups if tissue == "muscle" and re.search(r"\bnerves?\b", g, re.I)
                       and g not in GENERIC_GROUPS]
        ta = ta2.get(low) or ta2.get(re.sub(r" muscle$", "", low))
        meta.append({
            "id": sid, "name": disp, "source_name": o.name, "side": side, "region": region,
            "system": SYSTEM_OF[tissue], "tissue": tissue, "depth": depth, "depth_note": note,
            "groups": groups, "content_ref": cref, "content_shared_from": shared,
            "innervation": innervation, "latin": ta[1] if ta else None, "ta2_id": ta[0] if ta else None,
        })
        if txt is None:
            report.append(f"NO description text: {disp} ({region})")
        elif cref not in contents[region]:
            parsed = parse_text(txt.as_string())
            parsed.update({"source": "Z-Anatomy (CC BY-SA 4.0), text based on Wikipedia",
                           "reviewed_by": None, "reviewed_on": None})
            contents[region][cref] = parsed

    # write each bundle's baked objects to its own temp .blend, then export them one by one
    tmpdir = tempfile.mkdtemp()
    todo = []
    for b, _ in BUNDLES:
        if per_bundle[b]:
            p = os.path.join(tmpdir, f"{b}.blend")
            bpy.data.libraries.write(p, set(per_bundle[b]), fake_user=True)
            todo.append((b, p))
    for b, p in todo:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        with bpy.data.libraries.load(p, link=False) as (src, dst):
            dst.objects = list(src.objects)
        for ob in dst.objects:
            bpy.context.scene.collection.objects.link(ob)
        bpy.ops.export_scene.gltf(filepath=os.path.join(a.out, f"{b}.raw.glb"), export_format="GLB",
                                  export_yup=True, export_normals=True, export_texcoords=False,
                                  export_materials="EXPORT", export_extras=False)
        with open(os.path.join(a.out, f"{b}.content.json"), "w") as f:
            json.dump(contents[b], f, ensure_ascii=False, separators=(",", ":"))

    # metadata and manifest (merge with an earlier run when exporting --only some bundles)
    meta_path = os.path.join(a.out, "metadata.json")
    if only and os.path.exists(meta_path):
        old = json.load(open(meta_path))["structures"]
        meta = [m for m in old if m["region"] not in only] + meta
    meta.sort(key=lambda m: (m["region"], m["depth"], m["name"]))
    with open(meta_path, "w") as f:
        json.dump({"structures": meta}, f, separators=(",", ":"))
    count = Counter(m["region"] for m in meta)
    manifest = {"bundles": [{"id": b, "label": lab, "count": count[b], "model": f"{b}.glb",
                             "content": f"{b}.content.json"} for b, lab in BUNDLES if count[b]]}
    with open(os.path.join(a.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)

    with open(os.path.join(a.out, "report.txt"), "w") as f:
        f.write(f"Exported {len(meta)} structures\n\nBy region:\n")
        for b, lab in BUNDLES:
            f.write(f"  {lab:<24} {count[b]}\n")
        f.write("\nBy depth and tissue:\n")
        for k, v in sorted(Counter((m["depth"], m["tissue"]) for m in meta).items()):
            f.write(f"  depth {k[0]}  {k[1]:<14} {v}\n")
        mus = [m for m in meta if m["tissue"] == "muscle"]
        f.write(f"\nMuscles with nerve supply filled: {sum(1 for m in mus if m['innervation'])} of {len(mus)}\n")
        f.write(f"Structures with description text: {sum(1 for m in meta if m['content_ref'])} of {len(meta)}\n")
        f.write("\nKnown gaps in source data:\n")
        for g in KNOWN_GAPS:
            f.write(f"  {g}\n")
        f.write("\nPipeline notes:\n")
        for r in report:
            f.write(f"  {r}\n")
    print(f"done: {len(meta)} structures in {len(manifest['bundles'])} bundles -> {a.out}")


if __name__ == "__main__":
    sys.exit(main())
