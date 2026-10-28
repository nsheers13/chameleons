"""Step 2: turn the skeleton into a sculptable mesh and manage resolution."""

import bmesh
import bpy

from .common import SKELETON, BODY, find_by_role, ensure_object_mode, make_active

BODY_NAME = "CHM_Body"


def voxel_remesh(context, obj, voxel_size):
    obj.data.remesh_voxel_size = voxel_size
    with context.temp_override(active_object=obj, object=obj, selected_objects=[obj]):
        bpy.ops.object.voxel_remesh()


def close_holes(mesh):
    """The Skin modifier leaves small holes at branching joints, and the voxel
    remesher turns any opening into noise across the whole surface."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()


class CHM_OT_make_sculpt_mesh(bpy.types.Operator):
    """Bake the skeleton blockout into a remeshed body and start sculpting"""
    bl_idname = "chm.make_sculpt_mesh"
    bl_label = "Make Sculpt Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        skeleton = find_by_role(context, SKELETON)
        if not skeleton:
            self.report({'ERROR'}, "Add a creature skeleton first")
            return {'CANCELLED'}
        if find_by_role(context, BODY):
            self.report({'ERROR'}, "This scene already has a sculpt body; delete it to rebuild")
            return {'CANCELLED'}
        ensure_object_mode(context)

        depsgraph = context.evaluated_depsgraph_get()
        mesh = bpy.data.meshes.new_from_object(skeleton.evaluated_get(depsgraph))
        mesh.name = BODY_NAME
        close_holes(mesh)
        body = bpy.data.objects.new(BODY_NAME, mesh)
        body["chm_role"] = BODY
        body.matrix_world = skeleton.matrix_world.copy()
        context.collection.objects.link(body)

        voxel_remesh(context, body, context.scene.chm_voxel_size)
        mesh.shade_smooth()
        mesh.use_mirror_x = True
        skeleton.hide_set(True)

        make_active(context, body)
        bpy.ops.object.mode_set(mode='SCULPT')
        return {'FINISHED'}


class CHM_OT_remesh(bpy.types.Operator):
    """Voxel remesh the sculpt body to even out stretched topology"""
    bl_idname = "chm.remesh"
    bl_label = "Remesh Body"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body = find_by_role(context, BODY)
        if not body:
            self.report({'ERROR'}, "Make a sculpt mesh first")
            return {'CANCELLED'}
        if any(m.type == 'MULTIRES' for m in body.modifiers):
            self.report({'ERROR'}, "Remeshing would discard the Multires detail; apply or remove it first")
            return {'CANCELLED'}
        voxel_remesh(context, body, context.scene.chm_voxel_size)
        return {'FINISHED'}


class CHM_OT_add_multires(bpy.types.Operator):
    """Add a Multires modifier for fine detail once the big forms are done"""
    bl_idname = "chm.add_multires"
    bl_label = "Add Detail Levels"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body = find_by_role(context, BODY)
        if not body:
            self.report({'ERROR'}, "Make a sculpt mesh first")
            return {'CANCELLED'}
        multires = next((m for m in body.modifiers if m.type == 'MULTIRES'), None)
        if not multires:
            multires = body.modifiers.new("Multires", 'MULTIRES')
            body.modifiers.move(body.modifiers.find(multires.name), 0)
        with context.temp_override(active_object=body, object=body, selected_objects=[body]):
            for _ in range(context.scene.chm_multires_levels):
                bpy.ops.object.multires_subdivide(modifier=multires.name, mode='CATMULL_CLARK')
        self.report({'INFO'}, f"Multires now has {multires.total_levels} levels")
        return {'FINISHED'}


classes = (CHM_OT_make_sculpt_mesh, CHM_OT_remesh, CHM_OT_add_multires)
