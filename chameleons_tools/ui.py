"""Sidebar panel (N panel > Chameleons) laying out the workflow in order."""

import bpy


class CHM_PT_workflow(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Chameleons"
    bl_label = "Creature Workflow"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        box = layout.box()
        box.label(text="1. Block out", icon='OUTLINER_OB_MESH')
        box.operator("chm.add_skeleton", icon='ADD')
        box.label(text="Edit points; Ctrl+A scales thickness")

        box = layout.box()
        box.label(text="2. Sculpt", icon='SCULPTMODE_HLT')
        box.prop(scene, "chm_voxel_size")
        box.operator("chm.make_sculpt_mesh")
        box.operator("chm.remesh")
        row = box.row(align=True)
        row.prop(scene, "chm_multires_levels", text="Levels")
        row.operator("chm.add_multires")

        box = layout.box()
        box.label(text="3. Rig", icon='ARMATURE_DATA')
        box.operator("chm.build_rig")
        box.operator("chm.bind_mesh")

        box = layout.box()
        box.label(text="4. Pose", icon='POSE_HLT')
        box.operator("chm.reset_pose")
        box.operator("chm.key_pose")


classes = (CHM_PT_workflow,)
