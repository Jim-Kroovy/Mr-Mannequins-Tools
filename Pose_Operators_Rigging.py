import bpy
import math
from bpy.props import (StringProperty, FloatProperty, BoolProperty, EnumProperty, PointerProperty)

from . import (Base_Functions, Pose_Functions_Rigging, Pose_Properties_Rigging)

class JK_OT_Add_Head_Controls(bpy.types.Operator):
    """Adds head tracking controls"""
    bl_idname = "jk.add_head_controls"
    bl_label = "Add Head Tracking"

    Props: PointerProperty(type=Pose_Properties_Rigging.JK_MMT_Head_Tracking_Props)
    
    def execute(self, context):
        self.Props.Stretch = "HT_STRETCH" + self.Props.name[2:]
        self.Props.Target = "HT" + self.Props.name[2:]
        axes = (True, False, False) if "X" in self.Props.Axis else (False, True, False) if "Y" in self.Props.Axis else (False, False, True)
        distance = (0 - self.Props.Distance) if "NEGATIVE" in self.Props.Axis else self.Props.Distance
        vector = (distance, 0, 0 ) if "X" in self.Props.Axis else (0, distance, 0) if "Y" in self.Props.Axis else (0, 0, distance)
        rig = bpy.context.object
        # deselect any selected pose bones...
        bpy.ops.pose.select_all(action='DESELECT')
        # loop through all the bones to track and select them...
        for bone in [self.Props.name, self.Props.Neck, self.Props.Spine]:
            p_bone = rig.pose.bones[bone]
            p_bone.bone.select = True
        # go to edit mode and duplicate them...
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.duplicate(do_flip_names=False)
        # rename the duplicates...
        for e_bone in bpy.context.selected_bones:
            e_bone.name = "GB" + e_bone.name[2:-4]
            e_bone.layers, e_bone.use_deform = [False]*23+[True]+[False]*8, False
        # get a reference to the head bone...
        h_bone = rig.data.edit_bones["GB" + self.Props.name[2:]]
        h_bone.use_inherit_scale = False
        # add and create the target bone...
        t_bone = rig.data.edit_bones.new(self.Props.Target)
        t_bone.head, t_bone.tail, t_bone.roll = h_bone.head, h_bone.tail, h_bone.roll
        bpy.ops.armature.select_all(action='DESELECT')
        t_bone.select_tail, t_bone.select_head = True, True
        bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=(axes[0], axes[1], axes[2]))
        if h_bone.parent.parent.parent != None:
            t_bone.parent = h_bone.parent.parent.parent #if h_bone.parent.parent.parent != None else None
        else:
            t_bone.parent = None
        t_bone.roll, t_bone.layers, t_bone.use_deform = 0, [False]*1+[True]+[False]*30, False
        # add and set the stretch bone...
        s_bone = rig.data.edit_bones.new(self.Props.Stretch)
        s_bone.head, s_bone.tail, s_bone.roll = h_bone.head, t_bone.head, 0
        s_bone.parent = rig.data.edit_bones["GB" + self.Props.Neck[2:]]
        s_bone.layers, s_bone.use_deform = [False]*1+[True]+[False]*30, False
        # re-parent the head gizmo bone...
        h_bone.parent = s_bone
        # back to pose mode to set up constraints and stuff...
        bpy.ops.object.mode_set(mode='POSE')
        # target just needs group and shape...
        p_bone = rig.pose.bones[self.Props.Target]
        p_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
        p_bone.custom_shape_scale = 0.5
        p_bone.bone_group = rig.pose.bone_groups["IK Targets"]
        # stretch bone hase IK contraint...
        p_bone = rig.pose.bones[self.Props.Stretch]
        p_bone.custom_shape, p_bone.custom_shape_scale = bpy.data.objects["B_Shape_Circle_Limbs"], 1
        p_bone.bone_group, p_bone.ik_stretch = rig.pose.bone_groups["IK Targets"], 1
        ik = p_bone.constraints.new('IK')
        ik.name, ik.show_expanded = "Head Tracking - IK", False
        ik.target, ik.subtarget, ik.chain_count = rig, "HT" + self.Props.name[2:], 3
        # set up the control bones...
        for bone in [self.Props.name, self.Props.Neck, self.Props.Spine]:
            # set the gizmo bone...
            p_bone = rig.pose.bones["GB" + bone[2:]]
            p_bone.custom_shape, p_bone.bone_group = None, rig.pose.bone_groups["Gizmo Bones"]
            p_bone.ik_stretch, p_bone.ik_stiffness_x, p_bone.ik_stiffness_y, p_bone.ik_stiffness_z = 0.5, 0, 0, 0
            # set the control bone...
            p_bone = rig.pose.bones[bone]
            ik = p_bone.constraints.new('IK')
            ik.name, ik.show_expanded, ik.target, ik.chain_count = "Head Tracking - IK", False, rig, 1
            # set the right target bone...
            ik.subtarget = "GB" + self.Props.Neck[2:] if bone == self.Props.Spine else "GB" + self.Props.name[2:]
            # head just uses rotation based IK... (could be a damped track with a limit rotation but i prefer IK)
            if bone == self.Props.name:
                ik.use_location, ik.use_rotation = False, True     
            # neck and spine also have copy Y rotation constraints...
            else:
                copy_rot = p_bone.constraints.new('COPY_ROTATION')
                copy_rot.name, copy_rot.show_expanded = "Head Tracking - Copy Rotation", False
                copy_rot.target, copy_rot.subtarget = rig, "GB" + bone[2:]
                copy_rot.use_x, copy_rot.use_z = False, False
                copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'  
            # turn on the IK limits for all three...    
            p_bone.use_ik_limit_x, p_bone.use_ik_limit_y, p_bone.use_ik_limit_z = True, True, True
        # set the data entry...
        if self.Props.name in rig.JK_MMT.Head_tracking_data:
            data = rig.JK_MMT.Head_tracking_data[self.Props.name]
        else:
            data = rig.JK_MMT.Head_tracking_data.add()
            data.name = self.Props.name
        data.Target, data.Stretch, data.Neck, data.Spine = self.Props.Target, self.Props.Stretch, self.Props.Neck, self.Props.Spine
        data.Forward_axis, data.Target_distance = self.Props.Axis, self.Props.Distance
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        if bpy.context.active_pose_bone != None:
            active_bone = bpy.context.active_pose_bone
            self.Props.name = active_bone.name
            self.Props.Neck = active_bone.parent.name
            self.Props.Spine = active_bone.parent.parent.name    
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        layout.ui_units_x = 20
        row = layout.row()
        label_col = row.column()
        label_col.ui_units_x = 7
        label_col.label(text="Head Bone:")
        label_col.label(text="Neck Bone:")
        label_col.label(text="Spine Bone:")
        label_col.label(text="Target Orientation:")
        prop_col = row.column()
        prop_col.prop_search(self.Props, "name", armature.pose, "bones", text="")
        prop_col.prop_search(self.Props, "Neck", armature.pose, "bones", text="")
        prop_col.prop_search(self.Props, "Spine", armature.pose, "bones", text="")
        row = prop_col.row()
        row.prop(self.Props, "Axis", text="")
        row.prop(self.Props, "Distance", text="Distance")

