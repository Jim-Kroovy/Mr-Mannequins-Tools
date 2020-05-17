import bpy
import sys
import os
import math
import mathutils
import time

from mathutils import Matrix, Vector

# one little message box function... (just in case)
def Show_Message(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# gets all .FBXs in the given folder location...
def Get_Imports_FBX(self, context, i_path):
    items = []
    if os.path.exists(bpy.path.abspath(i_path)):
        for filename in os.listdir(bpy.path.abspath(i_path)):
            if filename.upper().endswith(".FBX"):
                items.append((os.path.join(i_path, filename), filename[:-4], os.path.join(i_path, filename)))
    return items   

# get distance between start and end...
def Get_Distance(start, end):
    x = end[0] - start[0]
    y = end[1] - start[1]
    z = end[2] - start[2]
    distance = math.sqrt((x)**2 + (y)**2 + (z)**2)
    return distance

# returns what should be the right rotational direction...
def Get_Rot_Direction_Shortest(bone, axis, c_int, t_loc):
    # we need references to the head tail and roll...
    start_head = bone.head[:]
    start_tail = bone.tail[:]
    start_roll = bone.roll
    # rotate positively and get result...
    bpy.ops.transform.rotate(value=0.001, orient_axis=axis[0], orient_type='NORMAL')
    positive = abs(t_loc - bone.tail[c_int])
    # reset bone...
    bone.head = start_head
    bone.tail = start_tail 
    bone.roll = start_roll
    # rotate negatively and get result...
    bpy.ops.transform.rotate(value=-0.001, orient_axis=axis[0], orient_type='NORMAL')
    negative = abs(t_loc - bone.tail[c_int])
    # reset bone...
    bone.head = start_head
    bone.tail = start_tail
    bone.roll = start_roll
    #print(t_loc - positive, t_loc - negative)
    return axis + ('_NEGATIVE' if t_loc - positive > t_loc - negative else '')

# incrementally adjusts an edit bone around a normal axis to reach the target location channel...
def Set_Bone_Rotation_By_Step(bone, axis, c_int, t_loc):
    # declare some variables...
    increment = 0.01
    step = False
    direction = Get_Rot_Direction_Shortest(bone, axis[0], c_int, t_loc)
    last = bone.tail[c_int]
    # going to put a limit on how long this can run...
    time_start = time.time()
    # while loop on increment size...
    while increment > 0.00000001:
        # switch bool on positive vs negative step over...
        if (bone.tail[c_int] > t_loc and last < t_loc) or (bone.tail[c_int] < t_loc and last > t_loc):
            direction = axis[0] + ('' if 'NEGATIVE' in direction else '_NEGATIVE')
            #direction = Get_Rot_Direction_Shortest(bone, axis, c_int, t_loc)  
            step = True
        # on step over make increment smaller...    
        if step == True:
            increment = (increment * 0.1)
            step = False
        last = bone.tail[c_int]
        # value gets negated depending on direction and step...
        val = (increment * 1) if 'NEGATIVE' in direction else (increment * -1)
        print(val)
        bpy.ops.transform.rotate(value=val, orient_axis=direction[0], orient_type='NORMAL')
        # safety precaution...
        if increment < 0.0000001 or time.time() >= (time_start + 10):
            break
    bone.select = True
    bpy.ops.armature.calculate_roll(type='ACTIVE')

# should get the normal direction a bone must travel to reach the target...        
def Get_Loc_Direction_Shortest(bone, axis, c_int, t_loc):
    # set up a couple of variables...
    axes = (True, False, False) if 'X' in axis else (False, True, False) if 'Y' in axis else (False, False, True)
    val = -0.0001
    # we need references to the head tail and roll...
    start_head = bone.head[:]
    start_tail = bone.tail[:]
    start_roll = bone.roll
    # translate positively and get result...
    vector = (abs(val), 0.0, 0.0) if 'X' in axis else (0.0, abs(val), 0.0) if 'Y' in axis else (0.0, 0.0, abs(val))
    bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=axes)
    positive = abs(t_loc - bone.tail[c_int])
    # reset bone...
    bone.head = start_head
    bone.tail = start_tail 
    bone.roll = start_roll
    # translate negatively and get result...
    vector = (val, 0.0, 0.0) if 'X' in axis else (0.0, val, 0.0) if 'Y' in axis else (0.0, 0.0, val)
    bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=axes)
    negative = abs(t_loc - bone.tail[c_int])
    # reset bone...
    bone.head = start_head
    bone.tail = start_tail
    bone.roll = start_roll
    #print(t_loc - positive, t_loc - negative)
    return axis + ('_NEGATIVE' if t_loc - positive < t_loc - negative else '')
            
