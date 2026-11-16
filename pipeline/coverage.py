"""Compare the atlas against Terminologia Anatomica 2 (TA2) to find missing structures.

For each TA2 term of a discrete kind (muscle, artery, vein, nerve, ligament) it reports whether the term is:
  in_atlas   - exported to the web atlas (as a structure or as a group of structures)
  in_source  - in the Z-Anatomy .blend but not exported by our pipeline
  missing    - not in Z-Anatomy at all

Usage: python coverage.py <metadata.json> <blend_names.json> <col_members.json> <TA2.csv> <out.csv>
blend_names.json: bpy dump of object, collection and text names.
col_members.json: bpy dump of collection name -> all mesh/curve objects inside it (any depth).
A group counts as in the atlas when any of its parts was exported.
"""
import csv
import json
import re
import sys
from collections import Counter

meta_p, blend_p, members_p, ta2_p, out_p = sys.argv[1:6]


def norm(s):
    s = re.sub(r"\.(r|l|j|i|t|g|s|e\d*[rl]?|o\d*[rl]?)$", "", s.strip())
    s = s.strip().strip("()").strip().lower()
    return re.sub(r"\s+", " ", s)


meta = json.load(open(meta_p))["structures"]
atlas = {norm(s["name"]) for s in meta} | {norm(g) for s in meta for g in s["groups"]}
exported = {s["source_name"] for s in meta}
members = json.load(open(members_p))
atlas |= {norm(c) for c, objs in members.items() if any(o in exported for o in objs)}
blend = json.load(open(blend_p))
source = {norm(n) for n, _ in blend["objects"]} | {norm(c) for c in blend["collections"]}

# chapter ranges by TA2 id (first ids found in TA2.csv)
CHAPTERS = [(352, "Skeletal system"), (1515, "Joints"), (1974, "Muscles"), (2750, "Alimentary system"),
            (3133, "Respiratory system"), (3357, "Urinary system"), (3467, "Genital systems"),
            (3699, "Abdominopelvic cavity"), (3852, "Endocrine glands"), (3891, "Cardiovascular system"),
            (5150, "Lymphoid system"), (5363, "Central nervous system"), (6178, "Cranial nerves"),
            (6362, "Spinal and autonomic nerves"), (6861, "Ear and sense organs"), (7135, "Extra Z-Anatomy terms")]


def chapter(i):
    name = "General terms"
    for start, n in CHAPTERS:
        if i >= start:
            name = n
    return name


KINDS = [
    ("muscle", re.compile(r"\bmuscles?\b")),
    ("artery", re.compile(r"\barter(y|ies)\b")),
    ("vein", re.compile(r"\bveins?\b")),
    ("nerve", re.compile(r"\bnerves?\b")),
    ("ligament", re.compile(r"\bligaments?\b")),
]
SKIP = re.compile(r"fascia|bursa|sheath|insertion|branch(es)? to|groove|sulcus|canal|foramen|impression|"
                  r"tubercle|notch|surface|border|margin|fossa|hiatus|opening|of muscles|muscular branches?$")

rows, seen = [], set()
for line in open(ta2_p, encoding="utf-8-sig"):
    p = line.strip().strip('"').split(";")
    if not p[0].isdigit() or int(p[0]) >= 7135:
        continue
    tid, en, la = int(p[0]), p[1].strip(), p[2].strip()
    n = norm(en)
    if n in seen:
        continue
    kind = next((k for k, rx in KINDS if rx.search(n)), None)
    if kind is None or SKIP.search(n):
        continue
    seen.add(n)
    status = "in_atlas" if n in atlas else "in_source" if n in source else "missing"
    variant = en.strip().startswith("(")
    rows.append({"ta2_id": tid, "english": en.strip("()"), "latin": la, "kind": kind, "chapter": chapter(tid),
                 "status": status, "variant": "yes" if variant else ""})

with open(out_p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

print("kind       total  in_atlas  in_source_only  missing")
for k, _ in KINDS:
    c = Counter(r["status"] for r in rows if r["kind"] == k)
    t = sum(c.values())
    print(f"{k:<10}{t:>6}{c['in_atlas']:>10}{c['in_source']:>16}{c['missing']:>9}")
