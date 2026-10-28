"""Step 3: build an armature from the skeleton's points and bind the body."""

import bpy
from mathutils import Vector

from .common import SKELETON, BODY, RIG, find_by_role, ensure_object_mode, make_active

RIG_NAME = "CHM_Rig"

# Deform bones: (name, head point, tail point, parent). Anything ending in .L
# is also built mirrored as .R. A bone is connected to its parent when its
# head sits on the parent's tail.
BONES = [
    ("spine_01", "hips", "spine_1", "root"),
    ("spine_02", "spine_1", "spine_2", "spine_01"),
    ("spine_03", "spine_2", "chest", "spine_02"),
    ("neck", "chest", "neck", "spine_03"),
    ("head", "neck", "snout", "neck"),
    ("tail_01", "hips", "tail_1", "spine_01"),
    ("tail_02", "tail_1", "tail_2", "tail_01"),
    ("tail_03", "tail_2", "tail_3", "tail_02"),
    ("tail_04", "tail_3", "tail_4", "tail_03"),
    ("tail_05", "tail_4", "tail_5", "tail_04"),
    ("upper_arm.L", "shoulder.L", "elbow.L", "spine_03"),
    ("forearm.L", "elbow.L", "wrist.L", "upper_arm.L"),
    ("hand.L", "wrist.L", "fingers.L", "forearm.L"),
    ("thigh.L", "hip.L", "knee.L", "spine_01"),
    ("shin.L", "knee.L", "ankle.L", "thigh.L"),
    ("foot.L", "ankle.L", "toes.L", "shin.L"),
]

# IK legs: (upper bone, lower bone, end bone). The end bone follows an IK
# control and the knee or elbow aims at a pole control.
LIMBS = [("upper_arm", "forearm", "hand"), ("thigh", "shin", "foot")]

TAIL_BONES = [b[0] for b in BONES if b[0].startswith("tail_")]


def mirrored(name):
    return name[:-2] + ".R" if name.endswith(".L") else name


def read_points(skeleton):
    """World positions of every named point, with .R points mirrored from .L."""
    groups = {g.index: g.name for g in skeleton.vertex_groups}
    local = {}
    for v in skeleton.data.vertices:
        for g in v.groups:
            if g.weight > 0 and g.group in groups:
                local[groups[g.group]] = v.co.copy()
    for name, co in list(local.items()):
        if name.endswith(".L"):
            local[mirrored(name)] = Vector((-co.x, co.y, co.z))
    return {name: skeleton.matrix_world @ co for name, co in local.items()}


def signed_angle(u, v, normal):
    angle = u.angle(v)
    if u.cross(v).angle(normal) < 1:
        angle = -angle
    return angle


def pole_angle(base, lower, pole_location):
    """IK pole angle that keeps the chain in its rest pose."""
    pole_normal = (lower.tail - base.head).cross(pole_location - base.head)
    projected = pole_normal.cross(base.tail - base.head)
    return signed_angle(base.x_axis, projected, base.tail - base.head)


