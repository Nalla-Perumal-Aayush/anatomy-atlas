"""Print the collection tree of the Z-Anatomy .blend with object counts.

Usage: python inspect_blend.py <file.blend> [max_depth]
"""
import sys
import bpy

path = sys.argv[1]
max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 3
bpy.ops.wm.open_mainfile(filepath=path)

print("objects:", len(bpy.data.objects), "meshes:", len(bpy.data.meshes),
      "collections:", len(bpy.data.collections))
types = {}
for o in bpy.data.objects:
    types[o.type] = types.get(o.type, 0) + 1
print("object types:", types)


def count_mesh(col):
    n = sum(1 for o in col.objects if o.type == "MESH")
    return n + sum(count_mesh(c) for c in col.children)


def walk(col, depth):
    if depth > max_depth:
        return
    print("  " * depth + f"{col.name}  [{count_mesh(col)} meshes, {len(col.objects)} direct]")
    for c in col.children:
        walk(c, depth + 1)


for c in bpy.context.scene.collection.children:
    walk(c, 0)
