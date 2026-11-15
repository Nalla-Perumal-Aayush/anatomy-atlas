"""Check definition text objects, material colours and curve-to-mesh conversion.

Usage: python inspect_misc.py <file.blend>
"""
import sys
import bpy

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])

print("texts:", len(bpy.data.texts), [t.name for t in list(bpy.data.texts)[:10]])
for n in ("Median nerve.t", "Median nerve.g", "Median nerve.s", "Biceps brachii muscle.t",
          "Deltoid muscle.t", "Humerus.t", "Humerus.g", "Humerus.s"):
    o = bpy.data.objects.get(n)
    if o:
        body = o.data.body if o.type == "FONT" else ""
        print(f"{n!r} {o.type} body={body[:300]!r} parent={o.parent.name if o.parent else None}")

fonts = [o for o in bpy.data.objects if o.type == "FONT"]
for o in fonts[:3] + [f for f in fonts if f.name.endswith(".t")][:3]:
    print("FONT", repr(o.name), repr(o.data.body[:200]))

# text datablocks that look like definitions
for t in bpy.data.texts:
    if "median" in t.name.lower() or "humerus" in t.name.lower():
        print("TEXT", t.name, repr(t.as_string()[:400]))


def base_color(m):
    if m.use_nodes and m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                return tuple(round(v, 3) for v in nd.inputs["Base Color"].default_value)
    return tuple(round(v, 3) for v in m.diffuse_color)


for mname in ("Skin-1", "Skin-in", "Bone", "Cartilage", "Nerve", "Nerve-2", "Artery", "Vein",
              "Fascia", "Tendon", "Ligament", "Flexion", "Abductor", "Bursa", "Lymph-4",
              "Articular capsule"):
    m = bpy.data.materials.get(mname)
    if m:
        print("MAT", mname, base_color(m), "alpha", m.blend_method if hasattr(m, "blend_method") else "")

dg = bpy.context.evaluated_depsgraph_get()
for n in ("Median nerve.r", "Brachial artery.r", "Cephalic vein.r"):
    o = bpy.data.objects[n]
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    print("CURVE->MESH", n, "verts", len(me.vertices), "faces", len(me.polygons),
          "bevel", o.data.bevel_depth, o.data.bevel_object.name if o.data.bevel_object else None)
    ev.to_mesh_clear()

for n in ("Pectoralis major muscle.r", "Latissimus dorsi muscle.r", "Trapezius muscle.r",
          "Serratus anterior muscle.r", "Pectoralis minor muscle.r", "Subclavius muscle.r",
          "Levator scapulae muscle.r", "Rhomboid major muscle.r", "Rhomboid minor muscle.r",
          "Axillary artery.r", "Subclavian artery.r", "Axillary nerve.r", "Lateral cord of brachial plexus.r",
          "Medial cord of brachial plexus.r", "Axillary nodes.r"):
    print("EXISTS", n, n in bpy.data.objects,
          [o.name for o in bpy.data.objects if o.name.lower().startswith(n.split(" muscle")[0].split(".r")[0].lower()) and o.name.endswith(".r")][:4])
