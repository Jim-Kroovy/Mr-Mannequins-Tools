import bpy
import os
import math

def Add_Mute_Constraint_Driver(armature, constraint):
    driver = constraint.driver_add("mute")       
    var = driver.driver.variables.new()
    var.name = "Master_Mute"
    var.type = 'SINGLE_PROP'
    var.targets[0].id = armature
    var.targets[0].data_path = "JK_MMT.Mute_default_constraints"
    driver.driver.expression = "Master_Mute"
    if len(driver.modifiers) > 0:
        driver.modifiers.remove(driver.modifiers[0])

def Add_Hide_Bone_Driver(armature, p_bone):
    driver = p_bone.bone.driver_add("hide")       
    var = driver.driver.variables.new()
    var.name = "Hide_Deform_Bones"
    var.type = 'SINGLE_PROP'
    var.targets[0].id = armature
    var.targets[0].data_path = "JK_MMT.Hide_deform_bones"
    driver.driver.expression = "Hide_Deform_Bones"
    if len(driver.modifiers) > 0:
        driver.modifiers.remove(driver.modifiers[0])

def Get_Distance(start, end):
    x = end[0] - start[0]
    y = end[1] - start[1]
    z = end[2] - start[2]
    distance = math.sqrt((x)**2 + (y)**2 + (z)**2)
    return distance

def Add_Finger_Controls(rig, side):
    # create any bones in edit mode...       
    bpy.ops.object.mode_set(mode='EDIT')
    # get the hand bone...
    hand_bone = rig.data.edit_bones["CB_hand_" + side]
    # set up the finger tip names if they exist...
    end_bones = []
    for child in hand_bone.children:
        if "thumb" in child.name:
            end_bones.append("CB_thumb_03_")
        if "index" in child.name:
            end_bones.append("CB_index_03_")
        if "middle" in child.name:
            end_bones.append("CB_middle_03_")
        if "ring" in child.name:
            end_bones.append("CB_ring_03_")
        if "pinky" in child.name:
            end_bones.append("CB_pinky_03_")    
    # if there are any finger tips set them up...
    if len(end_bones) > 0:
        for name in end_bones:
            e_bone = rig.data.edit_bones[name + side]
            control_bone = rig.data.edit_bones.new(name[:-3] + side)
            control_bone.head = e_bone.parent.parent.head
            control_bone.tail = e_bone.parent.parent.tail
            control_bone.roll = e_bone.parent.parent.roll
            control_bone.parent = e_bone.parent.parent.parent
            control_bone.use_deform = False
            bpy.ops.armature.select_all(action='DESELECT')
            control_bone.select_tail = True
            bpy.ops.transform.translate(value=(0, Get_Distance(e_bone.parent.parent.tail, e_bone.tail), 0), orient_type='NORMAL', orient_matrix=control_bone.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(False, True, False))
            control_bone.layers = [False]*1+[True]+[False]*30
        # set all the bones in pose mode...
        bpy.ops.object.mode_set(mode='POSE')    
        for name in end_bones:
            p_bone = rig.pose.bones[name + side]
            c_bone = rig.pose.bones[name[:-3] + side]
            # end of digit only uses local Z axis...
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.target = rig
            copy_rot.subtarget = c_bone.name
            copy_rot.use_x = False
            copy_rot.use_y = False
            copy_rot.mix_mode = 'BEFORE'
            copy_rot.target_space = 'LOCAL'
            copy_rot.owner_space = 'LOCAL'
            # same for the middle of digit...
            copy_rot = p_bone.parent.constraints.new('COPY_ROTATION')
            copy_rot.target = rig
            copy_rot.subtarget = c_bone.name
            copy_rot.use_x = False
            copy_rot.use_y = False
            copy_rot.mix_mode = 'BEFORE'
            copy_rot.target_space = 'LOCAL'
            copy_rot.owner_space = 'LOCAL'
            # end of digit uses all axes...
            copy_rot = p_bone.parent.parent.constraints.new('COPY_ROTATION')
            copy_rot.target = rig
            copy_rot.subtarget = rig.pose.bones[name[:-3] + side].name
            copy_rot.mix_mode = 'BEFORE'
            copy_rot.target_space = 'LOCAL'
            copy_rot.owner_space = 'LOCAL'
            # set the control bones custom shape...
            c_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
            c_bone.custom_shape_scale = 0.25
            c_bone.bone_group = rig.pose.bone_groups["Control Bones"]

