"""Step 4: posing helpers."""

import bpy

from .common import RIG, find_by_role


def active_rig(context):
    obj = context.object
    return obj if obj and obj.type == 'ARMATURE' else find_by_role(context, RIG)


class CHM_OT_reset_pose(bpy.types.Operator):
    """Return every bone of the rig to its rest position"""
    bl_idname = "chm.reset_pose"
    bl_label = "Reset Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = active_rig(context)
        if not rig:
            self.report({'ERROR'}, "No rig found")
            return {'CANCELLED'}
        for bone in rig.pose.bones:
            bone.location = (0, 0, 0)
            bone.rotation_quaternion = (1, 0, 0, 0)
            bone.rotation_euler = (0, 0, 0)
            bone.scale = (1, 1, 1)
        return {'FINISHED'}


class CHM_OT_key_pose(bpy.types.Operator):
    """Keyframe every bone of the rig on the current frame"""
    bl_idname = "chm.key_pose"
    bl_label = "Key Whole Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = active_rig(context)
        if not rig:
            self.report({'ERROR'}, "No rig found")
            return {'CANCELLED'}
        for bone in rig.pose.bones:
            rotation = "rotation_quaternion" if bone.rotation_mode == 'QUATERNION' else "rotation_euler"
            for path in ("location", rotation, "scale"):
                bone.keyframe_insert(path, group=bone.name)
        self.report({'INFO'}, f"Keyed frame {context.scene.frame_current}")
        return {'FINISHED'}


classes = (CHM_OT_reset_pose, CHM_OT_key_pose)