def build_rig(context, skeleton):
    points = read_points(skeleton)
    needed = {p for _, head, tail, _ in BONES for p in (head, tail, mirrored(head), mirrored(tail))}
    missing = needed - points.keys()
    if missing:
        raise ValueError("Skeleton is missing points: " + ", ".join(sorted(missing)))

    arm = bpy.data.armatures.new(RIG_NAME)
    rig = bpy.data.objects.new(RIG_NAME, arm)
    rig["chm_role"] = RIG
    rig.show_in_front = True
    context.collection.objects.link(rig)
    deform_coll = arm.collections.new("Deform")
    control_coll = arm.collections.new("Controls")

    make_active(context, rig)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones

    body_length = (points["snout"] - points["tail_5"]).length
    root = eb.new("root")
    root.head = (points["hips"] + points["chest"]) / 2
    root.head.z = 0
    root.tail = root.head + Vector((0, body_length * 0.25, 0))
    root.use_deform = False
    control_coll.assign(root)

    for name, head, tail, parent in BONES:
        for mirror in (False, True) if name.endswith(".L") else (False,):
            side = mirrored if mirror else (lambda n: n)
            bone = eb.new(side(name))
            bone.head = points[side(head)]
            bone.tail = points[side(tail)]
            bone.parent = eb[side(parent)]
            bone.use_connect = (bone.head - bone.parent.tail).length < 1e-5
            deform_coll.assign(bone)

    poles = {}
    for upper, lower, end in LIMBS:
        for s in (".L", ".R"):
            u, l, e = eb[upper + s], eb[lower + s], eb[end + s]
            ik = eb.new(f"{end}_ik{s}")
            ik.head, ik.tail, ik.roll = e.head, e.tail, e.roll
            ik.parent = root
            ik.use_deform = False
            control_coll.assign(ik)

            # Put the pole out from the bend, so the joint keeps bending the
            # way it was built.
            chain = l.tail - u.head
            bend = (l.head - u.head) - (l.head - u.head).project(chain)
            if bend.length < 1e-4:
                bend = Vector((0, -1, 0))
            reach = u.length + l.length
            pole = eb.new(f"{lower}_pole{s}")
            pole.head = l.head + bend.normalized() * reach
            pole.tail = pole.head + Vector((0, 0, reach * 0.2))
            pole.parent = root
            pole.use_deform = False
            control_coll.assign(pole)
            poles[lower + s] = (ik.name, pole.name, pole_angle(u, l, pole.head))

    # Rotating this one control curls the whole tail; each tail bone adds it
    # on top of its own rotation, so the tail can still be posed by hand.
    curl = eb.new("tail_curl")
    curl.head = points["tail_1"] + Vector((0, 0, body_length * 0.15))
    curl.tail = curl.head + Vector((0, body_length * 0.1, 0))
    curl.parent = eb["spine_01"]
    curl.use_deform = False
    control_coll.assign(curl)

    bpy.ops.object.mode_set(mode='POSE')
    pb = rig.pose.bones
    for lower, (ik_name, pole_name, angle) in poles.items():
        ik = pb[lower].constraints.new('IK')
        ik.target, ik.subtarget = rig, ik_name
        ik.pole_target, ik.pole_subtarget = rig, pole_name
        ik.pole_angle = angle
        ik.chain_count = 2
        end = pb[ik_name.replace("_ik", "")]
        follow = end.constraints.new('COPY_ROTATION')
        follow.target, follow.subtarget = rig, ik_name
    for name in TAIL_BONES:
        add = pb[name].constraints.new('COPY_ROTATION')
        add.target, add.subtarget = rig, "tail_curl"
        add.mix_mode = 'ADD'
        add.target_space = add.owner_space = 'LOCAL'
    for bone in pb:
        if not bone.bone.use_deform:
            bone.color.palette = 'THEME09'
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


class CHM_OT_build_rig(bpy.types.Operator):
    """Build a creature armature from the skeleton's joint points"""
    bl_idname = "chm.build_rig"
    bl_label = "Build Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        skeleton = find_by_role(context, SKELETON)
        if not skeleton:
            self.report({'ERROR'}, "Add a creature skeleton first")
            return {'CANCELLED'}
        if find_by_role(context, RIG):
            self.report({'ERROR'}, "This scene already has a rig; delete it to rebuild")
            return {'CANCELLED'}
        ensure_object_mode(context)
        try:
            build_rig(context, skeleton)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}


class CHM_OT_bind_mesh(bpy.types.Operator):
    """Skin the sculpt body to the rig with automatic weights"""
    bl_idname = "chm.bind_mesh"
    bl_label = "Bind Body to Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body, rig = find_by_role(context, BODY), find_by_role(context, RIG)
        if not (body and rig):
            self.report({'ERROR'}, "Needs both a sculpt body and a rig")
            return {'CANCELLED'}
        ensure_object_mode(context)
        rig.data.pose_position = 'REST'
        make_active(context, rig)
        body.select_set(True)
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        rig.data.pose_position = 'POSE'

        deform = {b.name for b in rig.data.bones if b.use_deform}
        groups = {g.index for g in body.vertex_groups if g.name in deform}
        unweighted = sum(
            1 for v in body.data.vertices
            if not any(g.group in groups and g.weight > 0 for g in v.groups)
        )
        if unweighted:
            self.report({'WARNING'}, f"{unweighted} vertices got no weights; paint them in Weight Paint mode")
        else:
            self.report({'INFO'}, "Body bound to rig")
        return {'FINISHED'}


classes = (CHM_OT_build_rig, CHM_OT_bind_mesh)