def Add_Foot_Control_Bones(rig, side):
    # create all the bones in edit mode...      
    bpy.ops.object.mode_set(mode='EDIT')
    #bone_names = ["PB_foot_", "LT_foot_", "CB_foot_roll_", "GB_ball_roll_", "GB_foot_roll_"], "GB_foot_"]
    CB_foot = rig.data.edit_bones["CB_foot_" + side] 
    CB_ball = rig.data.edit_bones["CB_ball_" + side]
    # foot pivot bone == to the foot control...       
    PB_foot = rig.data.edit_bones["PB_foot_" + side]
    PB_foot.head = CB_foot.head
    PB_foot.tail = CB_foot.tail
    PB_foot.roll = CB_foot.roll
    PB_foot.parent = CB_foot.parent
    # foot control bone parented to pivot bone...
    CB_foot.parent = PB_foot    
    # leg target == foot control bone but dropped to foot tail and straight... (useful for calculating location with independent IK)
    LT_foot = rig.data.edit_bones.new("LT_foot_" + side)
    LT_foot.head = [CB_foot.tail.x, CB_foot.tail.y, 0]
    LT_foot.tail = [CB_foot.tail.x, CB_foot.tail.y, -0.1]
    LT_foot.roll = 0
    LT_foot.layers = [False]*1+[True]+[False]*30   
    # foot roll control == foot control bone rotated back by 90 degrees on Z axis and parented to the leg target...
    bpy.ops.armature.select_all(action='DESELECT')
    CB_foot_roll = rig.data.edit_bones.new("CB_foot_roll_" + side)
    CB_foot_roll.head = CB_foot.head
    CB_foot_roll.tail = CB_foot.tail
    CB_foot_roll.roll = CB_foot.roll
    CB_foot_roll.parent = LT_foot
    CB_foot_roll.select_tail = True
    bpy.ops.transform.rotate(value=1.5708 if side == "l" else -1.5708, orient_axis='Z', orient_type='NORMAL', orient_matrix=CB_foot_roll.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(False, False, True))
    CB_foot_roll.layers = [False]*1+[True]+[False]*30
    # ball roll gizmo == ball control bone rotated back by 180 degrees on Z axis and parented to the leg target...
    bpy.ops.armature.select_all(action='DESELECT')
    GB_ball_roll = rig.data.edit_bones.new("GB_ball_roll_" + side)
    GB_ball_roll.head = CB_ball.head
    GB_ball_roll.tail = CB_ball.tail
    GB_ball_roll.roll = CB_ball.roll
    GB_ball_roll.parent = LT_foot
    GB_ball_roll.select_tail = True
    bpy.ops.transform.rotate(value=3.141593 if side == "l" else -3.141593, orient_axis='Z', orient_type='NORMAL', orient_matrix=GB_ball_roll.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(False, False, True))
    GB_ball_roll.roll = 1.554827
    GB_ball_roll.layers = [False]*23+[True]+[False]*8  
    # foot roll gizmo == foot control bone dropped to its tail and rotated forward by 90 degrees on Z axis and parented to the ball roll...
    bpy.ops.armature.select_all(action='DESELECT')
    GB_foot_roll = rig.data.edit_bones.new("GB_foot_roll_" + side)
    GB_foot_roll.head = CB_foot.head
    GB_foot_roll.tail = CB_foot.tail
    GB_foot_roll.roll = CB_foot.roll
    GB_foot_roll.parent = GB_ball_roll
    GB_foot_roll.select_head = True
    bpy.ops.transform.translate(value=(0, Get_Distance(CB_foot.head, CB_foot.tail), 0), orient_type='NORMAL', orient_matrix=GB_foot_roll.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(False, True, False))
    GB_foot_roll.select_head = False
    GB_foot_roll.select_tail = True
    bpy.ops.transform.rotate(value=-1.5708 if side == "l" else 1.5708, orient_axis='Z', orient_type='NORMAL', orient_matrix=GB_foot_roll.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(False, False, True))
    GB_foot_roll.layers = [False]*23+[True]+[False]*8
    # foot gizmo == foot control bone parented to the leg target
    GB_foot = rig.data.edit_bones.new("GB_foot_" + side)
    GB_foot.head = CB_foot.head
    GB_foot.tail = CB_foot.tail
    GB_foot.roll = CB_foot.roll
    GB_foot.parent = GB_foot_roll
    GB_foot.layers = [False]*23+[True]+[False]*8
    # add floor target...
    FT_foot = rig.data.edit_bones.new("FT_foot_" + side)
    FT_foot.head = [0.4 if side == "l" else -0.4, 0, 0]
    FT_foot.tail = [0.4 if side == "l" else -0.4, 0, -0.1]
    FT_foot.roll = 0
    FT_foot.layers = [False]*1+[True]+[False]*30    
    # set all the bones in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    ball_bone = rig.pose.bones["CB_ball_" + side]
    copy_rot = ball_bone.constraints.new('COPY_ROTATION')
    copy_rot.target = rig
    copy_rot.subtarget = "GB_ball_roll_" + side
    copy_rot.target_space = 'LOCAL'
    copy_rot.owner_space = 'LOCAL'
    copy_rot.use_x = False
    copy_rot.use_y = False
    copy_rot.invert_z = True
    copy_rot.mix_mode = 'BEFORE'       
    for name in ["PB_foot_", "CB_foot_roll_", "LT_foot_", "GB_ball_roll_", "GB_foot_roll_", "GB_foot_", "FT_foot_"]: 
        p_bone = rig.pose.bones[name + side]
        p_bone.bone.use_deform = False
        if p_bone.name.startswith("PB"):
            # pivot bone copies world space rotation of foot gizmo...
            copy_rot = p_bone.constraints.new('COPY_ROTATION')
            copy_rot.target = rig
            copy_rot.subtarget = "GB" + name[2:] + side
        elif p_bone.name.startswith("CB"):
            # roll control has its rotation limited...
            limit_rot = p_bone.constraints.new('LIMIT_ROTATION')
            limit_rot.use_limit_y = True
            limit_rot.use_limit_z = True
            limit_rot.min_z = -0.523599 if side == "l" else -0.785398
            limit_rot.max_z = 0.785398 if side == "l" else 0.523599
            limit_rot.owner_space = 'LOCAL'
            limit_rot.use_transform_limit = True
            p_bone.custom_shape = bpy.data.objects["B_Shape_Bracket"]
            p_bone.bone_group = rig.pose.bone_groups["Control Bones"]
        elif p_bone.name.startswith("LT"):
            p_bone.custom_shape = bpy.data.objects["B_Shape_Foot_" + side.upper()]
            p_bone.custom_shape_scale = 2.5
            p_bone.bone_group = rig.pose.bone_groups["IK Targets"]
            floor = p_bone.constraints.new('FLOOR')
            floor.target = rig
            floor.subtarget = "FT_foot_" + side
            floor.use_rotation = True
            floor.floor_location = 'FLOOR_NEGATIVE_Y'
            floor.offset = 0.0
        elif p_bone.name.startswith("FT"):
            p_bone.custom_shape = bpy.data.objects["B_Shape_FootFloor_" + side.upper()]
            p_bone.custom_shape_scale = 2.0
            p_bone.bone_group = rig.pose.bone_groups["Floor Targets"]            
        else:
            if p_bone.name != "GB_foot_" + side:
                # roll gizmos copy roll control rotation... (local Z axis)
                copy_rot = p_bone.constraints.new('COPY_ROTATION')
                copy_rot.target = rig
                copy_rot.subtarget = "CB_foot_roll_" + side
                copy_rot.target_space = 'LOCAL'
                copy_rot.owner_space = 'LOCAL'
                copy_rot.use_x = True if "ball" in name else False
                copy_rot.use_y = False
                # and have their rotation limited...
                limit_rot = p_bone.constraints.new('LIMIT_ROTATION')
                limit_rot.use_limit_z = True
                limit_rot.min_z = 0 if "ball" in name else -0.523599
                limit_rot.max_z = 0.785398 if "ball" in name else 0
                limit_rot.owner_space = 'LOCAL'
                limit_rot.use_transform_limit = True
                # and the foot roll has a X location driver to stop it from drifting...            
                if "foot_roll" in name:
                    driver = p_bone.driver_add("location", 0)       
                    var = driver.driver.variables.new()
                    var.name = "Z_Roll"
                    var.type = 'TRANSFORMS'
                    var.targets[0].id = rig
                    var.targets[0].bone_target = "CB" + name[2:] + side
                    var.targets[0].transform_type = 'ROT_Z'
                    var.targets[0].transform_space = 'LOCAL_SPACE'
                    driver.driver.expression = "Z_Roll * 0.05 * -1 if Z_Roll < 0 else 0"
                    if len(driver.modifiers) > 0:
                        driver.modifiers.remove(driver.modifiers[0])
            p_bone.bone_group = rig.pose.bone_groups["Gizmo Bones"]
                         
