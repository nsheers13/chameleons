"""Step 1: the creature skeleton.

The skeleton is an edge-only mesh wrapped by Mirror, Skin and Subdivision
modifiers. It defines both the blockout shape (via skin radii) and the joint
positions the rig is built from (via one vertex group per named point), so
editing it in Edit Mode reshapes the creature and moves the joints together.
"""

import bpy
import bmesh

from .common import SKELETON, find_by_role, ensure_object_mode, make_active

SKELETON_NAME = "CHM_Skeleton"

# name: (location, skin radius). Only the centre line and the left side
# (x >= 0) are stored; the Mirror modifier makes the right side. The creature
# faces -Y and stands on Z = 0.
POINTS = {
    "tail_5": ((0.0, 1.00, 0.35), 0.02),
    "tail_4": ((0.0, 0.88, 0.38), 0.03),
    "tail_3": ((0.0, 0.76, 0.41), 0.04),
    "tail_2": ((0.0, 0.64, 0.44), 0.05),
    "tail_1": ((0.0, 0.52, 0.47), 0.07),
    "hips": ((0.0, 0.38, 0.50), 0.10),
    "spine_1": ((0.0, 0.20, 0.53), 0.13),
    "spine_2": ((0.0, 0.02, 0.54), 0.14),
    "chest": ((0.0, -0.14, 0.52), 0.12),
    "neck": ((0.0, -0.26, 0.54), 0.08),
    "head": ((0.0, -0.36, 0.56), 0.10),
    "snout": ((0.0, -0.52, 0.53), 0.05),
    "shoulder.L": ((0.08, -0.12, 0.48), 0.05),
    "elbow.L": ((0.16, -0.10, 0.32), 0.035),
    "wrist.L": ((0.15, -0.16, 0.12), 0.03),
    "fingers.L": ((0.16, -0.22, 0.02), 0.025),
    "hip.L": ((0.08, 0.36, 0.46), 0.06),
    "knee.L": ((0.16, 0.30, 0.30), 0.04),
    "ankle.L": ((0.15, 0.38, 0.12), 0.03),
    "toes.L": ((0.16, 0.32, 0.02), 0.025),
}

# Pairs of points joined by an edge, which the Skin modifier turns into a limb.
EDGES = [
    ("tail_5", "tail_4"), ("tail_4", "tail_3"), ("tail_3", "tail_2"),
    ("tail_2", "tail_1"), ("tail_1", "hips"), ("hips", "spine_1"),
    ("spine_1", "spine_2"), ("spine_2", "chest"), ("chest", "neck"),
    ("neck", "head"), ("head", "snout"),
    ("chest", "shoulder.L"), ("shoulder.L", "elbow.L"),
    ("elbow.L", "wrist.L"), ("wrist.L", "fingers.L"),
    ("hips", "hip.L"), ("hip.L", "knee.L"),
    ("knee.L", "ankle.L"), ("ankle.L", "toes.L"),
]


def create_skeleton(context):
    names = list(POINTS)
    mesh = bpy.data.meshes.new(SKELETON_NAME)
    obj = bpy.data.objects.new(SKELETON_NAME, mesh)
    obj["chm_role"] = SKELETON
    context.collection.objects.link(obj)

    bm = bmesh.new()
    skin = bm.verts.layers.skin.verify()
    verts = []
    for name in names:
        co, radius = POINTS[name]
        v = bm.verts.new(co)
        v[skin].radius = (radius, radius)
        v[skin].use_root = name == "hips"
        verts.append(v)
    for a, b in EDGES:
        bm.edges.new((verts[names.index(a)], verts[names.index(b)]))
    bm.to_mesh(mesh)
    bm.free()

    for i, name in enumerate(names):
        obj.vertex_groups.new(name=name).add([i], 1.0, 'REPLACE')

    mirror = obj.modifiers.new("Mirror", 'MIRROR')
    mirror.use_clip = True
    mirror.use_mirror_merge = True
    obj.modifiers.new("Skin", 'SKIN').use_smooth_shade = True
    subsurf = obj.modifiers.new("Subdivision", 'SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 2
    return obj


class CHM_OT_add_skeleton(bpy.types.Operator):
    """Add an editable creature skeleton that defines the blockout and the rig"""
    bl_idname = "chm.add_skeleton"
    bl_label = "Add Creature Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if find_by_role(context, SKELETON):
            self.report({'ERROR'}, "This scene already has a creature skeleton")
            return {'CANCELLED'}
        ensure_object_mode(context)
        make_active(context, create_skeleton(context))
        return {'FINISHED'}


classes = (CHM_OT_add_skeleton,)
