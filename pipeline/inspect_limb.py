"""List objects in the right upper limb + right hand groups by system.

Usage: python inspect_limb.py <file.blend> <out.tsv>
"""
import sys
from collections import Counter
import bpy

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
systems = [c for c in bpy.context.scene.collection.children
           if c.name[:2] in {f"{i}:" for i in range(1, 10)}]
sysmap = {}
for s in systems:
    for o in s.all_objects:
        sysmap.setdefault(o.name, s.name)

objs = {}
for cname in ("Right upper limb", "Right hand"):
    for o in bpy.data.collections[cname].all_objects:
        if o.type in ("MESH", "CURVE"):
            objs[o.name] = o

cnt = Counter()
rows = []
for name, o in sorted(objs.items()):
    sysname = sysmap.get(name, "?")
    nverts = len(o.data.vertices) if o.type == "MESH" else -1
    mats = [m.name for m in o.data.materials if m] if hasattr(o.data, "materials") else []
    cnt[(sysname, o.type, name[-2:])] += 1
    rows.append((name, o.type, sysname, str(nverts), ",".join(mats),
                 ";".join(c.name for c in o.users_collection)))
for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
    print(k, v)
with open(sys.argv[2], "w") as f:
    for r in rows:
        f.write("\t".join(r) + "\n")
print("rows", len(rows))