def Add_Arm_IK_Chain(rig, side):
    # first add the finger controls...
    Add_Finger_Controls(rig, side)
    # create all the bones in edit mode...       
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.reveal(select=False)
    # get references to a couple of bones...
    CB_hand = rig.data.edit_bones["CB_hand_" + side] 
    CB_lowerarm = rig.data.edit_bones["CB_lowerarm_" + side]  
    # the arm target = hand control without a parent...
    AT_hand = rig.data.edit_bones.new("AT_hand_" + side)
    AT_hand.head = CB_hand.head
    AT_hand.tail = CB_hand.tail
    AT_hand.roll = CB_hand.roll
    AT_hand.use_deform = False
    AT_hand.layers = [False]*1+[True]+[False]*30
    # pole target = upperarm moved back on local X axis...
    bpy.ops.armature.select_all(action='DESELECT')
    AT_upperarm = rig.data.edit_bones.new("AT_upperarm_" + side)
    AT_upperarm.head = CB_lowerarm.parent.head
    AT_upperarm.tail = CB_lowerarm.parent.tail
    AT_upperarm.roll = CB_lowerarm.parent.roll
    AT_upperarm.use_deform = False
    AT_upperarm.select_head = True
    bpy.ops.transform.translate(value=(-0.25 if side == "l" else 0.25, 0, 0), orient_type='NORMAL', orient_matrix=CB_lowerarm.parent.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(True, False, False))
    AT_upperarm.layers = [False]*1+[True]+[False]*30
    # add floor target...
    FT_hand = rig.data.edit_bones.new("FT_hand_" + side)
    FT_hand.head = [0.6 if side == "l" else -0.6, 0, 0]
    FT_hand.tail = [0.6 if side == "l" else -0.6, 0, -0.1]
    FT_hand.roll = 0
    FT_hand.layers = [False]*1+[True]+[False]*30
    FT_hand.use_deform = False 
    # hand pivot bone = hand control...
    PB_hand = rig.data.edit_bones["PB_hand_" + side]
    PB_hand.head = CB_hand.head
    PB_hand.tail = CB_hand.tail
    PB_hand.roll = CB_hand.roll
    PB_hand.parent = CB_hand.parent
    # parent the hand control to the pivot...
    CB_hand.parent = PB_hand
    # into pose mode to add constraints...
    bpy.ops.object.mode_set(mode='POSE')   
    # hand pivot copys IK target rotation
    p_bone = rig.pose.bones["PB_hand_" + side]
    copy_rot = p_bone.constraints.new('COPY_ROTATION')
    copy_rot.target = rig
    copy_rot.subtarget = "AT" + p_bone.name[2:]
    # lowerarm holds the IK constraint...
    p_bone = rig.pose.bones["CB_lowerarm_" + side]
    ik = p_bone.constraints.new('IK')
    ik.target = rig
    ik.subtarget = "AT_hand_" + side
    ik.pole_target = rig
    ik.pole_subtarget = "AT_upperarm_" + side
    ik.pole_angle = -3.141593 if side == "l" else 0
    ik.chain_count = 2
    # and set up the ik chain data for the interface...   
    data = rig.JK_MMT.IK_chain_data.add()
    data.Owner_name = p_bone.name
    data.Parent_name = ik.subtarget
    data.Target_name = ik.subtarget
    data.Pole_name = ik.pole_subtarget
    data.Pole_angle = ik.pole_angle        
    data.Root_name = "CB_ik_hand_root"
    data.Chain_name = ("Left " if p_bone.name.endswith("_l") else "Right ") + "Arm"
    # set the custom shape for the hand target..
    rig.pose.bones["AT_hand_" + side].custom_shape = bpy.data.objects["B_Shape_IK_Hand_" + side.upper()]
    rig.pose.bones["AT_hand_" + side].custom_shape_scale = 1.5
    rig.pose.bones["AT_hand_" + side].bone_group = rig.pose.bone_groups["IK Targets"]
    # and it's floor constraint...
    floor = rig.pose.bones["AT_hand_" + side].constraints.new('FLOOR')
    floor.target = rig
    floor.subtarget = "FT_hand_" + side
    floor.use_rotation = True
    floor.floor_location = 'FLOOR_NEGATIVE_Y'
    floor.offset = -0.03
    # and the floor targets shape and group...
    rig.pose.bones["FT_hand_" + side].custom_shape = bpy.data.objects["B_Shape_HandFloor_" + side.upper()]
    rig.pose.bones["FT_hand_" + side].custom_shape_scale = 1.5
    rig.pose.bones["FT_hand_" + side].bone_group = rig.pose.bone_groups["Floor Targets"]
    # and the pole targets shape and group...
    rig.pose.bones["AT_upperarm_" + side].custom_shape = bpy.data.objects["B_Shape_Sphere_End"]
    rig.pose.bones["AT_upperarm_" + side].bone_group = rig.pose.bone_groups["IK Targets"]