class JK_OT_Remove_Head_Controls(bpy.types.Operator):
    """Removes head tracking controls"""
    bl_idname = "jk.remove_head_controls"
    bl_label = "Remove Head Tracking"

    Name: StringProperty(
        name="Name",
        description="The name of the head tracking to be removed",
        default="",
        maxlen=1024,
        )
    
    def execute(self, context):
        armature = bpy.context.object
        data = armature.JK_MMT.Head_tracking_data
        props = data[self.Name]
        for bone in [props.name, props.Neck, props.Spine]:
            p_bone = armature.pose.bones[bone]
            p_bone.constraints["Head Tracking - IK"].driver_remove('mute')
            p_bone.constraints.remove(p_bone.constraints["Head Tracking - IK"])
            if bone != props.name:
                p_bone.constraints["Head Tracking - Copy Rotation"].driver_remove('mute')
                p_bone.constraints.remove(p_bone.constraints["Head Tracking - Copy Rotation"])
            p_bone.use_ik_limit_x = False
            p_bone.use_ik_limit_y = False
            p_bone.use_ik_limit_z = False
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in [props.Target, props.Stretch, "GB" + props.name[2:], "GB" + props.Neck[2:], "GB" + props.Spine[2:]]:
            armature.data.edit_bones.remove(armature.data.edit_bones[bone])   
        bpy.ops.object.mode_set(mode='POSE')
        data.remove(data.find(self.Name)) 
        return {'FINISHED'}

class JK_OT_Add_Twist_Controls(bpy.types.Operator):
    """Adds twist controls"""
    bl_idname = "jk.add_twist_controls"
    bl_label = "Add Twist Controls"
    
    Props: PointerProperty(type=Pose_Properties_Rigging.JK_MMT_Twist_Bone_Props)

    def execute(self, context):
        rig = bpy.context.object 
        p_bone = rig.pose.bones[self.Props.name]
        if p_bone.parent != None:
            self.Props.Parent = p_bone.parent.name
        # if we want the twist bone to hold back deformation at the head of the bone...
        if self.Props.Type == 'HEAD_HOLD':
            damped_track = p_bone.constraints.new('DAMPED_TRACK')
            damped_track.name, damped_track.show_expanded = "Twist - Damped Track", False
            damped_track.target, damped_track.subtarget, damped_track.head_tail = rig, self.Props.Target, self.Props.Float
            limit_rot = p_bone.constraints.new('LIMIT_ROTATION')
            limit_rot.name, limit_rot.show_expanded = "Twist - Limit Rotation", False
            limit_rot.use_limit_x, limit_rot.min_x, limit_rot.max_x = self.Props.Limits_use[0], self.Props.Limits_min[0], self.Props.Limits_max[0] 
            limit_rot.use_limit_z, limit_rot.min_z, limit_rot.max_z = self.Props.Limits_use[2], self.Props.Limits_min[2], self.Props.Limits_max[2]
            limit_rot.use_transform_limit, limit_rot.owner_space = True, 'LOCAL'
            if self.Props.Has_pivot:
                pivot_bone = Pose_Functions_Rigging.Add_Pivot_Bone(rig, self.Props.name, 'PARENT_SKIP', True)
                pivot_bone.custom_shape = bpy.data.objects["B_Shape_Bracket"]
                pivot_bone.custom_shape_scale = 0.5
            else:
                bpy.ops.object.mode_set(mode='EDIT')
                e_bone = rig.data.edit_bones[self.Props.name]
                e_bone.parent = e_bone.parent.parent
                bpy.ops.object.mode_set(mode='POSE')  
        # if we want the twist bone to follow deformation at the tail of the bone...
        elif self.Props.Type == 'TAIL_FOLLOW':
            ik = p_bone.constraints.new('IK')
            ik.name, ik.show_expanded = "Twist - IK", False
            ik.target, ik.subtarget = rig, self.Props.Target
            ik.chain_count, ik.use_location, ik.use_rotation, ik.influence = 1, False, True, self.Props.Float
            p_bone.use_ik_limit_y, p_bone.ik_min_y, p_bone.ik_max_y = self.Props.Limits_use[1], self.Props.Limits_min[1], self.Props.Limits_max[1] 
            if self.Props.Has_pivot:
                pivot_bone = Pose_Functions_Rigging.Add_Pivot_Bone(rig, self.Props.name, 'PARENT_SHARE', True)
                pivot_bone.custom_shape = bpy.data.objects["B_Shape_Bracket"]
                pivot_bone.custom_shape_scale = 0.5    
        if self.Props.name in rig.JK_MMT.Twist_bone_data:
            data = rig.JK_MMT.Twist_bone_data[self.Props.name]
        else:
            data = rig.JK_MMT.Twist_bone_data.add()
            data.name = self.Props.name
        data.Type, data.Target, data.Parent, data.Float = self.Props.Type, self.Props.Target, self.Props.Parent, self.Props.Float
        data.Limits_use, data.Limits_min, data.Limits_max, data.Has_pivot = self.Props.Limits_use, self.Props.Limits_min, self.Props.Limits_max, self.Props.Has_pivot
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        if bpy.context.active_pose_bone != None:
            selected_bones = bpy.context.selected_pose_bones
            active_bone = bpy.context.active_pose_bone
            self.Props.name = active_bone.name
            if len(selected_bones) > 1:
                self.Props.Target = selected_bones[0].name
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        layout.ui_units_x = 20
        row = layout.row()
        label_col = row.column()
        label_col.ui_units_x = 7
        label_col.label(text="Twist Type:")
        label_col.label(text="Twist Bone:")
        label_col.label(text="Target Bone:")
        #label_col.label(text="Head Vs Tail:" if self.Props.Type == 'HEAD_HOLD' else "Influence:")
        label_col.label(text="Use Limits:")
        label_col.label(text="Limits Min:")
        label_col.label(text="Limits Max:")
        prop_col = row.column()
        row = prop_col.row()
        row.prop(self.Props, "Type", text="")
        row.prop(self.Props, "Has_pivot", text="Add Pivot Bone")
        prop_col.prop_search(self.Props, "name", armature.pose, "bones", text="")
        row = prop_col.row()
        row.prop_search(self.Props, "Target", armature.pose, "bones", text="")
        row.prop(self.Props, "Float", text="Head Vs Tail" if self.Props.Type == 'HEAD_HOLD' else "Influence")
        row = prop_col.row()
        row.prop(self.Props, "Limits_use", text="")
        row = prop_col.row()
        row.prop(self.Props, "Limits_min", text="")
        row = prop_col.row()
        row.prop(self.Props, "Limits_max", text="")