# incrementally adjusts an edit bones tail on a normal axis to reach the target location channel...
def Set_Bone_Location_By_Step(bone, axis, c_int, t_loc):
    # declare some variables...
    roll = bone.roll
    axes = (True, False, False) if 'X' in axis else (False, True, False) if 'Y' in axis else (False, False, True) 
    increment = 0.01
    step = False
    last = bone.tail[c_int]
    direction = axis
    # if we are moving on the Y...
    if 'Y' in axis:
        # and we are going to pass negatively through the head of the bone...
        if (bone.tail[c_int] > bone.head[c_int] and t_loc < bone.head[c_int]) or (bone.tail[c_int] < bone.head[c_int] and t_loc > bone.head[c_int]):
            # just reverse the bone... 
            bpy.ops.transform.translate(value=(0.0, (bone.length * 2) * -1, 0.0), orient_type='NORMAL', constraint_axis=axes)
            # set it's roll inverse of what it was to begin with..
            bone.roll = roll * -1
            # and set the new shortest direction and last location...
            direction = Get_Loc_Direction_Shortest(bone, axis[0], c_int, t_loc)
            last = bone.tail[c_int]
    # going to put a limit on how long this can run...
    time_start = time.time()
    # while loop on increment size...
    while increment > 0.0000001:
        # switch bool on positive vs negative step over..
        if (bone.tail[c_int] > t_loc and last < t_loc) or (bone.tail[c_int] < t_loc and last > t_loc):
            direction = axis[0] + ('' if 'NEGATIVE' in direction else '_NEGATIVE')
            step = True
        # on step over make increment smaller...    
        if step == True:
            increment = (increment * 0.1)
            step = False
        last = bone.tail[c_int]
        # value gets negated depending on direction and step...
        val = (increment * -1) if 'NEGATIVE' in direction else (increment * 1)
        # set value to correct vector axis we are translating on...
        vector = (val, 0.0, 0.0) if 'X' in axis else (0.0, val, 0.0) if 'Y' in axis else (0.0, 0.0, val)
        bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=axes)
        # safety precaution...
        if increment < 0.000001 or time.time() >= (time_start + 10):
            break

# gets the local matrix of a pose bone after constraints and drivers have been applied...
def Get_Local_Bone_Matrix(p_bone):
    matrix = p_bone.matrix
    rest = p_bone.bone.matrix_local.copy()
    rest_inv = rest.inverted()
    if p_bone.parent:
        parent_matrix = p_bone.parent.matrix.copy()
        parent_inv = parent_matrix.inverted()
        parent_rest = p_bone.parent.bone.matrix_local.copy()
    else:
        parent_matrix = Matrix()
        parent_inv = Matrix()
        parent_rest = Matrix()
    
    local_matrix = rest_inv @ (parent_rest @ (parent_inv @ matrix))

    # Compensate for non-local location - causes errors might try to fix in the future?
    #if not pose_bone.bone.use_local_location:
        #location = local_matrix.to_translation() * (parent_rest.inverted() @ rest).to_quaternion()
        #local_matrix.translation = location
    return local_matrix 

def Get_Fcurve_Channel(fcurve):
    name = None
    if fcurve.data_path.endswith('.location'):
        name = 'location'
        #name = "location_" + str(fcurve.array_index)
    elif fcurve.data_path.endswith('.rotation_quaternion'):
        name = 'quaternion'
        #name = "rotation_quaternion_" + str(fcurve.array_index)
    elif fcurve.data_path.endswith('.rotation_euler'):
        name = 'euler'
        #name = "rotation_euler_" + str(fcurve.array_index)
    elif fcurve.data_path.endswith('.scale'):
        name = 'scale'
        #name = "scale_" + str(fcurve.array_index)
    return name #, fcurve.array_index]

