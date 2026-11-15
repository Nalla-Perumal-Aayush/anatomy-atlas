"""Whole-body inventory of the Z-Anatomy .blend: what would be exported, by system, region and suffix.

Usage: python inventory.py <file.blend> <out.tsv>
"""
import re
import sys
from collections import Counter

import bpy

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scene = bpy.context.scene
top = [c for c in scene.collection.children if re.match(r"^\d:", c.name)]
top_of = {}
for c in top:
    for o in c.all_objects:
        top_of.setdefault(o.name, c.name)

divs = bpy.data.collections["Main divisions"]
div_of = {}
for d in divs.children:
    for o in d.all_objects:
        div_of.setdefault(o.name, d.name)

rows = []
suf = Counter()
for o in bpy.data.objects:
    if o.type not in ("MESH", "CURVE") or o.name not in top_of:
        continue
    m = re.search(r"\.([a-z0-9]+)$", o.name)
    s = m.group(1) if m else "-"
    suf[s] += 1
    if s not in ("r", "l", "-"):
        continue
    nv = len(o.data.vertices) if o.type == "MESH" else 0
    mats = ",".join(mt.name for mt in getattr(o.data, "materials", []) if mt)
    c = o.matrix_world.translation
    rows.append((o.name, o.type, top_of[o.name], div_of.get(o.name, "?"), str(nv), mats,
                 f"{c.x:.3f},{c.y:.3f},{c.z:.3f}", str(o.hide_viewport or o.hide_get() if hasattr(o, 'hide_get') else '')))

print("suffixes:", suf.most_common(25))
print("kept:", len(rows))
print("by system:", Counter(r[2] for r in rows).most_common())
print("by division:", Counter(r[3] for r in rows).most_common())
print("by type:", Counter(r[1] for r in rows).most_common())
print("total mesh verts:", sum(int(r[4]) for r in rows))
with open(sys.argv[2], "w") as f:
    for r in rows:
        f.write("\t".join(r) + "\n")
