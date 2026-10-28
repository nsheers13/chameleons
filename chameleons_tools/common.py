"""Helpers shared by the workflow steps."""

import bpy

# Objects made by the add-on are tagged with obj["chm_role"] so later steps
# can find them even after the user renames them.
SKELETON = "skeleton"
BODY = "body"
RIG = "rig"


def find_by_role(context, role):
    return next((o for o in context.scene.objects if o.get("chm_role") == role), None)


def ensure_object_mode(context):
    if context.object and context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def make_active(context, obj):
    for o in context.view_layer.objects.selected:
        o.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