def Get_Scaled_Loc_Matrix(target, source, s_scale):
    # create a location matrix
    loc = source.matrix.to_translation()
    loc_scaled = (loc[0] * s_scale.scale[0], loc[1] * s_scale.scale[1], loc[2] * s_scale.scale[2])
    mat_loc = mathutils.Matrix.Translation(loc_scaled)
    # create an identitiy matrix
    mat_sca = mathutils.Matrix.Scale(1, 4, target.matrix.to_scale())
    # create a rotation matrix
    mat_rot = source.matrix.to_quaternion().to_matrix().to_4x4() #t_bone.matrix.to_quaternion().to_matrix().to_4x4()# mathutils.Matrix.Rotation(math.radians(45.0), 4, 'X')#
    # combine transformations
    mat_out = mat_loc @ mat_rot @ mat_sca
    return mat_out

# symetrizes bone rolls for control bones... (requires edit mode)
def Set_Symmetrical_Control_Rolls(armature, to_right):
    # declare the four suffix strings...
    suffices = ["_L", ".L", "_R", ".R"]
    # set the source suffices from bool...
    source_a = suffices[0] if to_right else suffices[2]
    source_b = suffices[1] if to_right else suffices[3]
    # set the target suffices from bool...
    target_a = suffices[2] if to_right else suffices[0]
    target_b = suffices[3] if to_right else suffices[1]
    # get all the control bones and iterate through them...
    control_bones = {e_bone.name.upper() : e_bone for e_bone in armature.data.edit_bones if e_bone.name.startswith("CB_")}
    for name, bone in control_bones.items():
        # if the uppercase name ends with source underscore suffix...
        if name.endswith(source_a):
            # and an uppercase name exists with the target underscore suffix...
            if name[:-2] + target_a in control_bones:
                # set the targets bone roll to the reverse of the sources...
                t_bone = control_bones[name[:-2] + target_a]
                t_bone.roll = bone.roll * -1 
        # if the uppercase name ends with source underscore suffix...
        elif name.endswith(source_b):
            # and an uppercase name exists with the target underscore suffix...
            if name[:-2] + target_b in control_bones:
                # set the targets bone roll to the reverse of the sources...
                t_bone = control_bones[name[:-2] + target_b]
                t_bone.roll = bone.roll * -1  

def Get_Custom_Shapes(path, unit_scale):
    # load the shape .blend...    
    with bpy.data.libraries.load(path, link=False, relative=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name not in bpy.data.objects]
    # set fake user true so they don't get removed on save/load...
    for obj in data_to.objects:
        obj.use_fake_user = True

def Get_Root_Bones(armature):
    return [bone for bone in armature.pose.bones if bone.parent == None]

def Export_FBX(path, MMT, export_anim):
    bpy.ops.export_scene.fbx(filepath=path, 
        check_existing=True, 
        filter_glob="*.fbx", 
        use_selection=True, 
        use_active_collection=False, 
        global_scale=1.0, 
        apply_unit_scale=False, 
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False, 
        object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'}, 
        use_mesh_modifiers=MMT.Apply_modifiers, 
        use_mesh_modifiers_render=True, 
        mesh_smooth_type='FACE',
        use_subsurf=False,  
        use_mesh_edges=False, 
        use_tspace=False, 
        use_custom_props=False, 
        add_leaf_bones=MMT.Add_leaf_bones, 
        primary_bone_axis=MMT.Primary_bone_axis, 
        secondary_bone_axis=MMT.Secondary_bone_axis, 
        use_armature_deform_only=True, 
        armature_nodetype='NULL', 
        bake_anim=export_anim, 
        bake_anim_use_all_bones=True, 
        bake_anim_use_nla_strips=False, 
        bake_anim_use_all_actions=False, 
        bake_anim_force_startend_keying=MMT.Startend_keys, 
        bake_anim_step=MMT.Anim_step, 
        bake_anim_simplify_factor=MMT.Simplify_factor, 
        path_mode='AUTO', 
        embed_textures=False, 
        batch_mode='OFF', 
        use_batch_own_dir=True, 
        use_metadata=True, 
        axis_forward=MMT.Axis_forward, 
        axis_up=MMT.Axis_up)