class JK_OT_Remove_Twist_Controls(bpy.types.Operator):
    """Removes twist bone controls"""
    bl_idname = "jk.remove_twist_controls"
    bl_label = "Remove Twist Controls"

    Name: StringProperty(name="Name", description="The name of the twist controls to be removed", default="")
    
    def execute(self, context):
        armature = bpy.context.object
        data = armature.JK_MMT.Twist_bone_data
        props = data[self.Name]
        p_bone = armature.pose.bones[props.name]
        if props.Type == 'HEAD_HOLD':
            p_bone.constraints["Twist - Damped Track"].driver_remove('mute')
            p_bone.constraints.remove(p_bone.constraints["Twist - Damped Track"])
            p_bone.constraints["Twist - Limit Rotation"].driver_remove('mute')
            p_bone.constraints.remove(p_bone.constraints["Twist - Limit Rotation"])
        else:
            p_bone.constraints["Twist - IK"].driver_remove('mute')
            p_bone.constraints.remove(p_bone.constraints["Twist - IK"])
        if p_bone.parent.name != props.Parent:
            bpy.ops.object.mode_set(mode='EDIT')
            e_bone = armature.data.edit_bones[props.name]
            e_bone.parent = armature.data.edit_bones[props.Parent]
            if props.Has_pivot:
                armature.data.edit_bones.remove(armature.data.edit_bones["PB" + props.name[2:]])
            bpy.ops.object.mode_set(mode='POSE')
        data.remove(data.find(self.Name)) 
        return {'FINISHED'} 
            
class JK_OT_Add_Digit_Controls(bpy.types.Operator):
    """Adds digit controls"""
    bl_idname = "jk.add_digit_controls"
    bl_label = "Add Digit Controls"
    
    Props: PointerProperty(type=Pose_Properties_Rigging.JK_MMT_Digit_Bone_Props)

    def execute(self, context):
        self.Props.name = "CB_DIGIT" + self.Props.Proximal[2:]
        rig = bpy.context.object
        axes = [True, False] if 'X' in self.Props.Main_axis else [False, True]
        # create any bones in edit mode...       
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.reveal(select=False)
        # create bone to control all digits...
        e_bone = rig.data.edit_bones[self.Props.Distal]
        c_digit = rig.data.edit_bones.new(self.Props.name)
        c_digit.head, c_digit.tail, c_digit.roll = e_bone.parent.parent.head, e_bone.parent.parent.tail, e_bone.parent.parent.roll
        c_digit.parent = e_bone.parent.parent.parent
        bpy.ops.armature.select_all(action='DESELECT')
        c_digit.select_tail = True
        bpy.ops.transform.translate(value=(0, Base_Functions.Get_Distance(e_bone.parent.parent.tail, e_bone.tail), 0), orient_type='NORMAL', constraint_axis=(False, True, False))
        c_digit.layers, c_digit.use_deform = [False]*1+[True]+[False]*30, False
        # set all the constraints in pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        c_bone = rig.pose.bones[self.Props.name]
        for name in [self.Props.Proximal, self.Props.Medial, self.Props.Distal]:
            p_bone = rig.pose.bones[name]
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.name = "Digit - Copy Rotation"
            copy_rot.target, copy_rot.subtarget, copy_rot.show_expanded = rig, c_bone.name, False
            # medial and distal digit bones only copy main axis proximal copies all three...
            if name != self.Props.Proximal:
                copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = axes[0], False, axes[1]
            copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'
        # set the control bones custom shape...
        c_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
        c_bone.custom_shape_scale = 0.25
        c_bone.bone_group = rig.pose.bone_groups["Control Bones"]
        if self.Props.name in rig.JK_MMT.Digit_bone_data:
            data = rig.JK_MMT.Digit_bone_data[self.Props.name]
        else:
            data = rig.JK_MMT.Digit_bone_data.add()
            data.name = self.Props.name
        data.Main_axis = self.Props.Main_axis
        data.Proximal = self.Props.Proximal
        data.Medial = self.Props.Medial
        data.Distal = self.Props.Distal
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        if bpy.context.active_pose_bone != None:
            active_bone = bpy.context.active_pose_bone
            self.Props.Distal = active_bone.name
            self.Props.Medial = active_bone.parent.name
            self.Props.Proximal = active_bone.parent.parent.name
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        layout.ui_units_x = 15
        row = layout.row()
        label_col = row.column()
        label_col.ui_units_x = 7
        label_col.label(text="Main Rotation:")
        label_col.label(text="Proximal Bone:")
        label_col.label(text="Medial Bone:")
        label_col.label(text="Distal Bone:")
        prop_col = row.column()
        prop_col.prop(self.Props, "Main_axis", text="")
        prop_col.prop_search(self.Props, "Proximal", armature.pose, "bones", text="")
        prop_col.prop_search(self.Props, "Medial", armature.pose, "bones", text="")
        prop_col.prop_search(self.Props, "Distal", armature.pose, "bones", text="")

class JK_OT_Remove_Digit_Controls(bpy.types.Operator):
    """Removes twist bone controls"""
    bl_idname = "jk.remove_digit_controls"
    bl_label = "Remove Digit Controls"

    Name: StringProperty(name="Name", description="The name of the digit controls to be removed", default="")
    
    def execute(self, context):
        armature = bpy.context.object
        data = armature.JK_MMT.Digit_bone_data
        props = data[self.Name]
        if props.IKvsFK == 'OFFSET':
            props.IKvsFK = 'NONE'
        for name in [props.Proximal, props.Medial, props.Distal]:
            p_bone = armature.pose.bones[name]
            p_bone.constraints["Digit - Copy Rotation"].driver_remove('mute')
            p_bone.constraints.remove(p_bone.constraints["Digit - Copy Rotation"])
        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones.remove(armature.data.edit_bones[props.name])
        bpy.ops.object.mode_set(mode='POSE')
        data.remove(data.find(self.Name))
        return {'FINISHED'}