def Add_Leg_IK_Chain(rig, side):
    # add the foot controls first...
    Add_Foot_Control_Bones(rig, side)
    # create all the bones in edit mode...       
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.reveal(select=False)
    # get references...
    CB_calf = rig.data.edit_bones["CB_calf_" + side]
    # pole target = thigh moved forward on local X axis...
    bpy.ops.armature.select_all(action='DESELECT')
    LT_thigh = rig.data.edit_bones.new("LT_thigh_" + side)
    LT_thigh.head = CB_calf.parent.head
    LT_thigh.tail = CB_calf.parent.tail
    LT_thigh.roll = CB_calf.parent.roll
    LT_thigh.use_deform = False
    LT_thigh.select_head = True    
    bpy.ops.transform.translate(value=(0.25 if side == "l" else -0.25, 0, 0), orient_type='NORMAL', orient_matrix=CB_calf.parent.matrix.to_3x3(), orient_matrix_type='NORMAL', constraint_axis=(True, False, False))    
    LT_thigh.layers = [False]*1+[True]+[False]*30
    # into pose mode to add constraints...
    bpy.ops.object.mode_set(mode='POSE')
    # calf holds the IK constraint...
    p_bone = rig.pose.bones["CB_calf_" + side]
    ik = p_bone.constraints.new('IK')
    ik.target = rig
    ik.subtarget = "GB_foot_" + side
    ik.pole_target = rig
    ik.pole_subtarget = "LT_thigh_" + side
    ik.pole_angle = -3.141593 if side == "r" else 0
    ik.chain_count = 2
    # and set up the ik chain data for the interface...   
    data = rig.JK_MMT.IK_chain_data.add()
    data.Owner_name = p_bone.name
    data.Parent_name = rig.pose.bones["LT_foot_" + side].name
    data.Target_name = ik.subtarget
    data.Pole_name = ik.pole_subtarget
    data.Pole_angle = ik.pole_angle        
    data.Root_name = "CB_ik_foot_root"
    data.Chain_name = ("Left " if p_bone.name.endswith("_l") else "Right ") + "Leg"
    # set the pole targets custom shape...
    rig.pose.bones["LT_thigh_" + side].custom_shape = bpy.data.objects["B_Shape_Sphere_End"]
    rig.pose.bones["LT_thigh_" + side].bone_group = rig.pose.bone_groups["IK Targets"]