def Export_FBX_Anim_Most_Host(path, MMT):
    bpy.ops.ue4fbx.exportfbx(filepath=path, 
        check_existing=True, 
        filter_glob="*.fbx", 
        use_selection=True, 
        use_active_collection=False, 
        global_scale=1.0, 
        apply_unit_scale=True, 
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False, 
        object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'}, 
        use_mesh_modifiers=MMT.Apply_modifiers, 
        use_mesh_modifiers_render=True, 
        mesh_smooth_type='FACE',
        #use_subsurf=False,  
        use_mesh_edges=False, 
        use_tspace=False, 
        use_custom_props=False, 
        add_leaf_bones=MMT.Add_leaf_bones, 
        primary_bone_axis=MMT.Primary_bone_axis, 
        secondary_bone_axis=MMT.Secondary_bone_axis, 
        use_armature_deform_only=True, 
        armature_nodetype='NULL', 
        bake_anim=True, 
        bake_anim_use_all_bones=True, 
        bake_anim_use_nla_strips=False, 
        bake_anim_use_all_actions=False, 
        bake_anim_force_startend_keying=MMT.Startend_keys, 
        bake_anim_step=MMT.Anim_step, 
        bake_anim_simplify_factor=MMT.Simplify_factor, 
        path_mode='AUTO', 
        embed_textures=False, 
        batch_mode='OFF', 
        use_batch_own_dir=True, 
        use_metadata=True, 
        axis_forward=MMT.Axis_forward, 
        axis_up=MMT.Axis_up)

def Import_FBX(path, MMT, use_anim):
    bpy.ops.import_scene.fbx(filepath=path,
        directory="", 
        filter_glob="*.fbx", 
        #files=None, 
        ui_tab='MAIN', 
        use_manual_orientation=MMT.Manual_orient, 
        global_scale=1.0, 
        bake_space_transform=False, 
        use_custom_normals=True, 
        use_image_search=True, 
        use_alpha_decals=False, 
        decal_offset=0.0, 
        use_anim=use_anim, 
        anim_offset=MMT.Frame_offset, 
        use_subsurf=False, 
        use_custom_props=MMT.User_props, 
        use_custom_props_enum_as_string=True, 
        ignore_leaf_bones=MMT.Leaf_bones, 
        force_connect_children=False, 
        automatic_bone_orientation=False, 
        primary_bone_axis=MMT.Primary_bone_axis, 
        secondary_bone_axis=MMT.Secondary_bone_axis, 
        use_prepost_rot=True, 
        axis_forward=MMT.Axis_forward, 
        axis_up=MMT.Axis_up)   

def Import_FBX_Anim_Most_Host(path, MMT):
    bpy.ops.ue4fbx.importfbx(filepath=path,
        directory="", 
        filter_glob="*.fbx", 
        #files=None, 
        ui_tab='MAIN', 
        use_manual_orientation=False, 
        global_scale=1.0, 
        bake_space_transform=False, 
        use_custom_normals=True, 
        use_image_search=True, 
        use_alpha_decals=False, 
        decal_offset=0.0, 
        use_anim=True, 
        anim_offset=MMT.Frame_offset, 
        use_subsurf=False, 
        use_custom_props=MMT.User_props, 
        use_custom_props_enum_as_string=True, 
        ignore_leaf_bones=MMT.Leaf_bones, 
        force_connect_children=False, 
        automatic_bone_orientation=False, 
        primary_bone_axis=MMT.Primary_bone_axis, 
        secondary_bone_axis=MMT.Secondary_bone_axis, 
        use_prepost_rot=True, 
        axis_forward=MMT.Axis_forward, 
        axis_up=MMT.Axis_up)

