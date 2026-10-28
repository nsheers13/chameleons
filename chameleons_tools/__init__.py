"""Chameleons Tools: a block out -> sculpt -> rig -> pose workflow for creatures."""

import bpy

from . import skeleton, sculpt, rig, pose, ui

classes = skeleton.classes + sculpt.classes + rig.classes + pose.classes + ui.classes


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.chm_voxel_size = bpy.props.FloatProperty(
        name="Voxel Size",
        description="Detail of the remeshed sculpt body; smaller is denser",
        default=0.008, min=0.001, max=0.1, precision=4, unit='LENGTH',
    )
    bpy.types.Scene.chm_multires_levels = bpy.props.IntProperty(
        name="Multires Levels",
        description="How many detail levels to add at once",
        default=2, min=1, max=4,
    )


def unregister():
    del bpy.types.Scene.chm_multires_levels
    del bpy.types.Scene.chm_voxel_size
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
