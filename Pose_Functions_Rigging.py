import bpy
import math
import mathutils
from . import Base_Functions

# used to get a dictionary of bone matrices to their names...
def Get_Bone_Matrices(armature, names):
    matrices = {}
    for name in names:
        p_bone = armature.pose.bones[name]
        matrices[name] = p_bone.matrix
    return matrices

# used to set a dictionary of bone names to matrices...
def Set_Bone_Matrices(armature, matrices):
    for key, value in matrices.items():
        p_bone = armature.pose.bones[key]
        p_bone.matrix = value

# might come back to this at some point...
def Set_Rotation_Limits(p_bone, constraint, zero_overide):
    if zero_overide:
        constraint.influence = 1.0
        #constraint.use_limit_x, constraint.min_x, constraint.max_x = True, 0, 0
        #constraint.use_limit_y, constraint.min_y, constraint.max_y = True, 0, 0
        #constraint.use_limit_z, constraint.min_z, constraint.max_z = True, 0, 0
    else:
        constraint.influence = 0.0
        #constraint.use_limit_x, constraint.min_x, constraint.max_x = p_bone.use_ik_limit_x, p_bone.ik_min_x, p_bone.ik_max_x
        #constraint.use_limit_y, constraint.min_y, constraint.max_y = p_bone.use_ik_limit_y, p_bone.ik_min_y, p_bone.ik_max_y
        #constraint.use_limit_z, constraint.min_z, constraint.max_z = p_bone.use_ik_limit_z, p_bone.ik_min_z, p_bone.ik_max_z

# adds a pivot bone...
def Add_Pivot_Bone(rig, name, pivot_type, is_parent):
    # create any bones in edit mode...       
    bpy.ops.object.mode_set(mode='EDIT')
    # get the target edit bone...
    e_bone = rig.data.edit_bones[name]
    # create the pivot bone...
    pivot_bone = rig.data.edit_bones.new("PB" + name[2:])
    pivot_bone.head = e_bone.head
    pivot_bone.tail = e_bone.tail
    pivot_bone.roll = e_bone.roll
    pivot_bone.use_deform = False
    # if the pivot should share the targets parent...
    if pivot_type == 'PARENT_SHARE':
        pivot_bone.parent = e_bone.parent
    # or skip it...
    elif pivot_type == 'PARENT_SKIP':
        if e_bone.parent != None:
            pivot_bone.parent = e_bone.parent.parent
    # if the pivot bone is the parent of the target bone...
    if is_parent:   
        e_bone.parent = pivot_bone
    # set it to the layer the IK targets are on...
    pivot_bone.layers = [False]*1+[True]+[False]*30
    # go back to pose mode to set the bone group...
    bpy.ops.object.mode_set(mode='POSE')
    p_bone = rig.pose.bones["PB" + name[2:]]
    p_bone.bone_group = rig.pose.bone_groups["Pivot Bones"]
    # and return the pose bone...
    return p_bone
    
#---------- NOTES -----------------------------------------------------------------------------

# So this is a bunch of functions for IK options... so whether we are using IK roots for the targets and if they are always/never parented as well as head tracking...
# Both independant and parented IK can be useful so there is a switchable method with a property that can be keyframed...
# If using switchable IK parenting and IK vs FK together it seems to make more sense to force the parenting off while using the FK so my scripts don't have to manage two sets of IK targets...

#---------- FUNCTIONS -------------------------------------------------------------------------

# adds a driver variable using variable inputs...
def Add_Driver_Var(driver, armature, v_name, name):
    var = driver.driver.variables.new()
    var.name = v_name
    var.type = 'SINGLE_PROP'
    var.targets[0].id = armature
    if v_name == "UseP":
        var.targets[0].data_path = 'JK_MMT.IK_chain_data["' + name + '"].Chain_use_parent'
    elif v_name == "UseFK":
        var.targets[0].data_path = 'JK_MMT.IK_chain_data["' + name + '"].Chain_use_fk'
    elif v_name == "Master_Mute":
        var.targets[0].data_path = 'JK_MMT.Mute_default_constraints'

