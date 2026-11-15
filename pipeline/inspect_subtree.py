"""Print selected collection subtrees in detail, plus naming and text-datablock info.

Usage: python inspect_subtree.py <file.blend> <collection name> [<collection name> ...]
"""
import sys
import bpy

path = sys.argv[1]
names = sys.argv[2:]
bpy.ops.wm.open_mainfile(filepath=path)


def walk(col, depth, max_depth=6):
    objs = [o for o in col.objects if o.type in ("MESH", "CURVE")]
    sample = ", ".join(o.name for o in objs[:6])
    print("  " * depth + f"- {col.name} ({len(objs)} geo) {sample}")
    if depth < max_depth:
        for c in col.children:
            walk(c, depth + 1, max_depth)


for n in names:
    col = bpy.data.collections.get(n)
    if col is None:
        print("MISSING", n)
        continue
    print("=" * 60)
    walk(col, 0)

print("=" * 60)
print("texts:", len(bpy.data.texts))
for t in list(bpy.data.texts)[:8]:
    print("  text:", repr(t.name), len(t.as_string()), repr(t.as_string()[:160]))
o = bpy.data.objects.get("Biceps brachii muscle.r") or next(
    (o for o in bpy.data.objects if "iceps brachii" in o.name), None)
if o:
    print("sample obj:", o.name, o.type, dict(o.items()) if o.keys() else {},
          [c.name for c in o.users_collection], o.parent)