# start the retargeting process... (uses existing bone groups for other things)
def Start_Rig_Retargeting(armature, template_name):
    template = None
    scene = bpy.context.scene
    MMT = scene.JK_MMT
    unit_scale = scene.unit_settings.scale_length
    # load the template...    
    with bpy.data.libraries.load(os.path.join(MMT.MMT_path, template_name + ".blend"), link=False, relative=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name == "UE4_Mannequin_Template"]
        data_to.texts = [name for name in data_from.texts if name == "UE4_Mannequin_Template.py"]
    # check and scale it...
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            template = obj
            #obj.scale = [obj.scale[0] * unit_scale, obj.scale[1] * unit_scale, obj.scale[2] * unit_scale] - reversed scaling for saving?
            obj.scale = [obj.scale[0] * (1 / unit_scale), obj.scale[1] * (1 / unit_scale), obj.scale[2] * (1 / unit_scale)]
            # always apply scale
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # run the clean up script... (stops multiple custom shapes being created for each template used)
    for ref_text in data_to.texts:
            if ref_text is not None:
                # run and unlink the appended text...
                copy_text = bpy.context.copy()
                copy_text['edit_text'] = ref_text
                bpy.ops.text.run_script(copy_text)
                bpy.ops.text.unlink(copy_text)
    # if the template loaded set everything up...
    if template != None:
        armature.data.display_type = 'STICK'
        template.display_type = 'WIRE'
        bpy.ops.object.mode_set(mode='EDIT')
        # end bones or bones with multiple children should be edited/finalised by the user...
        user_edits = ["CB_head", "CB_thumb_03_", "CB_index_03_", "CB_middle_03_", "CB_ring_03_", "CB_pinky_03_", "CB_hand_", "CB_foot_", "CB_ball_"]
        # get the pivot bones so they can be used to offset locations...
        pivot_bones = [bone.name for bone in template.data.edit_bones if bone.name.startswith("PB_")]
        # any extra bones should be created...
        extra_bones = [bone.name for bone in armature.data.edit_bones if "CB_" + bone.name not in template.data.edit_bones]    
        # create the root bone that might not exist...
        if "root" not in armature.data.edit_bones:
            root = armature.data.edit_bones.new("root")
            root.head = [0, 0, 0]
            root.tail = [0, 0.23196600377559662, 0]
            root.roll = 0
            # any bones without a parent should be parented to the root...
            for e_bone in armature.data.edit_bones:
                if e_bone.parent == None:
                    e_bone.parent = root                            
        # add controls for any extra bones...
        for name in extra_bones:
            deform_bone = armature.data.edit_bones[name]
            template_bone = template.data.edit_bones.new("CB_" + name)
            template_bone.head = deform_bone.head
            template_bone.tail = deform_bone.tail
            template_bone.roll = deform_bone.roll
            template_bone.use_deform = False
            template_bone.use_inherit_rotation = False
            template_bone.layers = [False]*16+[True]+[False]*15
        # then match any parenting and switch inherit rotations off...    
        for e_bone in template.data.edit_bones:
            if e_bone.name[3:] in armature.data.edit_bones:
                d_bone = armature.data.edit_bones[e_bone.name[3:]]
                if d_bone.parent != None:
                    e_bone.parent = template.data.edit_bones["CB_" + d_bone.parent.name]         
                    e_bone.use_inherit_rotation = False
                    e_bone.use_inherit_scale = False        
        # now into pose mode and clear all transforms on all bones
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
        # pose the template roughly to the target armature...
        for p_bone in template.pose.bones:
            if p_bone.name[3:] in armature.pose.bones:
                # add a world space copy location to the target armatures deform bone...
                copy_loc = p_bone.constraints.new('COPY_LOCATION')
                copy_loc.target = armature
                copy_loc.subtarget = p_bone.name[3:]           
                # if it's an extra bone...
                if p_bone.name[3:] in extra_bones:                
                    # if extra bone has only one child stretch to it...
                    if len(p_bone.children) == 1:
                        ik = p_bone.constraints.new('IK')
                        ik.target = armature
                        ik.chain_count = 1                       
                        ik.subtarget = armature.pose.bones[p_bone.children[0].name[3:]].name
                        p_bone.ik_stretch = 1
                        p_bone.bone_group = template.pose.bone_groups["Control Bones"]
                     # if there are multiple or no children...                
                    else:
                        # stop inheritance of scale...
                        p_bone.bone.use_inherit_scale = False
                        # if the bone has no children make it pink...
                        if len(p_bone.children) == 0:
                            p_bone.bone_group = template.pose.bone_groups["Gizmo Bones"]
                        # if it does have children make it purple...
                        else:
                            p_bone.bone_group = template.pose.bone_groups["Mechanism Bones"]
                # if the name of the pose bone is in the user edits then just add it to a different bone group...
                elif any(p_bone.name.startswith(name) for name in user_edits):
                    p_bone.bone_group = template.pose.bone_groups["Mechanism Bones"]
                # if it's a twist bone... (add in some options here? these could be a little tricky to get tricky to get right)
                elif "twist" in p_bone.name: # and p_bone.name not in pivot_bones:
                    # if its a twist control...
                    if p_bone.name.startswith("CB_"):
                        # its location might need editing so change the copy location constraint target...
                        copy_loc.target = template
                        copy_loc.subtarget = "PB" + p_bone.name[2:]
                        # and make it locally offset...
                        copy_loc.target_space = 'LOCAL'
                        copy_loc.owner_space = 'LOCAL'
                        copy_loc.use_offset = True
                        # if its the lower arm or calf...
                        if "lowerarm" in p_bone.name or "calf" in p_bone.name:                
                            # add copy rotation... (making the wrist/ankle follow hand/foot Y is dependent on the hand/foot Y axis)               
                            copy_rot = p_bone.constraints.new('COPY_ROTATION')
                            # set up most of copy rotation...
                            copy_rot.target = template
                            copy_rot.target_space = 'LOCAL'
                            copy_rot.owner_space = 'LOCAL'
                            copy_rot.use_x = False
                            copy_rot.use_z = False
                            if "calf" in p_bone.name:                                        
                                copy_rot.subtarget = "CB_foot_" + ("l" if p_bone.name.endswith("_l") else "r")
                            else:
                                copy_rot.subtarget = "CB_hand_" + ("l" if p_bone.name.endswith("_l") else "r")                                                              
                        p_bone.bone_group = template.pose.bone_groups["Mechanism Bones"]
                    else:
                        p_bone.bone.hide = True                            
                elif "ik" in p_bone.name:
                    copy_rot = p_bone.constraints.new('COPY_ROTATION')
                    copy_rot.target = template
                    if "root" in p_bone.name:
                        copy_rot.subtarget = "CB_root"
                    elif "gun" in p_bone.name:
                        copy_rot.subtarget = "CB_hand_r"
                    elif "hand" in p_bone.name:
                        copy_rot.subtarget = "CB_hand_" + ("l" if p_bone.name.endswith("_l") else "r")                
                    elif "foot" in p_bone.name:
                        copy_rot.subtarget = "CB_foot_" + ("l" if p_bone.name.endswith("_l") else "r")
                    #p_bone.bone.hide = True                    
                # if it's a pivot bone just hide it...
                elif p_bone.name in pivot_bones:
                    p_bone.bone.hide = True                 
                # if the bone doesnt always need to be finalised by the user...
                elif p_bone.name != "CB_root":
                    # add stretching IK constraint...
                    ik = p_bone.constraints.new('IK')
                    ik.target = armature
                    ik.chain_count = 1
                    p_bone.ik_stretch = 1
                    # template multi child bones can stretch to specific children
                    if "spine_03" in p_bone.name:
                        ik.subtarget = "neck_01"
                    elif "pelvis" in p_bone.name:
                        ik.subtarget = "spine_01"
                    elif "calf" in p_bone.name:
                        ik.subtarget = "foot_" + ("l" if p_bone.name.endswith("_l") else "r")                    
                    elif p_bone.name[3:] in armature.pose.bones:
                        deform_bone = armature.pose.bones[p_bone.name[3:]]
                        ik.subtarget = deform_bone.children[0].name                            
            # if the template bone does not have a deform bone to control...
            else:
                # add to removal bones and hide it...
                p_bone.bone_group = template.pose.bone_groups["IK Targets"]
                p_bone.bone.hide = True
        # save the name of the armature we are retargeting too...
        template.JK_MMT.Retarget_target = armature.name                    
        template.name = armature.name + "_Retarget"