# adds a driver to hide a bone...
def Add_Hide_Driver(name, armature, b_bone, var_name_a, var_name_b, reverse):
    driver = b_bone.driver_add("hide")
    driver.driver.type = 'SCRIPTED'
    # add first variable...
    Add_Driver_Var(driver, armature, var_name_a, name)
    if var_name_b != None:
        Add_Driver_Var(driver, armature, var_name_b, name)
        condition = ("(not " + var_name_a + ") or " + var_name_b if reverse else var_name_a + " and (not " + var_name_b + ")")
    else:
        condition = ("not " + var_name_a if reverse else name)
    driver.driver.expression = condition
    # remove unwanted curve modifier...
    if len(driver.modifiers) > 0:
        driver.modifiers.remove(driver.modifiers[0])

def Set_IK_Drivers(armature, s_bone, t_bone):
    # all the IK settings...
    settings = ["ik_stretch", "lock_ik_x", "lock_ik_y", "lock_ik_z", 
        "ik_stiffness_x", "ik_stiffness_y", "ik_stiffness_z",
        "use_ik_limit_x", "ik_min_x", "ik_max_x",
        "use_ik_limit_y", "ik_min_y", "ik_max_y",
        "use_ik_limit_z", "ik_min_z", "ik_max_z"]
    # if we are adding the drivers there is a source bone...
    if s_bone != None:
        # iterate through and set the target setting to copy the source...
        for setting in settings:
            # add driver to setting...
            driver = t_bone.driver_add(setting)
            # add variable to driver...
            var = driver.driver.variables.new()
            var.name = setting
            var.type = 'SINGLE_PROP'
            var.targets[0].id = armature
            var.targets[0].data_path = 'pose.bones["' + s_bone.name + '"].' + setting
            # set the expression...
            driver.driver.expression = setting
            # remove unwanted curve modifier...
            if len(driver.modifiers) > 0:
                driver.modifiers.remove(driver.modifiers[0])
    # otherwise remove them...
    else:
        for setting in settings:
            t_bone.driver_remove(setting)

# adds offset FK vs IK to a digit...
def Set_IKvsFK_Offset_Digit(self):
    armature = bpy.context.object
    # show all layers...
    layers = armature.data.layers[:]
    armature.data.layers = [True]*32
    bpy.ops.pose.reveal(select=False)
    # enter edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    # create the gizmo bones..
    for name in [self.Proximal, self.Medial, self.Distal]:
        d_bone = armature.data.edit_bones[name]
        g_bone = armature.data.edit_bones.new("GB" + name[2:])
        g_bone.head = d_bone.head
        g_bone.tail = d_bone.tail
        g_bone.roll = d_bone.roll
        g_bone.parent = d_bone.parent if name == self.Proximal else armature.data.edit_bones["GB" + d_bone.parent.name[2:]]
        g_bone.use_deform = False
        # if it's the distal bone...
        if name == self.Distal:
            # create the floor target...
            f_bone = armature.data.edit_bones.new("FT" + self.Distal[2:])
            f_bone.head = (d_bone.head.x, d_bone.head.y, 0)
            f_bone.tail = (d_bone.head.x, d_bone.head.y, -0.05)
            f_bone.roll = 0
            #f_bone.parent = #e_bone.parent
            # and the IK target
            t_bone = armature.data.edit_bones.new("DT" + self.Distal[2:])
            t_bone.head = d_bone.head
            t_bone.tail = d_bone.tail
            t_bone.roll = d_bone.roll
            t_bone.parent = armature.data.edit_bones[self.name]
            t_bone.use_deform = False
            t_bone.use_inherit_scale = False
            # deselect any selected bones...
            bpy.ops.armature.select_all(action='DESELECT')
            t_bone.select_head = True
            t_bone.select_tail = True
            # move the target to the tail of the distal bone...
            bpy.ops.transform.translate(value=(0, Base_Functions.Get_Distance(d_bone.head, d_bone.tail), 0), orient_type='NORMAL', constraint_axis=(False, True, False))        
    # then into pose mode to set everything up...
    bpy.ops.object.mode_set(mode='POSE')
    for name in [self.Proximal, self.Medial, self.Distal]:
        # control bone copys the rotation of the gizmo bone...
        d_bone = armature.pose.bones[name]
        copy_rot = d_bone.constraints["Digit - Copy Rotation"]
        copy_rot.subtarget = "GB" + name[2:]
        copy_rot.use_x = True
        copy_rot.use_y = True
        copy_rot.use_z = True
        # assign gizmo bones bone group and layer
        g_bone = armature.pose.bones["GB" + name[2:]]
        g_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
        g_bone.bone.layers = [False]*23+[True]+[False]*8
        # if it's the distal bone...
        if name == self.Distal:
            # gizmo bone gets the IK constraint...
            ik = g_bone.constraints.new("IK")
            ik.show_expanded = False
            ik.target = armature
            ik.subtarget = "DT" + name[2:]
            ik.chain_count = 3
            # set the floor targets pose data...
            f_bone = armature.pose.bones["FT" + name[2:]]
            f_bone.custom_shape = bpy.data.objects["B_Shape_Circle"]
            f_bone.custom_shape_scale = 0.25
            f_bone.bone_group = armature.pose.bone_groups["Floor Targets"]
            f_bone.bone.layers = [False]*1+[True]+[False]*30
            # set the target bones pose data...
            t_bone = armature.pose.bones["DT" + name[2:]]
            t_bone.custom_shape = bpy.data.objects["B_Shape_Sphere"]
            t_bone.custom_shape_scale = 0.25
            t_bone.bone_group = armature.pose.bone_groups["IK Targets"]
            t_bone.bone.layers = [False]*1+[True]+[False]*30
            # and give it a floor constraint...
            floor = t_bone.constraints.new("FLOOR")
            floor.name = "Finger IK - Floor"
            floor.show_expanded = False
            floor.target = armature
            floor.subtarget = "FT" + name[2:]
            floor.use_rotation = True
            floor.floor_location = 'FLOOR_NEGATIVE_Y'
    # return the armatures layers once finished...
    armature.data.layers = layers
  
