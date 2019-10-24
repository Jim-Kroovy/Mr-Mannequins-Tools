import bpy

#---------- NOTES -----------------------------------------------------------------------------

# So this is a bunch of functions for IK options... so whether we are using IK roots for the targets and if they are always/never parented as well as head tracking...
# Both independant and parented IK can be useful so there is a switchable method with a property that can be keyframed...
# This still needs more testing but it's just about ready for use... I still need to figure out the dependancy/parenting of the IK roots themselves though.

# If using switchable IK parenting and IK vs FK together it seems to make more sense to force the parenting off while using the FK so my scripts don't have to manage two sets of IK targets...

#---------- FUNCTIONS -------------------------------------------------------------------------

# one little message box function... (just in case)
def ShowMessage(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# adds a driver variable using variable inputs...
def Add_Driver_Var(driver, armature, v_name, c_int):
    var = driver.driver.variables.new()
    var.name = v_name
    var.type = 'SINGLE_PROP'
    var.targets[0].id = armature
    if v_name == "UseP":
        var.targets[0].data_path = 'JK_MMT.IK_chain_data[' + str(c_int) + '].Chain_use_parent'
    elif v_name == "UseFK":
        var.targets[0].data_path = 'JK_MMT.IK_chain_data[' + str(c_int) + '].Chain_use_fk'
    elif v_name == "Master_Mute":
        var.targets[0].data_path = 'JK_MMT.Mute_default_constraints'
    
# adds a driver to control muting a constraint...        
def Add_Mute_Driver(bone, armature, constraint, reverse):
    driver = constraint.driver_add("mute")
    driver.driver.type = 'SCRIPTED'
    # add variable...
    Add_Driver_Var(driver, armature, "Master_Mute", None)
    # set expression...
    condition = ("not Master_Mute" if reverse else "Master_Mute")
    driver.driver.expression = condition
    # remove unwanted curve modifier...
    if len(driver.modifiers) > 0:
        driver.modifiers.remove(driver.modifiers[0])

# adds a driver to hide a bone... (if the chain is registered in the chain data of the armature)
def Add_Hide_Driver(data_int, armature, b_bone, var_name_a, var_name_b, reverse):
    driver = b_bone.driver_add("hide")
    driver.driver.type = 'SCRIPTED'
    # add first variable...
    Add_Driver_Var(driver, armature, var_name_a, data_int)
    if var_name_b != None:
        Add_Driver_Var(driver, armature, var_name_b, data_int)
        condition = ("(not " + var_name_a + ") or " + var_name_b if reverse else var_name_a + " and (not " + var_name_b + ")")
    else:
        condition = ("not " + var_name_a if reverse else data_int)
    driver.driver.expression = condition
    # remove unwanted curve modifier...
    if len(driver.modifiers) > 0:
        driver.modifiers.remove(driver.modifiers[0])
                
# adds offset FK vs IK to all the digits...
def Add_OffsetFK_IKvsFK_Digits(armature):
    # show all layers...
    layers = armature.data.layers[:]
    armature.data.layers = [True]*32
    bpy.ops.pose.reveal(select=True)
    # get the names of all the finger bones...
    f_bones = [bone.name for bone in armature.pose.bones if any(name in bone.name for name in ["CB_thumb_0", "CB_index_0", "CB_middle_0", "CB_ring_0", "CB_pinky_0"])]
    # these are the tail locations for the finger IK targets...
    f_target_tails = {"DT_index_l" : (0.6653876304626465, -0.09842129796743393, 0.9145689010620117),
        "DT_middle_l" : (0.694439709186554, -0.07562527060508728, 0.9048196077346802),
        "DT_pinky_l" : (0.6846345067024231, -0.010573631152510643, 0.9274247288703918),
        "DT_ring_l" : (0.6859810948371887, -0.047431282699108124, 0.9056609869003296),
        "DT_thumb_l" : (0.5859565734863281, -0.12965771555900574, 0.9678245782852173),
        "DT_index_r" : (-0.6653879284858704, -0.09842322021722794, 0.9145672917366028),
        "DT_middle_r" : (-0.6944392323493958, -0.07562658935785294, 0.9048161506652832),
        "DT_pinky_r" : (-0.6846341490745544, -0.010573622770607471, 0.9274291396141052),
        "DT_ring_r" : (-0.6859810948371887, -0.04743190109729767, 0.9056618809700012),
        "DT_thumb_r" : (-0.5859561562538147, -0.12965863943099976, 0.9678242206573486)}
    # these are the head locations for the finger floor targets...
    f_floor_heads = {"FT_index_l" : (0.6488967537879944, -0.017741473391652107, 0),
        "FT_middle_l" : (0.6545215249061584, 0.001011071726679802, 0),
        "FT_pinky_l" : (0.6334614157676697, 0.03494163230061531, 0),
        "FT_ring_l" : (0.6484405398368835, 0.01734289713203907, 0),
        "FT_thumb_l" : (0.6076781749725342, -0.035771310329437256, 0),
        "FT_index_r" : (-0.6488967537879944, -0.017741473391652107, 0),
        "FT_middle_r" : (-0.6545215249061584, 0.001011071726679802, 0),
        "FT_pinky_r" : (-0.6334614157676697, 0.03494163230061531, 0),
        "FT_ring_r" : (-0.6484405398368835, 0.01734289713203907, 0),
        "FT_thumb_r" : (-0.6076781749725342, -0.035771310329437256, 0)}        
    f_gizmos = []
    # enter edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    # to create the floor targets...
    for key, value in f_floor_heads.items():
        e_bone = armature.data.edit_bones.new(key)
        e_bone.head = value
        e_bone.tail = [value[0], value[1], -0.05]
        e_bone.roll = 0
        e_bone.parent = armature.data.edit_bones["FT_hand_" + ("l" if e_bone.name.endswith("_l") else "r")]
    # then into pose mode to set them up...
    bpy.ops.object.mode_set(mode='POSE')
    for key in f_floor_heads:
        p_bone = armature.pose.bones[key]
        p_bone.custom_shape = bpy.data.objects["B_Shape_Circle"]
        p_bone.custom_shape_scale = 0.25
        p_bone.bone_group = armature.pose.bone_groups["Floor Targets"]
        p_bone.bone.layers = [False]*1+[True]+[False]*30
        p_bone.bone.use_deform = False    
    # deselect any selected pose bones...
    bpy.ops.pose.select_all(action='DESELECT')
    # loop through all the finger bones and select them...
    for bone in f_bones:
        p_bone = armature.pose.bones[bone]
        p_bone.bone.select = True
    # back to edit mode and duplicate them...
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.duplicate(do_flip_names=False)
    # rename them...
    for e_bone in bpy.context.selected_bones:
        e_bone.name = "GB" + e_bone.name[2:-4]
        f_gizmos.append(e_bone.name)
    # and back to pose mode to set them up...
    bpy.ops.object.mode_set(mode='POSE')
    for bone in f_gizmos:
        p_bone = armature.pose.bones[bone]
        p_bone.custom_shape = None
        p_bone.custom_shape_scale = 1
        p_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
        p_bone.bone.layers = [False]*23+[True]+[False]*8
        p_bone.bone.use_deform = False    
    # then select only the end bones...
    bpy.ops.pose.select_all(action='DESELECT')    
    for bone in f_bones:
        p_bone = armature.pose.bones[bone]
        constraint = p_bone.constraints["Copy Rotation"]
        constraint.subtarget = "GB" + p_bone.name[2:]
        constraint.use_x = True
        constraint.use_y = True
        if "03" in bone:
            p_bone.bone.select = True
    # once more into edit mode...        
    bpy.ops.object.mode_set(mode='EDIT')
    # duplicate those end bones...
    bpy.ops.armature.duplicate(do_flip_names=False)
    # and rename them and set their tails, rolls and parents...
    for e_bone in bpy.context.selected_bones:
        o_bone = armature.data.edit_bones[e_bone.name[:-4]]
        e_bone.name = "DT" + e_bone.name[2:-8] + ("l" if e_bone.name.endswith("_l.001") else "r")
        e_bone.tail = f_target_tails[e_bone.name]
        e_bone.head = o_bone.tail
        e_bone.roll = o_bone.roll
        e_bone.parent = armature.data.edit_bones["CB" + e_bone.name[2:]]
    # then back to pose mode to set up their floor targets...
    bpy.ops.object.mode_set(mode='POSE')
    for p_bone in armature.pose.bones:
        if "DT" in p_bone.name:
            p_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
            p_bone.custom_shape_scale = 0.25
            p_bone.bone_group = armature.pose.bone_groups["IK Targets"]
            p_bone.bone.layers = [False]*1+[True]+[False]*30
            p_bone.bone.use_deform = False
            p_bone.bone.use_inherit_scale = False
            constraint = p_bone.constraints.new("FLOOR")
            constraint.name = "Finger IK - Floor"
            constraint.target = armature
            constraint.subtarget = "FT" + p_bone.name[2:]
            constraint.use_rotation = True
            constraint.floor_location = 'FLOOR_NEGATIVE_Y'
    # finally just loop through the gizmo bones to add the IK constraints...    
    for bone in f_gizmos:
        if "03" in bone:
            p_bone = armature.pose.bones[bone]
            constraint = p_bone.constraints.new("IK")
            constraint.target = armature
            constraint.subtarget = "DT" + bone[2:-4] + ("l" if bone.endswith("_l") else "r")
            constraint.chain_count = 3
    # return the armatures layers once finished...
    armature.data.layers = layers
    
# removes offset FK vs IK from all the digits...
def Remove_OffsetFK_IKvsFK_Digits(armature):
    f_bones = [bone.name for bone in armature.pose.bones if any(name in bone.name for name in ["CB_thumb_0", "CB_index_0", "CB_middle_0", "CB_ring_0", "CB_pinky_0"])]
    f_floor_targets = [bone.name for bone in armature.pose.bones if any(name in bone.name for name in ["FT_thumb", "FT_index_", "FT_middle_", "FT_ring_", "FT_pinky"])]
    f_ik_targets = [bone.name for bone in armature.pose.bones if any(name in bone.name for name in ["DT_thumb", "DT_index_", "DT_middle_", "DT_ring_", "DT_pinky"])]
    for bone in f_bones:
        p_bone = armature.pose.bones[bone]
        constraint = p_bone.constraints["Copy Rotation"]
        constraint.subtarget = p_bone.name[:-4] + ("l" if p_bone.name.endswith("_l") else "r")
        if "02" in bone or "03" in bone:
            constraint.use_x = False
            constraint.use_y = False
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in f_bones:
        e_bone = armature.data.edit_bones["GB" + bone[2:]]
        armature.data.edit_bones.remove(e_bone)
    for bone in f_floor_targets:
        e_bone = armature.data.edit_bones[bone]
        armature.data.edit_bones.remove(e_bone)
    for bone in f_ik_targets:
        e_bone = armature.data.edit_bones[bone]
        armature.data.edit_bones.remove(e_bone)
    bpy.ops.object.mode_set(mode='POSE')

# adds default mute drivers to limb IK constraints...
def Add_UseIK_IKvsFK_Limbs(armature):
    for bone in [armature.pose.bones[name] for name in [data.Owner_name for data in armature.JK_MMT.IK_chain_data]]:
        constraint = bone.constraints["IK"]
        Add_Mute_Driver(bone, armature, constraint, False)

# removes default mute drivers to limb IK constraints...
def Remove_UseIK_IKvsFK_Limbs(armature):
    for bone in [armature.pose.bones[name] for name in [data.Owner_name for data in armature.JK_MMT.IK_chain_data]]:
        constraint = bone.constraints["IK"]
        constraint.driver_remove('mute')
    
# adds offset FK by telling control bones to copy the rotation of a new IK chain...
def Add_OffsetFK_IKvsFK_Limbs(armature):
    # show all armature layers...
    layers = armature.data.layers[:]
    armature.data.layers = [True]*32
    bpy.ops.pose.reveal(select=True)
    IK_owners = [data.Owner_name for data in armature.JK_MMT.IK_chain_data]    
    # deselect everything then select all the IK chain bones...
    bpy.ops.pose.select_all(action='DESELECT')
    for bone in IK_owners:
        p_bone = armature.pose.bones[bone]
        p_bone.bone.select = True
        p_bone.parent.bone.select = True
    # enter edit mode and duplicate them...
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.duplicate(do_flip_names=False)
    # rename them...
    for e_bone in bpy.context.selected_bones:
        e_bone.name = "GB" + e_bone.name[2:-4]
    # go back to pose mode to set everything else up...
    bpy.ops.object.mode_set(mode='POSE')
    for bone in IK_owners:
        p_bone = armature.pose.bones["GB" + bone[2:]]
        p_bone.custom_shape = None
        p_bone.parent.custom_shape = None
        p_bone.custom_shape_scale = 1
        p_bone.parent.custom_shape_scale = 1
        p_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
        p_bone.parent.bone_group = armature.pose.bone_groups["Gizmo Bones"]
        p_bone.bone.layers = [False]*23+[True]+[False]*8
        p_bone.parent.bone.layers = [False]*23+[True]+[False]*8
        # switch pose bone to the original constraint owner...
        p_bone = armature.pose.bones[bone]
        # remove it's IK constraint...
        p_bone.constraints.remove(p_bone.constraints["IK"])
        # add an offset local to local copy rotation constraint targeting the new IK owner...
        constraint = p_bone.constraints.new("COPY_ROTATION")
        constraint.name = "Offset FK - Copy Rotation"
        constraint.target = armature
        constraint.subtarget = "GB" + bone[2:]
        constraint.target_space = 'LOCAL'
        constraint.owner_space = 'LOCAL'
        constraint.use_offset = True
        Add_Mute_Driver(p_bone, armature, constraint, False)
        # and the same for it's parent...
        constraint = p_bone.parent.constraints.new("COPY_ROTATION")
        constraint.name = "Offset FK - Copy Rotation"
        constraint.target = armature
        constraint.subtarget = "GB" + p_bone.parent.name[2:]
        constraint.target_space = 'LOCAL'
        constraint.owner_space = 'LOCAL'
        constraint.use_offset = True
        Add_Mute_Driver(p_bone.parent, armature, constraint, False)
    # return armature layers to how they were before...
    armature.data.layers = layers
    
# removes offset FK bones and returns constraints to original owners...      
def Remove_OffsetFK_IKvsFK_Limbs(armature):
    IK_owners = [data.Owner_name for data in armature.JK_MMT.IK_chain_data]
    # save current then show all target layers, we need the gizmo bone layer open to copy constraints...
    layers = armature.data.layers[:]
    armature.data.layers = [True]*32
    bpy.ops.pose.reveal(select=True)
    for bone in IK_owners:
        # deselect current selection and select the relevant bones...
        bpy.ops.pose.select_all(action='DESELECT')
        p_bone = armature.pose.bones[bone]
        p_bone.bone.select = True
        g_bone = armature.pose.bones["GB" + bone[2:]]
        g_bone.bone.select = True
        armature.data.bones.active = g_bone.bone
        # remove the copy rotation constraints...
        p_bone.constraints["Offset FK - Copy Rotation"].driver_remove('mute')
        p_bone.constraints.remove(p_bone.constraints["Offset FK - Copy Rotation"])
        p_bone.parent.constraints["Offset FK - Copy Rotation"].driver_remove('mute')
        p_bone.parent.constraints.remove(p_bone.parent.constraints["Offset FK - Copy Rotation"])
        # copy the IK constraint back to the original owner
        bpy.ops.pose.constraints_copy()
        # just incase the user has added constraints to the parent bone...
        if len(p_bone.parent.constraints) > 0:
            # deselect again...        
            bpy.ops.pose.select_all(action='DESELECT')
            # select the parents and copy their constraints back as well...
            p_bone.parent.bone.select = True
            g_bone.parent.bone.select = True
            bpy.context.active_object.data.bones.active = g_bone.parent.bone
            bpy.ops.pose.constraints_copy()
    # then enter edit mode and delete the added bones...
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in IK_owners:
        # remove parent first...            
        armature.data.edit_bones.remove(armature.data.edit_bones["GB" + bone[2:]].parent)
        armature.data.edit_bones.remove(armature.data.edit_bones["GB" + bone[2:]])
    bpy.ops.object.mode_set(mode='POSE')
    # return open armature layers
    armature.data.layers = layers
    
# adds IK switching that can be keyframed on and on off...
def Add_Switchable_IKvsFK_Limbs(armature):
    # go to edit mode for first iteration through IK chain data...
    bpy.ops.object.mode_set(mode='EDIT')  
    for data in armature.JK_MMT.IK_chain_data:
        # if the chain us using an offset IK chain target parent...
        if data.Target_name != data.Parent_name:
            # add a local target for it to follow when using FK...
            e_bone = armature.data.edit_bones.new("GB_local" + data.Parent_name[2:])
            e_bone.head = armature.data.edit_bones[data.Parent_name].head
            e_bone.tail = armature.data.edit_bones[data.Parent_name].tail
            e_bone.roll = armature.data.edit_bones[data.Parent_name].roll
            e_bone.parent = armature.data.edit_bones["PB" + data.Parent_name[2:]]
        # add pole bone local for upperarm/thigh...
        e_bone = armature.data.edit_bones.new("GB_local" + data.Pole_name[2:])
        e_bone.head = armature.data.edit_bones[data.Pole_name].head
        e_bone.tail = armature.data.edit_bones[data.Pole_name].tail
        e_bone.roll = armature.data.edit_bones[data.Pole_name].roll
        e_bone.parent = armature.data.edit_bones[data.Owner_name].parent
    # go to pose mode for second iteration through IK chain data...
    bpy.ops.object.mode_set(mode='POSE')
    for data in armature.JK_MMT.IK_chain_data:
        # if the chain us using an offset IK chain target parent...
        if data.Target_name != data.Parent_name:
            # set up the local target for its going to follow when using FK...
            ik_local_bone = armature.pose.bones["GB_local" + data.Parent_name[2:]]
            ik_local_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
            ik_local_bone.bone.layers = [False]*23+[True]+[False]*8
            ik_local_bone.bone.use_deform = False
        # set up local pole bone...
        pole_local_bone = armature.pose.bones["GB_local" + data.Pole_name[2:]]
        pole_local_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
        pole_local_bone.bone.layers = [False]*23+[True]+[False]*8
        pole_local_bone.bone.use_deform = False
        constraint = pole_local_bone.constraints.new("COPY_TRANSFORMS")
        constraint.name = "Use FK - Copy Transforms"
        constraint.target = armature
        constraint.subtarget = data.Pole_name
        # set up limit rotation on IK owner bone...
        owner_bone = armature.pose.bones[data.Owner_name]
        constraint = owner_bone.constraints.new("LIMIT_ROTATION")
        constraint.name = "Use FK - Limit Rotation"
        constraint.owner_space = 'LOCAL'
        Add_Mute_Driver(owner_bone, armature, constraint, False)
        # and it's parent...
        constraint = owner_bone.parent.constraints.new("LIMIT_ROTATION")
        constraint.name = "Use FK - Limit Rotation"
        constraint.owner_space = 'LOCAL'
        Add_Mute_Driver(owner_bone.parent, armature, constraint, False)
        # set the IK rotation overide to its default in order to fire its update function...
        data.Chain_ik_rotation_overide = False    
        
# removes switchable IK controls and drivers...        
def Remove_Switchable_IKvsFK_Limbs(armature):
    # iterate through chain data...
    for data in armature.JK_MMT.IK_chain_data:
        # return the switches to their defaults if required...
        if data.Chain_use_fk:
            data.Chain_use_fk = False
        if data.Chain_ik_rotation_overide:
            data.Chain_ik_rotation_overide = False
        # clean up the mute drivers and limit rotation constraints on the owner and its parent...
        owner = armature.pose.bones[data.Owner_name]
        owner.constraints["Use FK - Limit Rotation"].driver_remove("mute")
        owner.constraints.remove(owner.constraints["Use FK - Limit Rotation"])
        owner.parent.constraints["Use FK - Limit Rotation"].driver_remove("mute")
        owner.parent.constraints.remove(owner.parent.constraints["Use FK - Limit Rotation"])
    # jump to edit mode to remove all the local poles and targets...
    bpy.ops.object.mode_set(mode='EDIT')
    for data in armature.JK_MMT.IK_chain_data:
        # only try to remove local IK target if it exists...
        if "GB_local" + data.Target_name[2:] in armature.data.edit_bones:
            armature.data.edit_bones.remove(armature.data.edit_bones["GB_local" + data.Target_name[2:]])
        armature.data.edit_bones.remove(armature.data.edit_bones["GB_local" + data.Pole_name[2:]])
    bpy.ops.object.mode_set(mode='POSE')
        
# adds IK parenting that can be keyframed on and on off...
def Add_Switchable_Parenting(armature):
    # jump into edit mode so we can create some bones...    
    bpy.ops.object.mode_set(mode='EDIT')
    for data in armature.JK_MMT.IK_chain_data:
        # add/set local IK target...
        e_bone = armature.data.edit_bones.new(data.Parent_name[:2] + "_local" + data.Parent_name[2:])
        e_bone.head = armature.data.edit_bones[data.Parent_name].head
        e_bone.tail = armature.data.edit_bones[data.Parent_name].tail
        e_bone.roll = armature.data.edit_bones[data.Parent_name].roll
        e_bone.parent = armature.data.edit_bones[data.Root_name]
        # add/set local IK pole...
        e_bone = armature.data.edit_bones.new(data.Pole_name[:2] + "_local" + data.Pole_name[2:])
        e_bone.head = armature.data.edit_bones[data.Pole_name].head
        e_bone.tail = armature.data.edit_bones[data.Pole_name].tail
        e_bone.roll = armature.data.edit_bones[data.Pole_name].roll
        e_bone.parent = armature.data.edit_bones[data.Root_name]
    # back to pose mode to set everything else up
    bpy.ops.object.mode_set(mode='POSE')
    for i, data in enumerate(armature.JK_MMT.IK_chain_data):
        # set up the local IK target and IK target...
        ik_bone = armature.pose.bones[data.Parent_name]
        ik_local_bone = armature.pose.bones[data.Parent_name[:2] + "_local" + data.Parent_name[2:]]
        ik_local_bone.custom_shape = ik_bone.custom_shape
        ik_local_bone.custom_shape_scale = ik_bone.custom_shape_scale
        ik_local_bone.bone_group = ik_bone.bone_group
        ik_local_bone.bone.layers = ik_bone.bone.layers
        ik_local_bone.bone.use_deform = False
        # give it a copy transforms constraint...
        constraint = ik_local_bone.constraints.new("COPY_TRANSFORMS")
        constraint.name = "Use Parent - Copy Transforms"
        constraint.target = armature
        constraint.subtarget = ik_bone.name
        # and add the hide drivers...
        Add_Hide_Driver(i, armature, ik_local_bone.bone, "UseP", "UseFK", True)
        Add_Hide_Driver(i, armature, ik_bone.bone, "UseP", "UseFK", False)
        # set up the local IK pole and IK pole...
        pole_bone = armature.pose.bones[data.Pole_name]
        pole_local_bone = armature.pose.bones[data.Pole_name[:2] + "_local" + data.Pole_name[2:]]
        pole_local_bone.custom_shape = pole_bone.custom_shape
        pole_local_bone.custom_shape_scale = pole_bone.custom_shape_scale
        pole_local_bone.bone_group = pole_bone.bone_group
        pole_local_bone.bone.layers = pole_bone.bone.layers
        pole_local_bone.bone.use_deform = False
        # give it a copy transforms constraint...
        constraint = pole_local_bone.constraints.new("COPY_TRANSFORMS")
        constraint.name = "Use Parent - Copy Transforms"
        constraint.target = armature
        constraint.subtarget = pole_bone.name
        # and add the hide driver...
        Add_Hide_Driver(i, armature, pole_local_bone.bone, "UseP", "UseFK", True)
        Add_Hide_Driver(i, armature, pole_bone.bone, "UseP", "UseFK", False)
    
# removes alternative IK controls and gets rid of drivers... (needs further testing?)        
def Remove_Switchable_Parenting(armature):
    for data in armature.JK_MMT.IK_chain_data:
        # set parenting switch back to default...
        if data.Chain_use_parent:
            data.Chain_use_parent = False
        # clean up the hide driver and show the local ik target    
        target_local = armature.pose.bones[data.Parent_name[:2] + "_local" + data.Parent_name[2:]]
        target_local.bone.driver_remove('hide')
        target_local.bone.hide = False    
        # clean up the hide driver and show the local ik pole   
        pole_local = armature.pose.bones[data.Pole_name[:2] + "_local" + data.Pole_name[2:]]
        pole_local.bone.driver_remove('hide')
        pole_local.bone.hide = False
        # go into edit mode and remove the local bones...
        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones.remove(armature.data.edit_bones[target_local.name])
        armature.data.edit_bones.remove(armature.data.edit_bones[pole_local.name])
        # then back to pose mode to remove the hide drivers from the target and pole
        bpy.ops.object.mode_set(mode='POSE')        
        armature.pose.bones[data.Target_name].bone.driver_remove('hide')
        armature.pose.bones[data.Pole_name].bone.driver_remove('hide')
        
# adds head tracking bones and constraints...
def Add_Head_Tracking(armature):
    # deselect any selected pose bones...
    bpy.ops.pose.select_all(action='DESELECT')
    # loop through all the bones to track and select them...
    for bone in ["CB_head", "CB_neck_01", "CB_spine_03"]:
        p_bone = armature.pose.bones[bone]
        p_bone.bone.select = True
    # back to edit mode and duplicate them...
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.duplicate(do_flip_names=False)
    # rename them...
    for e_bone in bpy.context.selected_bones:
        e_bone.name = "GB" + e_bone.name[2:-4]
    # get a reference to the head bone...
    h_bone = armature.data.edit_bones["GB_head"]
    h_bone.use_inherit_scale = False
    # add and set the target bone...
    t_bone = armature.data.edit_bones.new("HT_head")
    t_bone.head = (h_bone.head[0], h_bone.head[1] - 0.25, h_bone.head[2])
    t_bone.tail = (t_bone.head[0], t_bone.head[1], t_bone.head[2] + 0.1)
    t_bone.parent = armature.data.edit_bones["CB_spine_02"]
    t_bone.roll = 0
    # add and set the stretch bone...
    s_bone = armature.data.edit_bones.new("HT_stretch")
    s_bone.head = h_bone.head
    s_bone.tail = t_bone.head
    s_bone.parent = armature.data.edit_bones["GB_neck_01"]
    s_bone.roll = 0
    # re-parent the head gizmo bone...
    h_bone.parent = s_bone
    # back to pose mode to set up constraints...
    bpy.ops.object.mode_set(mode='POSE')
    # set up the IK chain bones...
    p_bone = armature.pose.bones["HT_head"]
    p_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
    p_bone.custom_shape_scale = 1
    p_bone.bone_group = armature.pose.bone_groups["IK Targets"]
    p_bone.bone.layers = [False]*1+[True]+[False]*30
    p_bone = armature.pose.bones["HT_stretch"]
    p_bone.custom_shape = bpy.data.objects["B_Shape_Circle_Limbs"]
    p_bone.custom_shape_scale = 1
    p_bone.bone_group = armature.pose.bone_groups["IK Targets"]
    p_bone.bone.layers = [False]*1+[True]+[False]*30
    constraint = p_bone.constraints.new('IK')
    constraint.name = "Head Tracking - IK"
    constraint.target = armature
    constraint.subtarget = "HT_head"
    constraint.chain_count = 3
    p_bone.ik_stretch = 1    
    p_bone = armature.pose.bones["GB_head"]
    p_bone.custom_shape = None
    p_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
    p_bone.bone.layers = [False]*23+[True]+[False]*8
    p_bone.ik_stretch = 0.5
    p_bone.ik_stiffness_x = 0
    p_bone.ik_stiffness_y = 0
    p_bone.ik_stiffness_z = 0
    p_bone = armature.pose.bones["GB_neck_01"]
    p_bone.custom_shape = None
    p_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
    p_bone.bone.layers = [False]*23+[True]+[False]*8
    p_bone.ik_stretch = 0.5
    p_bone.ik_stiffness_x = 0
    p_bone.ik_stiffness_y = 0
    p_bone.ik_stiffness_z = 0
    p_bone = armature.pose.bones["GB_spine_03"]
    p_bone.custom_shape = None
    p_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
    p_bone.bone.layers = [False]*23+[True]+[False]*8
    p_bone.ik_stretch = 0.5
    p_bone.ik_stiffness_x = 0
    p_bone.ik_stiffness_y = 0
    p_bone.ik_stiffness_z = 0
    # set up the control bones...
    for bone in ["CB_head", "CB_neck_01", "CB_spine_03"]:
        p_bone = armature.pose.bones[bone]
        constraint = p_bone.constraints.new('IK')
        constraint.name = "Head Tracking - IK"
        constraint.target = armature
        constraint.chain_count = 1
        Add_Mute_Driver(p_bone, armature, constraint, False)
        # set the right target bone...
        if bone == "CB_spine_03":
            constraint.subtarget = "GB_neck_01"
        else:
            constraint.subtarget = "GB_head"
        # head just uses rotation based IK... (could be a damped track with a limit rotation but i prefer IK)
        if bone == "CB_head":
            constraint.use_location = False
            constraint.use_rotation = True            
        # neck and spine also have copy Y rotation constraints...
        else:
            constraint = p_bone.constraints.new('COPY_ROTATION')
            constraint.name = "Head Tracking - Copy Rotation"
            constraint.target = armature
            constraint.subtarget = "GB" + bone[2:]
            constraint.use_x = False
            constraint.use_z = False
            constraint.use_offset = True
            constraint.target_space = 'LOCAL'
            constraint.owner_space = 'LOCAL'
            Add_Mute_Driver(p_bone, armature, constraint, False)
        # turn on the IK limits for all three...    
        p_bone.use_ik_limit_x = True
        p_bone.use_ik_limit_y = True
        p_bone.use_ik_limit_z = True

# removes head tracking bones and constraints...    
def Remove_Head_Tracking(armature):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in ["HT_head", "HT_stretch", "GB_head", "GB_neck_01", "GB_spine_03"]:
        armature.data.edit_bones.remove(armature.data.edit_bones[bone])   
    bpy.ops.object.mode_set(mode='POSE')
    for bone in ["CB_head", "CB_neck_01", "CB_spine_03"]:
        p_bone = armature.pose.bones[bone]
        p_bone.constraints["Head Tracking - IK"].driver_remove('mute')
        p_bone.constraints.remove(p_bone.constraints["Head Tracking - IK"])
        if bone != "CB_head":
            p_bone.constraints["Head Tracking - Copy Rotation"].driver_remove('mute')
            p_bone.constraints.remove(p_bone.constraints["Head Tracking - Copy Rotation"])
        p_bone.use_ik_limit_x = False
        p_bone.use_ik_limit_y = False
        p_bone.use_ik_limit_z = False
        
# sets IK targets to be parented to the IK roots...
def Add_Parenting(armature):
    bpy.ops.object.mode_set(mode='EDIT')
    target_dict = {data.Parent_name : data.Root_name for data in armature.JK_MMT.IK_chain_data}
    for bone in target_dict:
        armature.data.edit_bones[bone].parent = armature.data.edit_bones[target_dict[bone]]
    bpy.ops.object.mode_set(mode='POSE')

# sets IK target parents to None...
def Remove_Parenting(armature):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in [armature.data.edit_bones[data.Parent_name] for data in armature.JK_MMT.IK_chain_data]:
        bone.parent = None
    bpy.ops.object.mode_set(mode='POSE')

#---------- EXECUTION -------------------------------------------------------------------------

# called by function to set head tracking...
def Set_Head_Tracking():
    armature = bpy.context.object
    MMT = armature.JK_MMT
    if MMT.Head_tracking == '0':        
        if MMT.Current_options[0] == 0:
            ShowMessage(message = "Already not using head tracking", title = "Option Info", icon = 'INFO')
            print("Already not using head tracking")
        else:
            Remove_Head_Tracking(armature)
    if MMT.Head_tracking == '1':        
        if MMT.Current_options[0] == 1:
            ShowMessage(message = "Already using head tracking", title = "Option Info", icon = 'INFO')
            print("Already using head tracking")
        else:
            Add_Head_Tracking(armature)

# called by function to set IK vs FK for digits... 
def Set_IKvsFK_Digits():
    armature = bpy.context.object
    MMT = armature.JK_MMT
    if MMT.IKvsFK_digits == '0':        
        if MMT.Current_options[3] == 0:
            ShowMessage(message = "Already using FK only for digits", title = "Option Info", icon = 'INFO')
            print("Already using FK only for digits")
        else:
            Remove_OffsetFK_IKvsFK_Digits(armature)
    if MMT.IKvsFK_digits == '1':        
        if MMT.Current_options[3] == 1:
            ShowMessage(message = "Already using offset digit IK vs FK", title = "Option Info", icon = 'INFO')
            print("Already using offset digit IK vs FK")
        else:
            Add_OffsetFK_IKvsFK_Digits(armature)
        
# called by function to set IK parenting... (unsets current parenting if needed)      
def Set_IK_Parenting():
    armature = bpy.context.object
    MMT = armature.JK_MMT
    if MMT.IK_parenting == '0':
        if MMT.Current_options[1] == 0:
            ShowMessage(message = "Already using Independent IK targets", title = "Option Info", icon = 'INFO')
            print("Already using Independent IK targets")
        else:
            if MMT.Current_options[1] == 1:
                Remove_Parenting(armature)
            elif MMT.Current_options[1] == 2: 
                Remove_Switchable_Parenting(armature)
    elif MMT.IK_parenting == '1':
        if MMT.Current_options[1] == 1:
            ShowMessage(message = "Already using Parented IK targets", title = "Option Info", icon = 'INFO')
            print("Already using Parented IK")
        else:
            if MMT.Current_options[1] == 2: 
                Remove_Switchable_Parenting(armature)
            Add_Parenting(armature)
    elif MMT.IK_parenting == '2':
        if MMT.Current_options[1] == 2:
            ShowMessage(message = "Already using Switchable IK Parents", title = "Option Info", icon = 'INFO')
            print("Already using Switchable IK Parents")
        else:
            if MMT.Current_options[1] == 1:
                Remove_Parenting(armature)
            Add_Switchable_Parenting(armature)

# called by function to set IK vs FK for limbs... (unsets current IK vs FK if needed)        
def Set_IKvsFK_Limbs():
    armature = bpy.context.object
    MMT = armature.JK_MMT
    if MMT.IKvsFK_limbs == '0':
        if MMT.Current_options[2] == 0:
            ShowMessage(message = "Already using only IK option", title = "Option Info", icon = 'INFO')
            print("Already using No IK vs FK options")
        else:
            if MMT.Current_options[2] == 1:
                Remove_OffsetFK_IKvsFK_Limbs(armature)            
            elif MMT.Current_options[2] == 2:
                Remove_Switchable_IKvsFK_Limbs(armature)
            Add_UseIK_IKvsFK_Limbs(armature)
    elif MMT.IKvsFK_limbs == '1': 
        if MMT.Current_options[2] == 1:
            ShowMessage(message = "Already using Offset FK option", title = "Option Info", icon = 'INFO')
            print("Already using Offset FK option")
        else:
            if MMT.Current_options[2] == 0:
                Remove_UseIK_IKvsFK_Limbs(armature)
            elif MMT.Current_options[2] == 2:
                Remove_Switchable_IKvsFK_Limbs(armature)
            Add_OffsetFK_IKvsFK_Limbs(armature)
    elif MMT.IKvsFK_limbs == '2':    
        if MMT.Current_options[2] == 2:
            ShowMessage(message = "Already using Switchable IK vs FK", title = "Option Info", icon = 'INFO')
            print("Already using Switchable IK vs FK")
        else:
            if MMT.Current_options[2] == 0:
                Remove_UseIK_IKvsFK_Limbs(armature)
            elif MMT.Current_options[2] == 1:
                Remove_OffsetFK_IKvsFK_Limbs(armature)        
            Add_Switchable_IKvsFK_Limbs(armature)

# functions here for testing...
#Set_Head_Tracking()
#Set_IKvsFK_Digits()
#Set_IK_Parenting()         
#Set_IKvsFK_Limbs()