class JK_OT_Add_Ankle_Controls(bpy.types.Operator):
    """Adds ankle controls"""
    bl_idname = "jk.add_ankle_controls"
    bl_label = "Add Ankle Controls"
    
    Name: StringProperty(name="Name", description="The name of the IK chain to add end controls too", default="")
    
    Pivot: StringProperty(name="Name", description="The name of the IK chain to add end controls too", default="")

    def execute(self, context):
        rig = bpy.context.object
        ik_data = rig.JK_MMT.IK_chain_data[self.Name]
        chain_data = ik_data.Chain_data
        end_data = ik_data.End_data
        end_data.Pivot = self.Pivot
        end_data.Control = "CB_ROLL" + end_data.name[2:]
        end_axes = [True, False] if 'X' in end_data.Main_axis else [False, True]
        pivot_axes = [True, False] if 'X' in end_data.Pivot_axis else [False, True]
        rotation = 1.5708 if 'NEGATIVE' in end_data.Main_axis else -1.5708
        # create all the bones in edit mode...      
        bpy.ops.object.mode_set(mode='EDIT')
        # get all the edit bones needed to set things up...
        CB_foot = rig.data.edit_bones[end_data.name]
        CB_ball = rig.data.edit_bones[end_data.Pivot]
        LT_foot = rig.data.edit_bones["LT" + end_data.name[2:]]
        FT_foot = rig.data.edit_bones["FT" + end_data.name[2:]]
        GB_foot = rig.data.edit_bones["GB" + end_data.name[2:]]
        # ball control must point forwards for this to work...
        bpy.ops.armature.select_all(action='DESELECT')
        CB_ball.select_tail = True
        if abs(CB_ball.head.z - CB_ball.tail.z) > 0.001:
            rot_axis = Base_Functions.Get_Rot_Direction_Shortest(CB_ball, end_data.Pivot_axis[0], 2, CB_ball.head.z) 
            Base_Functions.Set_Bone_Rotation_By_Step(CB_ball, rot_axis, 2, CB_ball.head.z)
        # if the tail is behind the head...
        if CB_ball.tail.y > CB_ball.head.y:
            old_roll = CB_ball.roll
            # just reverse the bone... 
            bpy.ops.transform.translate(value=(0.0, (CB_ball.length * 2) * -1, 0.0), orient_type='NORMAL', constraint_axis=(False, True, False))
            # set it's roll inverse of what it was to begin with..
            CB_ball.roll = old_roll * -1
        # foot roll control == foot control bone rotated back by 90 degrees on main axis and parented to the leg target...
        bpy.ops.armature.select_all(action='DESELECT')
        CB_foot_roll = rig.data.edit_bones.new(end_data.Control)
        CB_foot_roll.head, CB_foot_roll.tail, CB_foot_roll.roll = CB_foot.head, CB_foot.tail, CB_foot.roll
        CB_foot_roll.parent = LT_foot
        CB_foot_roll.select_tail = True
        bpy.ops.transform.rotate(value=rotation, orient_axis=end_data.Main_axis[0], orient_type='NORMAL')
        CB_foot_roll.layers, CB_foot_roll.use_deform = [False]*1+[True]+[False]*30, False
        # ball roll gizmo == ball control bone rotated back by 180 degrees on main axis and parented to the leg target...
        bpy.ops.armature.select_all(action='DESELECT')
        GB_ball_roll = rig.data.edit_bones.new("GB_ROLL" + end_data.Pivot[2:])
        GB_ball_roll.head, GB_ball_roll.tail, GB_ball_roll.roll = CB_ball.head, CB_ball.tail, CB_ball.roll
        GB_ball_roll.parent = LT_foot
        GB_ball_roll.select_tail = True
        # rotate by 90 degrees twice... (rotating by 180 messes up roll calculation for some reason)
        bpy.ops.transform.rotate(value=rotation, orient_axis=end_data.Main_axis[0], orient_type='NORMAL')
        bpy.ops.transform.rotate(value=rotation, orient_axis=end_data.Main_axis[0], orient_type='NORMAL')
        GB_ball_roll.layers, GB_ball_roll.use_deform = [False]*23+[True]+[False]*8, False
        # foot roll gizmo == foot control bone dropped to its tail and rotated forward by 90 degrees on Z axis and parented to the ball roll...
        bpy.ops.armature.select_all(action='DESELECT')
        GB_foot_roll = rig.data.edit_bones.new("GB" + end_data.Control[2:])
        GB_foot_roll.head, GB_foot_roll.tail, GB_foot_roll.roll = CB_foot.head, CB_foot.tail, CB_foot.roll
        GB_foot_roll.parent = GB_ball_roll
        GB_foot_roll.select_head = True
        GB_foot_roll.select_tail = True
        bpy.ops.transform.translate(value=(0, Base_Functions.Get_Distance(CB_foot.head, CB_foot.tail), 0), orient_type='NORMAL', constraint_axis=(False, True, False))
        GB_foot_roll.select_head = False
        bpy.ops.transform.rotate(value=rotation * -1, orient_axis=end_data.Main_axis[0], orient_type='NORMAL')
        GB_foot_roll.layers, GB_foot_roll.use_deform = [False]*23+[True]+[False]*8, False
        # parent the IK target to the foot roll...
        GB_foot.parent = GB_foot_roll    
        # set all the bones in pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # ball control copies ball gizmo...
        ball_bone = rig.pose.bones[end_data.Pivot]
        copy_rot = ball_bone.constraints.new('COPY_ROTATION')
        copy_rot.target, copy_rot.subtarget, copy_rot.show_expanded = rig, "GB_ROLL" + end_data.Pivot[2:], False
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = pivot_axes[0], False, pivot_axes[1]
        copy_rot.invert_x, copy_rot.invert_z, copy_rot.mix_mode = True, True, 'BEFORE'      
        # roll control has its rotation limited...
        roll_control = rig.pose.bones[end_data.Control]
        limit_rot = roll_control.constraints.new('LIMIT_ROTATION')
        limit_rot.show_expanded = False
        limit_rot.use_limit_x, limit_rot.use_limit_y, limit_rot.use_limit_z = end_axes[0], True, end_axes[1]
        limit_rot.min_x = -0.523599 if ik_data.Chain_side == 'LEFT' else -0.785398
        limit_rot.max_x = 0.785398 if ik_data.Chain_side == 'LEFT' else 0.523599
        limit_rot.min_z = -0.523599 if ik_data.Chain_side == 'LEFT' else -0.785398
        limit_rot.max_z = 0.785398 if ik_data.Chain_side == 'LEFT' else 0.523599    
        limit_rot.owner_space, limit_rot.use_transform_limit = 'LOCAL', True
        roll_control.custom_shape = bpy.data.objects["B_Shape_Bracket"]
        roll_control.bone_group = rig.pose.bone_groups["Control Bones"]
        # foot gizmo copies roll control rotation... (local axis)
        foot_roll = rig.pose.bones["GB" + end_data.Control[2:]]
        copy_rot = foot_roll.constraints.new('COPY_ROTATION')
        copy_rot.target, copy_rot.subtarget, copy_rot.show_expanded = rig, end_data.Control, False
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = end_axes[0], False, end_axes[1]
        # and has rotation limited...
        limit_rot = foot_roll.constraints.new('LIMIT_ROTATION')
        limit_rot.show_expanded = False
        limit_rot.use_limit_x, limit_rot.use_limit_z = end_axes[0], end_axes[1]
        # just do both X and Z as only one gets enabled...
        limit_rot.min_x = 0.0 if 'NEGATIVE' in end_data.Main_axis else -0.785398
        limit_rot.max_x = 0.785398 if 'NEGATIVE' in end_data.Main_axis else 0.0
        limit_rot.min_z = 0.0 if 'NEGATIVE' in end_data.Main_axis else -0.785398
        limit_rot.max_z = 0.785398 if 'NEGATIVE' in end_data.Main_axis else 0.0
        limit_rot.owner_space, limit_rot.use_transform_limit = 'LOCAL', True
        # foot roll has a driver to stop drifting...
        driver = foot_roll.driver_add("location", 0)       
        var = driver.driver.variables.new()
        var.name = end_data.Main_axis[0] + "_Roll"
        var.type = 'TRANSFORMS'
        var.targets[0].id = rig
        var.targets[0].bone_target = end_data.Control
        var.targets[0].transform_type = 'ROT_' + end_data.Main_axis[0]
        var.targets[0].transform_space = 'LOCAL_SPACE'
        driver.driver.expression = end_data.Main_axis[0] + "_Roll * 0.05 * -1 if " + end_data.Main_axis[0] + "_Roll " + (">" if 'NEGATIVE' in end_data.Main_axis else "<") + " 0 else 0"
        if len(driver.modifiers) > 0:
            driver.modifiers.remove(driver.modifiers[0])
        foot_roll.bone_group = rig.pose.bone_groups["Gizmo Bones"]
        # ball gizmo copies roll control rotation... (local axis)
        ball_roll = rig.pose.bones["GB_ROLL" + end_data.Pivot[2:]] 
        copy_rot = ball_roll.constraints.new('COPY_ROTATION')
        copy_rot.target, copy_rot.subtarget, copy_rot.show_expanded = rig, end_data.Control, False
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
        copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = True, False, True
        # invert z and X if there is a greater than 90 degree difference between the roll control and ball roll...
        copy_rot.invert_x = True if ball_roll.x_axis.angle(roll_control.x_axis) > 1.5708 else False
        copy_rot.invert_z = True if ball_roll.z_axis.angle(roll_control.z_axis) > 1.5708 else False
        # and has rotation limited...
        limit_rot = ball_roll.constraints.new('LIMIT_ROTATION')
        limit_rot.show_expanded, limit_rot.use_limit_x, limit_rot.use_limit_z = False, pivot_axes[0], pivot_axes[1]
        # just do both X and Z as only one gets enabled...
        limit_rot.min_x = -0.785398 if 'NEGATIVE' in end_data.Pivot_axis else 0.0
        limit_rot.max_x = 0.0 if 'NEGATIVE' in end_data.Pivot_axis else 0.785398
        limit_rot.min_z = -0.785398 if 'NEGATIVE' in end_data.Pivot_axis else 0.0
        limit_rot.max_z = 0.0 if 'NEGATIVE' in end_data.Pivot_axis else 0.785398    
        limit_rot.owner_space, limit_rot.use_transform_limit = 'LOCAL', True
        ball_roll.bone_group = rig.pose.bone_groups["Gizmo Bones"]
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        if bpy.context.active_pose_bone != None:
            active_bone = bpy.context.active_pose_bone
            if len(active_bone.children) > 0:
                self.Pivot = active_bone.children[0].name
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        End_data = armature.JK_MMT.IK_chain_data[self.Name].End_data
        layout = self.layout
        layout.ui_units_x = 20
        row = layout.row()
        label_col = row.column()
        label_col.ui_units_x = 5
        label_col.label(text="End Rotation:")
        label_col.label(text="Ball Bone:")
        prop_col = row.column()
        row = prop_col.row()
        col = row.column()
        col.ui_units_x = 11
        col.label(text="(End bone rotation might of changed!)")
        col = row.column()
        col.ui_units_x = 5
        col.prop(End_data, "Main_axis", text="")
        row = prop_col.row()
        row.prop_search(self, "Pivot", armature.pose, "bones", text="")
        col = row.column()
        col.ui_units_x = 5
        col.prop(End_data, "Pivot_axis", text="")

