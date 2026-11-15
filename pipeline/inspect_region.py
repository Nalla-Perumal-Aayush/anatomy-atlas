"""Explore region grouping, name suffixes and object kinds for the upper limb.

Usage: python inspect_region.py <file.blend>
"""
import sys
import re
from collections import Counter
import bpy

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])

suf = Counter()
for o in bpy.data.objects:
    m = re.search(r"\.([a-z])$", o.name)
    suf[(m.group(1) if m else "-", o.type)] += 1
print("suffix x type:", sorted(suf.items(), key=lambda x: -x[1])[:30])

md = bpy.data.collections.get("Main divisions")


def walk(col, depth, max_depth):
    geo = [o for o in col.all_objects if o.type in ("MESH", "CURVE")]
    print("  " * depth + f"- {col.name} ({len(geo)} geo all)")
    if depth < max_depth:
        for c in col.children:
            walk(c, depth + 1, max_depth)


walk(md, 0, 3)

# Top-level system collection per object
systems = [c for c in bpy.context.scene.collection.children if c.name[:2] in
           {f"{i}:" for i in range(1, 10)}]
for c in bpy.data.collections:
    if c.name.lower() in ("upper limb", "free part of upper limb"):
        geo = [o for o in c.all_objects if o.type in ("MESH", "CURVE")]
        print("\nREGION", c.name, len(geo))
        cnt = Counter()
        for o in geo:
            sysname = next((s.name for s in systems if o.name in s.all_objects), "?")
            cnt[(sysname, o.type, o.name[-2:])] += 1
        for k, v in sorted(cnt.items(), key=lambda x: -x[1])[:40]:
            print("  ", k, v)
        names = sorted(o.name for o in geo if o.name.endswith(".r"))
        print("  sample .r:", names[:60])