# returns digit control method to default...
def Set_IKvsFK_None_Digit(self):
    armature = bpy.context.object
    axes = [True, False] if 'X' in self.Main_axis else [False, True]
    # set the control bones copy rotation back...
    for name in [self.Proximal, self.Medial, self.Distal]:
        d_bone = armature.pose.bones[name]
        copy_rot = d_bone.constraints["Digit - Copy Rotation"]
        copy_rot.subtarget = self.name
        if name != self.Proximal:
            copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = axes[0], False, axes[1]
    # then go into edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    # to delete the gizmo bones...
    for name in [self.Proximal, self.Medial, self.Distal]:
        armature.data.edit_bones.remove(armature.data.edit_bones["GB" + name[2:]])
        # and if its the distal name get rid of the floor and ik targets...
        if name == self.Distal:
            armature.data.edit_bones.remove(armature.data.edit_bones["DT" + name[2:]])
            armature.data.edit_bones.remove(armature.data.edit_bones["FT" + name[2:]])
    # then back to pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    
# adds IK switching that can be keyframed on and on off...
def Set_IKvsFK_Switchable(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    end_data = self.End_data
    # go to edit mode to create local targets...
    bpy.ops.object.mode_set(mode='EDIT')
    # declare the edit bones...
    control = armature.data.edit_bones[chain_data.Control]
    end = armature.data.edit_bones["PB" + end_data.name[2:] if chain_data.Has_pivots else end_data.name]
    pole = armature.data.edit_bones[chain_data.Pole]
    second = armature.data.edit_bones[chain_data.name]
    for e_bone in [control, pole]:  
        # add a local target for the control to follow when using FK...
        local = armature.data.edit_bones.new(chain_data.Control_local if e_bone == control else chain_data.Pole_local)
        local.head, local.tail, local.roll = e_bone.head, e_bone.tail, e_bone.roll
        local.parent, local.use_deform, local.layers = end if e_bone == control else second, False, [False]*23+[True]+[False]*8
    # go to pose mode to set up bone groups, layers and constraints etc...
    bpy.ops.object.mode_set(mode='POSE')
    control = armature.pose.bones[chain_data.Control_local]
    pole = armature.pose.bones[chain_data.Pole_local]
    for p_bone in [control, pole]:
        p_bone.bone_group = armature.pose.bone_groups["Gizmo Bones"]
        if p_bone == control:
            copy_trans = p_bone.constraints.new("COPY_TRANSFORMS")
            copy_trans.name = "Use FK - Copy Transforms"
            copy_trans.show_expanded = False
            copy_trans.target, copy_trans.subtarget = armature, chain_data.Control
        
# returns limb IK back to default...        
def Set_IKvsFK_None(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    end_data = self.End_data
    # if switchable IK vs FK...
    if self.Last_IKvsFK == 'SWITCHABLE':
        # return the switch to its default...
        if self.Chain_use_fk:
            self.Chain_use_fk = False
        # jump to edit mode to remove the local bones...
        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones.remove(armature.data.edit_bones[chain_data.Control_local])
        armature.data.edit_bones.remove(armature.data.edit_bones[chain_data.Pole_local])
        bpy.ops.object.mode_set(mode='POSE')

# Returns IK parenting to default setting...
def Set_Parenting_None(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    # if targets were rooted un-root them...
    if self.Last_parenting == "ROOTED":
        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones[chain_data.Control].parent = None
        armature.data.edit_bones[chain_data.Pole].parent = None
        bpy.ops.object.mode_set(mode='POSE')    
    # if they were siwtchable remove alternative targets and get rid of drivers...       
    elif self.Last_parenting == "SWITCHABLE":
        # set parenting switch back to default...
        if self.Chain_use_parent:
            self.Chain_use_parent = False
        control = armature.pose.bones[chain_data.Target]
        pole = armature.pose.bones[chain_data.Pole]
        for p_bone in [control, pole]:
            # remove hide drivers from originals...
            p_bone.bone.driver_remove('hide')
            # clean up the hide driver and show the parented version...    
            local = armature.pose.bones[chain_data.Control_root if p_bone == control else chain_data.Pole_root]
            local.bone.driver_remove('hide')
            local.bone.hide = False
            # go in and out of edit mode to remove the local bone...
            bpy.ops.object.mode_set(mode='EDIT')
            armature.data.edit_bones.remove(armature.data.edit_bones[chain_data.Control_root if p_bone == control else chain_data.Pole_root])
            bpy.ops.object.mode_set(mode='POSE')
             
# sets IK parenting that can be keyframed on and on off...
def Set_Parenting_Switchable(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    end_data = self.End_data
    # jump into edit mode so we can create some bones...    
    bpy.ops.object.mode_set(mode='EDIT')
    Control = armature.data.edit_bones[chain_data.Control]
    Pole = armature.data.edit_bones[chain_data.Pole]
    Root = armature.data.edit_bones[chain_data.Root]
    for e_bone in [Control, Pole]:
        local = armature.data.edit_bones.new(chain_data.Control_root if e_bone == Control else chain_data.Pole_root)
        local.head, local.tail, local.roll, local.parent = e_bone.head, e_bone.tail, e_bone.roll, Root
        local.layers, local.use_deform = e_bone.layers, False
    # back to pose mode to set everything else up
    bpy.ops.object.mode_set(mode='POSE')
    # set up the local IK target and IK pole...
    control = armature.pose.bones[chain_data.Control]
    pole = armature.pose.bones[chain_data.Pole]
    for p_bone in [control, pole]:
        local = armature.pose.bones[chain_data.Control_root if p_bone == control else chain_data.Pole_root]
        #local = armature.pose.bones[chain_data.Control_root]
        local.custom_shape, local.custom_shape_scale, local.bone_group = p_bone.custom_shape, p_bone.custom_shape_scale, p_bone.bone_group
        # give it a copy transforms constraint...
        copy_trans = local.constraints.new("COPY_TRANSFORMS")
        copy_trans.name = "Use Parent - Copy Transforms"
        copy_trans.target, copy_trans.show_expanded = armature, False
        copy_trans.subtarget = chain_data.Control if p_bone == control else chain_data.Pole
        # and add the hide drivers...
        Add_Hide_Driver(self.name, armature, local.bone, "UseP", "UseFK", True)
        Add_Hide_Driver(self.name, armature, p_bone.bone, "UseP", "UseFK", False)

# sets IK targets to be parented to the IK root...
def Set_Parenting_Rooted(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    bpy.ops.object.mode_set(mode='EDIT')
    armature.data.edit_bones[chain_data.Control].parent = armature.data.edit_bones[chain_data.Root]
    armature.data.edit_bones[chain_data.Pole].parent = armature.data.edit_bones[chain_data.Root]
    bpy.ops.object.mode_set(mode='POSE')


#---------- Switchable Parenting and IK Updates -------------------------------------------------------------------------

def Set_None_To_Rooted(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    # declare the bones we need to do stuff too...
    control = armature.pose.bones[chain_data.Control]
    control_root = armature.pose.bones[chain_data.Control_root]
    pole = armature.pose.bones[chain_data.Pole]
    pole_root = armature.pose.bones[chain_data.Pole_root]
    # get the matrices before removing constraints...         
    control_matrix = control_root.matrix
    pole_matrix = pole_root.matrix
    # remove the copy transform constraints...
    control_root.constraints.remove(control_root.constraints["Use Parent - Copy Transforms"])                
    pole_root.constraints.remove(pole_root.constraints["Use Parent - Copy Transforms"])
    # set the matrices back to how they were before constraints got removed...
    control_root.matrix = control_matrix
    pole_root.matrix = pole_matrix
    # iterate over control and pole bones...
    for p_bone in [control, pole]:
        # the original bone copies the transforms of its parented version...
        constraint = p_bone.constraints.new("COPY_TRANSFORMS")
        constraint.name = "Use Parent - Copy Transforms"
        constraint.target, constraint.show_expanded = armature, False
        constraint.subtarget = chain_data.Control_root if p_bone == control else chain_data.Pole_root
        # if we had the not parented bone selected...
        if p_bone in bpy.context.selected_pose_bones:
            # if it was the active pose bone...
            if bpy.context.active_object.data.bones.active == p_bone.bone:
                # set the parented bone to be the new active...
                bpy.context.active_object.data.bones.active = control_root.bone if p_bone == control else pole_root.bone
            # deselect not parented bone and select the parented bone...
            p_bone.bone.select = False
            if p_bone == control:
                control_root.bone.select = True
            else:    
                pole_root.bone.select = True

def Set_Rooted_To_None(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    # declare the bones we need to do stuff too...
    control = armature.pose.bones[chain_data.Control]
    control_root = armature.pose.bones[chain_data.Control_root]
    pole = armature.pose.bones[chain_data.Pole]
    pole_root = armature.pose.bones[chain_data.Pole_root]
    # get the matrices before removing constraints...
    control_matrix = control.matrix
    pole_matrix = pole.matrix
    # remove the copy transform constraints...             
    control.constraints.remove(control.constraints["Use Parent - Copy Transforms"])              
    pole.constraints.remove(pole.constraints["Use Parent - Copy Transforms"])
    # set the matrices back to how they were before constraints got removed...
    control.matrix = control_matrix
    pole.matrix = pole_matrix
    # iterate over control and pole bones...
    for p_bone in [control_root, pole_root]:
        # the parented bone copies the transforms of its original version...
        constraint = p_bone.constraints.new("COPY_TRANSFORMS")
        constraint.name = "Use Parent - Copy Transforms"
        constraint.target, constraint.show_expanded = armature, False
        constraint.subtarget = chain_data.Control if p_bone == control_root else chain_data.Pole
        # if we had the parented bone selected...
        if p_bone in bpy.context.selected_pose_bones:
            # if it was the active pose bone...
            if bpy.context.active_object.data.bones.active == p_bone.bone:
                # set the not parented bone to be the new active...
                bpy.context.active_object.data.bones.active = control.bone if p_bone == control_root else pole.bone
            # deselect parented bone and select the not parented bone...
            p_bone.bone.select = False
            if p_bone == control_root:
                control.bone.select = True
            else:    
                pole.bone.select = True

def Set_IK_To_FK(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    end_data = self.End_data
    # declare the bones we need...
    target = armature.pose.bones[chain_data.Target]
    first = armature.pose.bones[self.name]
    first_gizmo = armature.pose.bones["GB" + self.name[2:]]
    first_stretch = armature.pose.bones["GB_STRETCH" + self.name[2:]]
    second = armature.pose.bones[chain_data.name]
    end = armature.pose.bones["PB" + end_data.name[2:] if chain_data.Has_pivots else end_data.name]
    control = armature.pose.bones[chain_data.Control]
    control_local = armature.pose.bones[chain_data.Control_local]
    pole = armature.pose.bones[chain_data.Pole]
    #pole_local = armature.pose.bones[chain_data.Pole_local]
    # get the matrices before removing constraints...
    end_matrix = end.matrix
    first_matrix = first.matrix
    second_matrix = second.matrix
    # if it's a leg chain...
    if self.Chain_type == 'LEG':
        # get any difference between the control and the target...
        distance = target.tail - control_local.head   
    # remove control constraints...
    end.constraints.remove(end.constraints["Copy Rotation"])
    first.constraints.remove(first.constraints["Copy Rotation"])
    second.constraints.remove(second.constraints["Copy Rotation"])
    control_local.constraints.remove(control_local.constraints["Use FK - Copy Transforms"])
    # set the matrices back to how they were before constraints got removed...  
    end.matrix = end_matrix
    first.matrix = first_matrix
    second.matrix = second_matrix
    # if it's a leg chain...
    if self.Chain_type == 'LEG':
        # apply any difference between the control and the target...
        control_local.matrix.translation = end.tail - distance
    # tell the IK gizmo and stretch bones to copy rotation of the first bone...
    for p_bone in [first_gizmo, first_stretch]:
        copy_rot = p_bone.constraints.new("COPY_ROTATION")
        copy_rot.name = "Use FK - Copy Rotation"
        copy_rot.show_expanded = False
        copy_rot.target, copy_rot.subtarget = armature, first.name
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
    # tell the control and pole to copy the local control and local pole...
    for p_bone in [control, pole]:
        copy_trans = p_bone.constraints.new("COPY_TRANSFORMS")
        copy_trans.name = "Use FK - Copy Transforms"
        copy_trans.target, copy_trans.show_expanded = armature, False
        copy_trans.subtarget = chain_data.Control_local if p_bone == control else chain_data.Pole_local
    
def Set_FK_To_IK(self):
    armature = bpy.context.object
    chain_data = self.Chain_data
    end_data = self.End_data
    # declare the bones we need...
    first = armature.pose.bones[self.name]
    first_gizmo = armature.pose.bones["GB" + self.name[2:]]
    first_stretch = armature.pose.bones["GB_STRETCH" + self.name[2:]]
    second = armature.pose.bones[chain_data.name]
    end = armature.pose.bones["PB" + end_data.name[2:] if chain_data.Has_pivots else end_data.name]
    control = armature.pose.bones[chain_data.Control]
    control_local = armature.pose.bones[chain_data.Control_local]
    pole = armature.pose.bones[chain_data.Pole]
    #pole_local = armature.pose.bones[chain_data.Pole_local]
    # get the matrices before removing constraints...
    control_matrix = control.matrix
    pole_matrix = pole.matrix
    # remove IKvsFK constraints...
    control.constraints.remove(control.constraints["Use FK - Copy Transforms"])                       
    pole.constraints.remove(pole.constraints["Use FK - Copy Transforms"])
    first_gizmo.constraints.remove(first_gizmo.constraints["Use FK - Copy Rotation"])
    first_gizmo.rotation_quaternion = first.rotation_quaternion
    first_stretch.constraints.remove(first_stretch.constraints["Use FK - Copy Rotation"])
    first_stretch.rotation_quaternion = first.rotation_quaternion
    # set the matrices back to how they were before constraints got removed...  
    control.matrix = control_matrix
    pole.matrix = pole_matrix
    # give back the copy rotations...
    for p_bone in [first, second, end]:
        copy_rot = p_bone.constraints.new("COPY_ROTATION")
        copy_rot.target, copy_rot.show_expanded = armature, False
        copy_rot.subtarget = "GB" + p_bone.name[2:] if p_bone != end else chain_data.Target
        copy_rot.target_space, copy_rot.owner_space = 'LOCAL' if p_bone != end else 'WORLD', 'LOCAL' if p_bone != end else 'WORLD'
    # give the local control back it's copy transform...
    copy_trans = control_local.constraints.new("COPY_TRANSFORMS")
    copy_trans.name = "Use FK - Copy Transforms"
    copy_trans.show_expanded = False
    copy_trans.target, copy_trans.subtarget = armature, chain_data.Control
    

                                