class JK_OT_Remove_Ankle_Controls(bpy.types.Operator):
    """Remove ankle controls"""
    bl_idname = "jk.remove_ankle_controls"
    bl_label = "Remove Ankle Controls"
    
    Name: StringProperty(name="Name", description="The name of the end controls to be removed", default="")

    def execute(self, context):
        rig = bpy.context.object
        ik_data = rig.JK_MMT.IK_chain_data[self.Name]
        chain_data = ik_data.Chain_data
        end_data = ik_data.End_data
        foot_roll = rig.pose.bones["GB" + end_data.Control[2:]]
        foot_roll.driver_remove("location")
        pivot = rig.pose.bones[end_data.Pivot]
        pivot.constraints.remove(pivot.constraints["Copy Rotation"])
        # remove all the bones in edit mode...      
        bpy.ops.object.mode_set(mode='EDIT')
        for name in ["GB" + end_data.Control[2:], "GB_ROLL" + end_data.Pivot[2:], end_data.Control]:
            rig.data.edit_bones.remove(rig.data.edit_bones[name])
        bpy.ops.object.mode_set(mode='POSE')
        end_data.Pivot = ""
        return {'FINISHED'}
        
class JK_OT_Add_IK_Chain(bpy.types.Operator):
    """Adds an IK chain"""
    bl_idname = "jk.add_ik_chain"
    bl_label = "Add IK Chain"
    
    Props: PointerProperty(type=Pose_Properties_Rigging.JK_MMT_IK_Props)
    
    def execute(self, context):
        rig = bpy.context.object
        # lets set up some variables to avoid getting too confused...
        Props = self.Props
        Chain = Props.Chain_data
        End = Props.End_data
        # set up target and pole target names...
        Chain.Target = ("AT" if Props.Chain_type == 'ARM' else "GB") + End.name[2:]
        Chain.Control = ("AT" if Props.Chain_type == 'ARM' else "LT") + End.name[2:]
        Chain.Pole = ("AT" if Props.Chain_type == 'ARM' else "LT") + Chain.name[2:]
        # and some transform variables for the pole target...
        axes = [True, False] if 'X' in Chain.Pole_axis else [False, True]
        distance = (0 - Chain.Pole_distance) if "NEGATIVE" in Chain.Pole_axis else Chain.Pole_distance
        vector = (distance, 0, 0) if 'X' in Chain.Pole_axis else (0, 0, distance)
        # create all the bones in edit mode...       
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.reveal(select=False)
        # get the edit bones needed to set things up...
        CB_target = rig.data.edit_bones[End.name] 
        CB_owner = rig.data.edit_bones[Props.name]
        CB_pole = rig.data.edit_bones[Chain.name]
        if CB_target.parent.parent.parent != None:
            self.Props.Chain_data.Parent = CB_target.parent.parent.parent.name
        # requires pivot point to be individual origins...
        bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        # create the limb target...
        IK_target = rig.data.edit_bones.new(Chain.Target)
        IK_target.head, IK_target.tail, IK_target.roll = CB_target.head, CB_target.tail, CB_target.roll
        IK_target.use_deform = False
        if Props.Chain_type == 'ARM':
            IK_target.layers = [False]*1+[True]+[False]*30
        # if it's for a leg we need change a few things and add a parent to the IK target...
        else:
            # control and target bone need to be pointing down with tails at 0.0 on the Z axis for my foot IK...
            bpy.ops.armature.select_all(action='DESELECT')
            CB_target.select_tail = True
            if abs(CB_target.head.y - CB_target.tail.y) > 0.001:
                rot_axis = Base_Functions.Get_Rot_Direction_Shortest(CB_target, End.Main_axis[0], 1, CB_target.head.y) 
                Base_Functions.Set_Bone_Rotation_By_Step(CB_target, rot_axis, 1, CB_target.head.y)
            if abs(0.0 - CB_target.tail.z) > 0.001:
                loc_axis = Base_Functions.Get_Loc_Direction_Shortest(CB_target, "Y", 2, 0.0) 
                Base_Functions.Set_Bone_Location_By_Step(CB_target, loc_axis, 2, 0.0)
            # set the target to the control...
            IK_target.tail, IK_target.roll = CB_target.tail, CB_target.roll
            # IK target becomes a gizmo bone...
            IK_target.layers = [False]*23+[True]+[False]*8
            # create the parent bone on the floor below the foot with 0 roll...
            IK_control = rig.data.edit_bones.new(Chain.Control)
            IK_control.head = [IK_target.tail.x, IK_target.tail.y, 0]
            IK_control.tail = [IK_target.tail.x, IK_target.tail.y, -0.1]
            IK_control.roll, IK_control.layers, IK_control.use_deform = 0, [False]*1+[True]+[False]*30, False
            # parent the IK target to it...
            IK_target.parent = IK_control
        # pole target = owner parent moved on local axis...
        bpy.ops.armature.select_all(action='DESELECT')
        IK_pole = rig.data.edit_bones.new(Chain.Pole)
        IK_pole.head, IK_pole.tail, IK_pole.roll = CB_pole.head, CB_pole.tail, CB_pole.roll
        IK_pole.select_tail = True
        IK_pole.select_head = True
        bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=(axes[0], False, axes[1]))
        IK_pole.layers, IK_pole.use_deform = [False]*1+[True]+[False]*30, False
        # add floor target...
        FT_target = rig.data.edit_bones.new("FT" + End.name[2:])
        FT_target.head = [IK_target.head.x, IK_target.head.y, 0]
        FT_target.tail = [IK_target.head.x, IK_target.head.y, -0.1]
        FT_target.roll, FT_target.layers, FT_target.use_deform = 0, [False]*1+[True]+[False]*30, False
        # into pose mode if we need to add pivot bones...
        bpy.ops.object.mode_set(mode='POSE')
        # if we want to use my pivot bones...
        if Chain.Has_pivots:
            # target pivot copys IK target rotation
            p_bone = Pose_Functions_Rigging.Add_Pivot_Bone(rig, End.name, 'PARENT_SHARE', True)
            p_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
            p_bone.custom_shape_scale = 0.5
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.target, copy_rot.subtarget, copy_rot.show_expanded = rig, Chain.Target, False
            # owner pivot copys owner rotation...
            p_bone = Pose_Functions_Rigging.Add_Pivot_Bone(rig, Props.name, 'PARENT_SHARE', False)
            p_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
            p_bone.custom_shape_scale = 0.25
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.target, copy_rot.subtarget, copy_rot.show_expanded = rig, Props.name, False
            # if it's an arm...        
            if Props.Chain_type == 'ARM':
                # we use a skip parent pivot bone...
                p_bone = Pose_Functions_Rigging.Add_Pivot_Bone(rig, Chain.name, 'PARENT_SKIP', True)
                if Chain.Parent != "":
                    # the pivot copys tail location of original parent of the owners parent... 
                    copy_loc = p_bone.constraints.new('COPY_LOCATION')
                    copy_loc.target, copy_loc.subtarget, copy_loc.show_expanded = rig, Chain.Parent, False
                    copy_loc.head_tail = 1.0 
            else:
                # if it's a leg no constraints or fruity parenting needed...
                p_bone = Pose_Functions_Rigging.Add_Pivot_Bone(rig, Chain.name, 'PARENT_SHARE', True)
            p_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
            p_bone.custom_shape_scale = 0.25        
        else:
            p_bone = rig.pose.bones[End.name]
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.show_expanded = False
            copy_rot.target = rig
            copy_rot.subtarget = Chain.Target
        # back to edit mode to add stretch bones...
        bpy.ops.object.mode_set(mode='EDIT') 
        CB_first = rig.data.edit_bones[Props.name]
        CB_second = rig.data.edit_bones[Chain.name]
        # iterate over the two bones within the chain... (to save script space)
        for e_bone in [CB_second, CB_first]:
            # add in a duplicate stretch bone...
            stretch = rig.data.edit_bones.new("GB_STRETCH" + e_bone.name[2:])
            stretch.head, stretch.tail, stretch.roll = e_bone.head, e_bone.tail, e_bone.roll
            stretch.layers, stretch.use_deform, stretch.inherit_scale = [False]*23+[True]+[False]*8, False, 'NONE'
            stretch.parent = e_bone.parent if e_bone == CB_second else rig.data.edit_bones["GB_STRETCH" + e_bone.parent.name[2:]]
            # and a duplicate gizmo bone...
            gizmo = rig.data.edit_bones.new("GB" + e_bone.name[2:])
            gizmo.head, gizmo.tail, gizmo.roll = e_bone.head, e_bone.tail, e_bone.roll
            gizmo.layers, gizmo.use_deform, gizmo.inherit_scale = [False]*23+[True]+[False]*8, False, 'NONE'
            gizmo.parent = e_bone.parent if e_bone == CB_second else rig.data.edit_bones["GB" + e_bone.parent.name[2:]]
        # then into pose mode to do the rest...
        bpy.ops.object.mode_set(mode='POSE')
        CB_target = rig.pose.bones[Chain.Target]
        CB_first = rig.pose.bones[Props.name]
        CB_second = rig.pose.bones[Chain.name]
        # iterate over the two bones within the chain... (to save script space)
        for p_bone in [CB_second, CB_first]:
            p_bone.ik_stretch = 0.1
            stretch = rig.pose.bones["GB_STRETCH" + p_bone.name[2:]]
            stretch.bone_group = rig.pose.bone_groups["Gizmo Bones"]
            Pose_Functions_Rigging.Set_IK_Drivers(rig, p_bone, stretch)
            if p_bone == CB_first:
                ik = stretch.constraints.new('IK')
                ik.target, ik.pole_target, ik.show_expanded = rig, rig, False
                ik.subtarget, ik.pole_subtarget = Chain.Target, Chain.Pole
                ik.pole_angle, ik.chain_count, ik.use_stretch = Props.Chain_pole_angle, 2, True
            # the gizmo bones copy the Y scale of the stretch bones...
            gizmo = rig.pose.bones["GB" + p_bone.name[2:]]
            gizmo.bone_group = rig.pose.bone_groups["Gizmo Bones"]
            gizmo.custom_shape, gizmo.custom_shape_scale = bpy.data.objects["B_Shape_Bracket"], 0.7
            copy_scale = gizmo.constraints.new('COPY_SCALE')
            copy_scale.show_expanded, copy_scale.target_space, copy_scale.owner_space = False, 'LOCAL', 'LOCAL'
            copy_scale.target, copy_scale.subtarget = rig, "GB_STRETCH" + p_bone.name[2:]
            copy_scale.use_x, copy_scale.use_z, copy_scale.use_offset = False, False, True
            copy_scale.target_space, copy_scale.owner_space = 'LOCAL', 'LOCAL'
            # with minumum Y scale limited to 1.0... (max is optional)
            limit_scale = gizmo.constraints.new('LIMIT_SCALE')
            limit_scale.show_expanded, limit_scale.owner_space = False, 'LOCAL'
            limit_scale.use_min_y, limit_scale.min_y = True, 1.0
            limit_scale.use_max_y, limit_scale.max_y = True, 2.0
            Pose_Functions_Rigging.Set_IK_Drivers(rig, p_bone, gizmo)
            if p_bone == CB_first:
                ik = gizmo.constraints.new('IK')
                ik.target, ik.pole_target, ik.show_expanded = rig, rig, False
                ik.subtarget, ik.pole_subtarget = Chain.Target, Chain.Pole
                ik.pole_angle, ik.chain_count, ik.use_stretch = Props.Chain_pole_angle, 2, False
            # and the control bone copies the gizmo rotation...
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.show_expanded, copy_rot.target_space, copy_rot.owner_space = False, 'LOCAL', 'LOCAL'
            copy_rot.target, copy_rot.subtarget = rig, gizmo.name
        # and set up the ik chain data for the interface...   
        ik_data = rig.JK_MMT.IK_chain_data.add()
        ik_data.name, ik_data.Chain_side, ik_data.Chain_type = Props.name, Props.Chain_side, Props.Chain_type
        ik_data.Chain_pole_angle, ik_data.End_data.name, ik_data.End_data.Main_axis = Props.Chain_pole_angle, End.name, End.Main_axis
        chain_data = ik_data.Chain_data
        chain_data.name, chain_data.Target, chain_data.Control = Chain.name, Chain.Target, Chain.Control
        chain_data.Control_local = "GB_LOCAL" + Chain.Control[2:]
        chain_data.Control_root = ("AT_ROOT" if Props.Chain_type == 'ARM' else "LT_ROOT") + Chain.Control[2:]
        chain_data.Parent, chain_data.Pole, chain_data.Root = Chain.Parent, Chain.Pole, Chain.Root   
        chain_data.Pole_local = "GB_LOCAL" + Chain.Pole[2:]
        chain_data.Pole_root = ("AT_ROOT" if Props.Chain_type == 'ARM' else "LT_ROOT") + Chain.Pole[2:]
        chain_data.Pole_axis, chain_data.Pole_distance, chain_data.Has_pivots = Chain.Pole_axis, Chain.Pole_distance, Chain.Has_pivots
        # set the custom shape for the target/parent depending on arm or leg..
        side_suffix = "L" if Props.Chain_side == 'LEFT' else 'R'
        control = rig.pose.bones[Chain.Control]
        control.custom_shape = bpy.data.objects["B_Shape_" + ("IK_Hand_" if Props.Chain_type == 'ARM' else "Foot_") +  side_suffix]
        control.custom_shape_scale = 1.5 if Props.Chain_type == 'ARM' else 2.5
        control.bone_group = rig.pose.bone_groups["IK Targets"]
        # and it's floor constraint...
        floor = control.constraints.new('FLOOR')
        floor.target, floor.subtarget, floor.show_expanded = rig, "FT" + End.name[2:], False 
        floor.use_rotation, floor.floor_location = True, 'FLOOR_NEGATIVE_Y'     
        floor.offset = -0.03 if Props.Chain_type == 'ARM' else 0.0
        # and the floor targets shape and group...
        floor_bone = rig.pose.bones["FT" + End.name[2:]]
        floor_bone.custom_shape = bpy.data.objects["B_Shape_" + ("HandFloor_" if Props.Chain_type == 'ARM' else "FootFloor_") + side_suffix]
        floor_bone.custom_shape_scale = 1.5 if Props.Chain_type == 'ARM' else 2.0
        floor_bone.bone_group = rig.pose.bone_groups["Floor Targets"]
        # and the pole targets shape and group...
        pole = rig.pose.bones[Chain.Pole]
        pole.custom_shape = bpy.data.objects["B_Shape_Sphere_End"]
        pole.bone_group = rig.pose.bone_groups["IK Targets"]
        # if it's a leg chain set targets shape and group...
        if Props.Chain_type == 'LEG':
            rig.pose.bones[Chain.Target].custom_shape = bpy.data.objects["B_Shape_Bracket_" + side_suffix]
            rig.pose.bones[Chain.Target].custom_shape_scale = 1.0
            rig.pose.bones[Chain.Target].bone_group = rig.pose.bone_groups["Gizmo Bones"]

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        if bpy.context.active_pose_bone != None:
            active_bone = bpy.context.active_pose_bone
            self.Props.name = active_bone.parent.name
            self.Props.End_data.name = active_bone.name
            self.Props.Chain_data.name = active_bone.parent.parent.name
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        layout.ui_units_x = 25
        row = layout.row()
        label_col = row.column()
        label_col.ui_units_x = 7
        label_col.label(text="General:")
        label_col.label(text="Root Bone:")
        label_col.label(text="End Bone:")
        label_col.label(text="First Bone:")
        label_col.label(text="Second Bone:")
        label_col.label(text="Pole Orientation:")
        prop_col = row.column()
        row = prop_col.row()
        row.prop(self.Props, "Chain_type", text="")
        row.prop(self.Props, "Chain_side", text="")
        row.prop(self.Props.Chain_data, "Has_pivots", text="Add Pivot Bones")
        prop_col.prop_search(self.Props.Chain_data, "Root", armature.pose, "bones", text="")
        row = prop_col.row()
        row.prop_search(self.Props.End_data, "name", armature.pose, "bones", text="")
        if self.Props.Chain_type == 'LEG':
            col = row.column()
            col.ui_units_x = 5
            col.prop(self.Props.End_data, "Main_axis", text="")
        prop_col.prop_search(self.Props, "name", armature.pose, "bones", text="")
        prop_col.prop_search(self.Props.Chain_data, "name", armature.pose, "bones", text="")
        row = prop_col.row()
        row.prop(self.Props.Chain_data, "Pole_axis", text="")
        row.prop(self.Props.Chain_data, "Pole_distance", text="Distance")
        row.prop(self.Props, "Chain_pole_angle", text="Angle")
        