# Saving this here it no longer gets used...
# uses constraints to apply keyframes based on imported animation to the MMT rig...
def A_Convert_By_Child(armature, target, no_parents, a_name):
    bpy.context.view_layer.objects.active = armature
    # get a reference to the imported animation...
    action = armature.animation_data.action
    # hop in and out of pose mode and clear the imported armatures transforms...
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='OBJECT')
    # deselect imported armature, select Mr Mannequins rig, go back into pose mode...
    armature.select_set(False)
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    
    Retarget_dict = {data.Control_name : data.Retarget_method for data in target.MMT.Retarget_data}
    
    # save current then show all target layers, we need them all open to set up constraints...
    layers = target.data.layers[:]
    target.data.layers = [True]*32
    bpy.ops.pose.reveal(select=True)
    # create a new action named after the FBX and clear all transforms...
    if target.animation_data is None:
        target.animation_data_create()
    target.animation_data.action = bpy.data.actions.new(name=a_name)    
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    # hide the deform and mechanism bones so they dont get processed...
    target.JK_MMT.Hide_deform_bones = True
    bpy.ops.pose.select_all(action='DESELECT')
    # if using switchable IK then set limbs to use FK...    
    if target.JK_MMT.IKvsFK_limbs == '2':
        for data in target.JK_MMT.IK_chain_data:
            if not data.Chain_use_fk:
                data.Chain_use_fk = True
    # if using switchable parenting without switchable IK then set that instead...
    elif target.JK_MMT.IK_parenting == '2':
        for data in target.JK_MMT.IK_chain_data:
            if data.Chain_use_parent:
                data.Chain_use_parent = False
    # if we are importing/converting root motion add a child of with no subtarget to the targets root control bone...
    if "root" in no_parents:
        bpy.context.active_object.data.bones.active = target.pose.bones["CB_root"].bone
        child_of = target.pose.bones["CB_root"].constraints.new(type='CHILD_OF')
        child_of.show_expanded = False
        child_of.name = "MMT_CHILD_OF"
        child_of.target = armature
        #child_of.subtarget = a_bone.name   
        context_copy = bpy.context.copy()
        context_copy["constraint"] = target.pose.bones["CB_root"].constraints["MMT_CHILD_OF"]
        bpy.ops.constraint.childof_clear_inverse(context_copy, constraint="MMT_CHILD_OF", owner='BONE')
        bpy.ops.constraint.childof_set_inverse(context_copy, constraint="MMT_CHILD_OF", owner='BONE')   
    # mute the default constraints...
    target.JK_MMT.Mute_default_constraints = True 
    # iterate over imported armatures pose bones...
    for a_bone in armature.pose.bones:
        if "CB_" + a_bone.name in target.pose.bones:
            # setting the target armatures active bone as we loop...
            t_bone = target.pose.bones["CB_" + a_bone.name]
            bpy.context.active_object.data.bones.active = t_bone.bone                                   
            # using limit loc/rots to fix inherited over rotation from using a child of when a parent also has a child of...
            if a_bone.name not in no_parents:
                limit_loc = t_bone.constraints.new(type='LIMIT_LOCATION')
                limit_loc.name = "MMT_LIMIT_LOC"
                limit_loc.show_expanded = False
                limit_loc.use_min_x = True
                limit_loc.use_min_y = True
                limit_loc.use_min_z = True
                limit_loc.use_max_x = True
                limit_loc.use_max_y = True
                limit_loc.use_max_z = True
                limit_loc.use_transform_limit = True
                limit_loc.owner_space = 'LOCAL_WITH_PARENT'
                limit_rot = t_bone.constraints.new(type='LIMIT_ROTATION')
                limit_rot.name = "MMT_LIMIT_ROT"
                limit_rot.show_expanded = False
                limit_rot.use_limit_x = True
                limit_rot.use_limit_y = True
                limit_rot.use_limit_z = True
                limit_rot.use_transform_limit = True
                limit_rot.owner_space = 'LOCAL_WITH_PARENT'
            # adding and setting the child of...
            child_of = t_bone.constraints.new(type='CHILD_OF')
            child_of.name = "MMT_CHILD_OF"
            child_of.show_expanded = False
            child_of.target = armature
            child_of.subtarget = a_bone.name   
            context_copy = bpy.context.copy()
            context_copy["constraint"] = t_bone.constraints["MMT_CHILD_OF"]
            bpy.ops.constraint.childof_clear_inverse(context_copy, constraint="MMT_CHILD_OF", owner='BONE')
            bpy.ops.constraint.childof_set_inverse(context_copy, constraint="MMT_CHILD_OF", owner='BONE')
            # some bones need there location locked or they have offset location issues...
            if t_bone.name in Retarget_dict:
                if Retarget_dict[t_bone.name] == 'SKELETON':
                    limit_loc1 = t_bone.constraints.new(type='LIMIT_LOCATION')
                    limit_loc1.name = "MMT_LIMIT_LOC_FIX"
                    limit_loc1.show_expanded = False
                    limit_loc1.use_min_x = True
                    limit_loc1.use_min_y = True
                    limit_loc1.use_min_z = True
                    limit_loc1.use_max_x = True
                    limit_loc1.use_max_y = True
                    limit_loc1.use_max_z = True
                    limit_loc1.owner_space = 'LOCAL'         
    bpy.ops.pose.select_all(action='DESELECT')
    # select everything that needs keyframing...
    for p_bone in target.pose.bones:
        if "CB" in p_bone.name or "PB" in p_bone.name or "AT" in p_bone.name or "LT" in p_bone.name:
            p_bone.bone.select = True
    bpy.context.active_object.data.bones.active = target.pose.bones["CB_root"].bone
    # iterate over frame range and insert visual keyframes... (might mess up curves if anim's keyframes are not at integers? seems fine on default mannequin anims though)
    for i in range(int(action.frame_range[0]), int(action.frame_range[1] + 1)):
        bpy.context.scene.frame_set(i)
        bpy.ops.pose.transforms_clear()
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_VisualLocRot')
        # maybe keyframe some things on the first frame...
        if i == int(action.frame_range[0]):
            if bpy.context.scene.JK_MMT.I_key_controls:
                target.JK_MMT.keyframe_insert(data_path="Mute_default_constraints", frame=i)
                if target.JK_MMT.IKvsFK_limbs == '2':
                    for data in target.JK_MMT.IK_chain_data:
                        data.keyframe_insert(data_path='Chain_use_fk', frame=i)
                elif target.JK_MMT.IK_parenting == '2':
                    for data in target.JK_MMT.IK_chain_data:
                        data.keyframe_insert(data_path='Chain_use_parent', frame=i)
    # remove the added constraints once keyframing has been completed...
    if "root" in no_parents:
        target.pose.bones["CB_root"].constraints.remove(target.pose.bones["CB_root"].constraints["MMT_CHILD_OF"])
    extra_bones = []
    for a_bone in armature.pose.bones:
        if "CB_" + a_bone.name in target.pose.bones:
            t_bone = target.pose.bones["CB_" + a_bone.name]
            if t_bone.constraints.get("MMT_LIMIT_LOC") != None:
                t_bone.constraints.remove(t_bone.constraints["MMT_LIMIT_LOC"])
            if t_bone.constraints.get("MMT_LIMIT_LOC_FIX") != None:
                t_bone.constraints.remove(t_bone.constraints["MMT_LIMIT_LOC_FIX"])
            if t_bone.constraints.get("MMT_LIMIT_ROT") != None:
                t_bone.constraints.remove(t_bone.constraints["MMT_LIMIT_ROT"])
            if t_bone.constraints.get("MMT_CHILD_OF") != None:
                t_bone.constraints.remove(t_bone.constraints["MMT_CHILD_OF"])
        else:
            extra_bones.append(a_bone.name)    
    # reset the targets armature layers to what was open when we started...
    target.data.layers = layers
    # remove the imported animation...
    bpy.data.actions.remove(action)
    # return to object mode... (only needed if batch importing?)
    bpy.ops.object.mode_set(mode='OBJECT')
    # print any extra bones...
    if len(extra_bones) > 0:
        print("These bones do not exist in the default mannequin armature: ", extra_bones[:], " Animation has not been imported/converted for them") 