def Add_Deform_Mechanism(armature, template):
    # in edit mode add all the mechanism bones to the template armature...
    for deform_bone in armature.data.edit_bones:
        # connected deform bones would require an entirely different system...
        deform_bone.use_connect = False
        mech_bone = template.data.edit_bones.new("MB_" + deform_bone.name)
        mech_bone.head = deform_bone.head
        mech_bone.tail = deform_bone.tail
        mech_bone.roll = deform_bone.roll
        mech_bone.parent = template.data.edit_bones["CB_" + deform_bone.name]
        mech_bone.use_deform = False
        mech_bone.use_inherit_rotation = True             
    # in pose mode set up all the deform bones copy transforms constraints
    bpy.ops.object.mode_set(mode='POSE')
    for p_bone in armature.pose.bones:
        copy_trans = p_bone.constraints.new("COPY_TRANSFORMS")
        copy_trans.target = template
        copy_trans.subtarget = "MB_" + p_bone.name        
        p_bone.bone.layers = [False]*8+[True]+[False]*23
        Add_Hide_Bone_Driver(template, p_bone)
        template.pose.bones["MB_" + p_bone.name].bone.layers = [False]*24+[True]+[False]*7
        template.pose.bones["MB_" + p_bone.name].bone_group = template.pose.bone_groups["Mechanism Bones"]
        Add_Hide_Bone_Driver(template, template.pose.bones["MB_" + p_bone.name])

def Force_Template_Pose(target, template_name, force_rot, force_loc):
    scene = bpy.context.scene
    MMT = scene.JK_MMT
    unit_scale = scene.unit_settings.scale_length
    default_dir = os.path.join(MMT.MMT_path, "MMT_Stash")    
    # load the template... (again)    
    with bpy.data.libraries.load(os.path.join(MMT.MMT_path, template_name + ".blend"), link=False, relative=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name == "UE4_Mannequin_Template"]
        data_to.texts = [name for name in data_from.texts if name == "UE4_Mannequin_Template.py"]
    # check and scale it...
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            template = obj
            #obj.scale = [obj.scale[0] * unit_scale, obj.scale[1] * unit_scale, obj.scale[2] * unit_scale] - reversed scaling for saving?
            obj.scale = [obj.scale[0] * (1 / unit_scale), obj.scale[1] * (1 / unit_scale), obj.scale[2] * (1 / unit_scale)]
            # always apply scale
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # run the clean up script... (stops multiple custom shapes being created for each template used)
    for ref_text in data_to.texts:
            if ref_text is not None:
                # run and unlink the appended text...
                copy_text = bpy.context.copy()
                copy_text['edit_text'] = ref_text
                bpy.ops.text.run_script(copy_text)
                bpy.ops.text.unlink(copy_text)
    # if the template loaded set everything up...
    if template != None:
        for p_bone in target.pose.bones:
            # check if the bone exsists in the template...
            if p_bone.name in template.pose.bones:
                # if we want template bone rotations...
                if force_rot:
                    copy_rot = p_bone.constraints.new('COPY_ROTATION')
                    copy_rot.name = "MMT Pose - Copy Rotation"
                    copy_rot.target = template
                    copy_rot.subtarget = p_bone.name
                # if we want template bone locations...
                if force_loc:
                    copy_loc = p_bone.constraints.new('COPY_LOCATION')
                    copy_loc.name = "MMT Pose - Copy Location"
                    copy_loc.target = template
                    copy_loc.subtarget = p_bone.name                                
        bpy.ops.object.mode_set(mode='OBJECT')
        # iterate through all objects...
        for obj in bpy.data.objects:
            # if it's a mesh...
            if obj.type == 'MESH':
                # iterate through it's modifiers...
                for modifier in obj.modifiers:
                    # if it's an armature modifier targeting the retarget target...
                    if modifier.type == 'ARMATURE' and modifier.object == target:
                        modifier.name = "Armature"
                        # apply and re-add armature modifiers...
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier="Armature")
                        modifier = obj.modifiers.new(type='ARMATURE', name="Armature")
                        modifier.object = target
        # go back to the target and apply the armature
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply(selected=False)
        
        for p_bone in target.pose.bones:
            for constraint in p_bone.constraints:
                if constraint.name.startswith("MMT Pose - "):
                    p_bone.constraints.remove(constraint)
        
        bpy.data.objects.remove(template)
            