class JK_OT_Remove_IK_Chain(bpy.types.Operator):
    """Removes an IK chain"""
    bl_idname = "jk.remove_ik_chain"
    bl_label = "Remove IK Chain"
    
    Name: StringProperty(name="Name", description="The name of the IK chain to be removed", default="")
    
    def execute(self, context):
        rig = bpy.context.object
        Props = rig.JK_MMT.IK_chain_data[self.Name]
        chain_data = Props.Chain_data
        end_data = Props.End_data
        # unset any IK vs FK options...
        if Props.IKvsFK_limbs != 'NONE':
            Props.IKvsFK_limbs = 'NONE'
        # unset any IK parenting options...
        if Props.IK_parenting != 'NONE':
            Props.IK_parenting = 'NONE'
        # remove end controls if they exist...
        if Props.End_data.Pivot != "":
            bpy.ops.jk.remove_ankle_controls(Name=Props.name)
        # get rid of the copy rotation constraints...
        first = rig.pose.bones[Props.name]
        second = rig.pose.bones[chain_data.name]
        second.constraints.remove(second.constraints["Copy Rotation"])
        first.constraints.remove(first.constraints["Copy Rotation"])
        # get rid of the IK drivers on the gizmo bones...
        Pose_Functions_Rigging.Set_IK_Drivers(rig, None, rig.pose.bones["GB" + Props.name[2:]])
        Pose_Functions_Rigging.Set_IK_Drivers(rig, None, rig.pose.bones["GB_STRETCH" + Props.name[2:]])
        Pose_Functions_Rigging.Set_IK_Drivers(rig, None, rig.pose.bones["GB" + chain_data.name[2:]])
        Pose_Functions_Rigging.Set_IK_Drivers(rig, None, rig.pose.bones["GB_STRETCH" + chain_data.name[2:]])
        # go into edit mode and remove the IK targets...
        bpy.ops.object.mode_set(mode='EDIT')
        for name in [chain_data.Target, chain_data.Pole]:
            rig.data.edit_bones.remove(rig.data.edit_bones[name])
        # and remove the gizmo bones...
        for name in [Props.name, chain_data.name]:
            rig.data.edit_bones.remove(rig.data.edit_bones["GB" + name[2:]])
            rig.data.edit_bones.remove(rig.data.edit_bones["GB_STRETCH" + name[2:]])
        if Props.Chain_type == 'LEG':
            rig.data.edit_bones.remove(rig.data.edit_bones[chain_data.Control])
        # if there are pivots get rid of them as well...
        if chain_data.Has_pivots:
            # kill the chain pivot...
            chain_pivot = rig.data.edit_bones["PB" + chain_data.name[2:]]
            for child in chain_pivot.children:
                child.parent = rig.data.edit_bones[chain_data.Parent]
            rig.data.edit_bones.remove(chain_pivot)
            # kill the owner pivot... (shouldn't have any children?)
            owner_pivot = rig.data.edit_bones["PB" + Props.name[2:]]
            rig.data.edit_bones.remove(owner_pivot)
            # kill the end bone pivot
            end_pivot = rig.data.edit_bones["PB" + end_data.name[2:]]
            for child in end_pivot.children:
                child.parent = end_pivot.parent
            rig.data.edit_bones.remove(end_pivot)
        # remove the floor target
        floor = rig.data.edit_bones["FT" + end_data.name[2:]]
        rig.data.edit_bones.remove(floor)
        # then back to pose mode and remove the chain data...
        bpy.ops.object.mode_set(mode='POSE')
        rig.JK_MMT.IK_chain_data.remove(rig.JK_MMT.IK_chain_data.find(self.Name))
        return {'FINISHED'}