# apply the retargeted bone transforms...
def Apply_Rig_Retargeting(armature, template, template_name):
    # first we'll load any custom shapes that aren't already in the .blend
    MMT = bpy.context.scene.JK_MMT
    default_dir = os.path.join(MMT.MMT_path, "MMT_Stash")    
    with bpy.data.libraries.load(os.path.join(default_dir, "ARMATURE_UE4_Mannequin_Skeleton.blend"), link=False, relative=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name not in bpy.data.objects and "B_Shape_" in name]
    # then we can deselect the deform armature..
    bpy.ops.object.mode_set(mode='OBJECT')
    armature.select_set(False)
    bpy.ops.object.mode_set(mode='POSE')
    # open all the layers of the template and unhide any hidden bones and apply the created pose...
    template.data.layers = [True]*32
    bpy.ops.pose.reveal(select=False)
    bpy.ops.pose.armature_apply(selected=False)
    # select everything and get rid of all the constraints used to retarget...
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.constraints_clear()
    # back to object mode to select the deform armature again..,
    bpy.ops.object.mode_set(mode='OBJECT')
    armature.select_set(True)
    # into pose mode to get the names of all the bones that need removing from the template...
    bpy.ops.object.mode_set(mode='POSE')
    remove_bones = [bone.name for bone in template.pose.bones if bone.bone_group.name == "IK Targets"]    
    # enter edit mode to get rid of all the bones that weren't present...
    bpy.ops.object.mode_set(mode='EDIT')
    for name in remove_bones:
        template.data.edit_bones.remove(template.data.edit_bones[name])        
    # get all the pivot bones if they still exist...
    pivot_bones = [bone.name for bone in template.data.edit_bones if bone.name.startswith("PB_")]
    # and sort out pivot bone parenting
    for name in pivot_bones:
        pivot_bone = template.data.edit_bones[name]
        control_bone = template.data.edit_bones["CB" + name[2:]]
        pivot_bone.head = control_bone.head
        pivot_bone.tail = control_bone.tail
        pivot_bone.roll = control_bone.roll      
        if "twist" in name:
            if "upperarm" in name or "thigh" in name:                
                pivot_bone.parent = template.data.edit_bones["PB_" + ("thigh_" if "thigh" in name else "upperarm_") + ("l" if name.endswith("_l") else "r")]
            else:
                pivot_bone.parent = template.data.edit_bones["PB_" + ("calf_" if "calf" in name else "lowerarm_") + ("l" if name.endswith("_l") else "r")]            
            control_bone.parent = pivot_bone
        elif "upperarm" in name or "thigh" in name:
            pivot_bone.parent = pivot_bone.parent.parent
        #else:
            #pivot_bone.parent = control_bone.parent - #should already be parented here?
    # add in the mechanism bones...
    Add_Deform_Mechanism(armature, template)
    bpy.ops.object.mode_set(mode='OBJECT')
    # iterate through all objects...
    for obj in bpy.data.objects:
        # if it's a mesh...
        if obj.type == 'MESH':
            # iterate through it's modifiers...
            for modifier in obj.modifiers:
                # if it's an armature modifier targeting the retarget target...
                if modifier.type == 'ARMATURE' and modifier.object == armature:
                    modifier.name = "Armature"
                    # set it to target the template instead...
                    modifier.object = template
    # go back to object mode make sure selection is correct and join the target into the template...        
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    template.select_set(True)
    bpy.context.view_layer.objects.active = template
    bpy.ops.object.join()
   
    # if we want to force the template pose...
    if template.JK_MMT.Force_template_rotations or template.JK_MMT.Force_template_locations:
        Force_Template_Pose(template, template_name, template.JK_MMT.Force_template_rotations, template.JK_MMT.Force_template_locations)
    
    # then into pose mode to sort out the twist bone constraints...
    bpy.ops.object.mode_set(mode='POSE')
    for name in pivot_bones:
        pivot_bone = template.pose.bones[name]
        control_bone = template.pose.bones["CB" + name[2:]]        
        if "twist" in name:
            if "upperarm" in name or "thigh" in name:
                limb_bone = template.pose.bones["CB_" + ("thigh_" if "thigh" in name else "upperarm_") + ("l" if name.endswith("_l") else "r")]
                damp_track = control_bone.constraints.new('DAMPED_TRACK')
                damp_track.target = template
                damp_track.subtarget = limb_bone.name
                damp_track.head_tail = 1.0            
                limit_rot = control_bone.constraints.new('LIMIT_ROTATION')
                limit_rot.use_limit_x = True
                limit_rot.min_x = -0.261799
                if "thigh" in name:                
                    limit_rot.max_x = 1.570796
                    limit_rot.use_limit_z = True
                    limit_rot.min_z = -1.570796
                    limit_rot.max_z = 1.570796
                else:    
                    limit_rot.max_x = 2.443461
                limit_rot.use_transform_limit = True
                limit_rot.owner_space = 'LOCAL'         
            elif "lowerarm" in name or "calf" in name:                
                twist_ik = control_bone.constraints.new('IK')
                twist_ik.target = template
                twist_ik.subtarget = "CB_" + ("foot_" if "calf" in name else "hand_") + ("l" if name.endswith("_l") else "r")
                twist_ik.chain_count = 1
                twist_ik.use_location = False
                twist_ik.use_rotation = True
                twist_ik.influence = 0.5
        elif "lowerarm" in name or "calf" in name:
            copy_rot = pivot_bone.constraints.new('COPY_ROTATION')
            copy_rot.target = template
            copy_rot.subtarget = "CB" + pivot_bone.name[2:]
        elif "upperarm" in name:
            copy_loc = pivot_bone.constraints.new('COPY_LOCATION')
            copy_loc.target = template
            copy_loc.subtarget = template.pose.bones["CB_upperarm_" + ("l" if name.endswith("_l") else "r")].parent.name
            copy_loc.head_tail = 1.0
    # add in the limb controls if possible...
    if "CB_foot_l" in template.pose.bones and "CB_ball_l" in template.pose.bones:
        Add_Leg_IK_Chain(template, "l")
    if "CB_foot_r" in template.pose.bones and "CB_ball_r" in template.pose.bones:
        Add_Leg_IK_Chain(template, "r")
    if "CB_hand_l" in template.pose.bones:
        Add_Arm_IK_Chain(template, "l")
    if "CB_hand_r" in template.pose.bones:
        Add_Arm_IK_Chain(template, "r")
    # add the spine 02 copy spine 01 rotation...
    if "CB_spine_02" in template.pose.bones and "CB_spine_01" in template.pose.bones:
        lumbar_copy_rot = template.pose.bones["CB_spine_02"].constraints.new('COPY_ROTATION')
        lumbar_copy_rot.target = template
        lumbar_copy_rot.subtarget = "CB_spine_01"
        lumbar_copy_rot.mix_mode = 'BEFORE'  
        lumbar_copy_rot.target_space = 'LOCAL'
        lumbar_copy_rot.owner_space = 'LOCAL'
    # set the templates rig type to custom for the interface options...
    template.JK_MMT.Rig_type = 'CUSTOM'    
    # finally do a quick clean up of the inheritance, bone groups and IK limits etc...
    bpy.ops.object.mode_set(mode='POSE')
    for p_bone in template.pose.bones:
        p_bone.bone.use_inherit_rotation = True
        p_bone.bone.use_inherit_scale = True
        p_bone.ik_stretch = 0.0
        if p_bone.bone.use_deform:
            p_bone.bone_group = template.pose.bone_groups["Deform Bones"]
        elif p_bone.name.startswith("CB_"):
            p_bone.bone_group = template.pose.bone_groups["Control Bones"]
            # this condition seems to work but it's only good for 2 bone IK chains...
            if any("IK" in child.constraints for child in p_bone.children) or "IK" in p_bone.constraints:
                p_bone.use_ik_limit_x = True
                p_bone.use_ik_limit_y = True
                p_bone.use_ik_limit_z = True
            # if it's a default IK control bone set it up it's constraints...    
            if p_bone.name in ["CB_ik_hand_l", "CB_ik_hand_r", "CB_ik_hand_gun", "CB_ik_foot_l", "CB_ik_foot_r", "CB_ik_foot_root", "CB_ik_hand_root"]:                    
                if "root" in p_bone.name:
                        copy_rot = p_bone.constraints.new('COPY_ROTATION')
                        copy_rot.target = template
                        copy_rot.subtarget = "CB_root"
                        copy_rot.mix_mode = 'BEFORE'
                        copy_rot.target_space = 'LOCAL'
                        copy_rot.owner_space = 'LOCAL'
                        copy_loc = p_bone.constraints.new('COPY_LOCATION')
                        copy_loc.target = template
                        copy_loc.subtarget = "CB_root"
                        copy_loc.use_offset = True
                        copy_loc.target_space = 'LOCAL'
                        copy_loc.owner_space = 'LOCAL'
                elif "hand" in p_bone.name:                                                 
                    copy_transform = p_bone.constraints.new('COPY_TRANSFORMS')
                    copy_transform.target = template                                            
                    if "gun" in p_bone.name or p_bone.name.endswith("_r"):                        
                        copy_transform.subtarget = "CB_hand_r"
                    else:
                        copy_transform.subtarget = "CB_hand_l"                        
                elif "foot" in p_bone.name:
                    copy_transform = p_bone.constraints.new('COPY_TRANSFORMS')
                    copy_transform.target = template                                            
                    if p_bone.name.endswith("_r"):                        
                        copy_transform.subtarget = "CB_foot_r"
                    else:
                        copy_transform.subtarget = "CB_foot_l"                    
            # add the mute driver to all control bone constraints...
            for constraint in p_bone.constraints:
                Add_Mute_Constraint_Driver(template, constraint)    
    # if we turned off custom shapes during re-target turn them back on again...
    if not template.data.show_bone_custom_shapes:
        template.data.show_bone_custom_shapes = True
        

# not currently used...
def Toggle_Remove_Bones(template, bool):
    for p_bone in template.pose.bones:
        if p_bone.bone_group == template.pose.bone_groups["IK Targets"]:
            p_bone.bone.hide = bool