import bpy
import os
import mathutils

from . import Base_Functions

# ------------------- Saved Retargets --------------------------------------------------------------

# writes current retargets to a text... (will be needed to replace custom retargets after updates)
def Write_Retargets(retargets):
    text = bpy.data.texts.new("MMT_Custom_Retargets.py")
    text.write("""import bpy
# we need a reference to the retargets in the add-on preferences...
retargets = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets
# the custom retargets that we wrote to this text file...""")
    text.write("\ncustom_retargets = {\n")
    # for each retarget...
    for retarget in retargets:
        # format the retarget line...
        text.write('\t"{r_name}" : {syntax}\n'.format(r_name=retarget.name, syntax="{"))
        # for each bone of the retarget...
        for i, bone in enumerate(retarget.Bones):
            # get the syntax needed for the end of retarget dictionary...
            end = ("}," if i == (len(retarget.Bones) - 1) else ",")
            # format bone line...
            text.write('\t    "{b_name}" : [{indices}, "{parent}", "{r_method}", "{r_type}", "{subtarget}"]{syntax}\n'.format(
                b_name=bone.name, 
                indices=(bone.Indices[0], bone.Indices[1], bone.Indices[2]), 
                parent=bone.Parent, 
                r_method=bone.Retarget,
                r_type=bone.Type,
                subtarget=bone.Subtarget, 
                syntax=end))
    # close the entire dictionary...
    text.write("    }\n\n")
    # write the operator to re-add the written retargets when the script gets run...
    text.write("""# then when we run this...
for retarget, bones in custom_retargets.items():
    # add the retargets...
    r_data = retargets.add()
    r_data.name = retarget
    # iterate through bones...
    for bone, data in bones.items():
        # add the bone and its indices...
        b_data = r_data.Bones.add()
        b_data.name = bone
        b_data.Indices = data[0]
        b_data.Parent = data[1]
        b_data.Retarget = data[2]
        b_data.Type = data[3]
        b_data.Subtarget = data[4]""")

# adds a 2 dimensional dictionary to the current retargets...
def Set_New_Retargets(retargets, new_dict, clear):
    # if we want to clear current retargets first...
    if clear:
        retargets.clear()
    # iterate through new retargets dictionary...
    for retarget, bones in new_dict.items():
        # add the retargets...
        r_data = retargets.add()
        r_data.name = retarget
        # iterate through bones...
        for bone, data in bones.items():
            # add the bone and its indices...
            b_data = r_data.Bones.add()
            b_data.name = bone
            b_data.Indices = data[0]
            b_data.Parent = data[1]
            b_data.Retarget = data[2]
            b_data.Type = data[3]
            b_data.Subtarget = data[4]

# ------------------- Armature Retarget Data --------------------------------------------------------------
            
def Get_Is_Extra_From_Deform_Name(armature, name):
    bool = False
    for data in armature.JK_MMT.Retarget_data:
        if data.name == name and data.Mapping_indices == (-1, -1, -1):
            bool = True
            break
    return bool

def Set_New_Retarget_Data(r_data, name, indices, c_name, r_method, r_type, target, subtarget):
    b_data = r_data.add()
    b_data.name = name
    b_data.Mapping_indices = indices
    b_data.Control_name = c_name
    b_data.Retarget_method = r_method
    b_data.Retarget_type = r_type
    b_data.Target = target
    b_data.Subtarget = subtarget

def Get_Retarget_Type_From_Deform_Name(armature, name):
    type = 'NONE'
    #if armature.Rig_props.Retarget_data[name]:
        #return armature.Rig_props.Retarget_data[name].Retarget_type    
    for data in armature.JK_MMT.Retarget_data:
        if data.name == name:
            type = data.Retarget_type
            break
    return type

def Get_New_Matrix(location, scale, rotation):
    mat_loc = mathutils.Matrix.Translation(location)
    mat_sca = mathutils.Matrix.Scale(1, 4, scale) #scale.to_matrix().to_4x4()
    mat_rot = rotation.to_matrix().to_4x4() #t_bone.matrix.to_quaternion().to_matrix().to_4x4()# mathutils.Matrix.Rotation(math.radians(45.0), 4, 'X')#
    # combine transformations...
    mat_out = mat_loc @ mat_rot @ mat_sca
    return mat_out

def Set_Bone_Groups_Retarget(armature, is_adding):
    if is_adding:
        # add in deform bones group...
        armature.pose.bone_groups.new(name='Deform Bones')
        # Purple bones need to be checked/setup by the user...
        check_group = armature.pose.bone_groups.new(name='Manual Bones')
        check_group.color_set = 'THEME06'
        # Yellow bones think they know what they are doing...
        auto_group = armature.pose.bone_groups.new(name='Auto Bones')
        auto_group.color_set = 'THEME09'
        # add in group for gizmo bones...
        gizmo_group = armature.pose.bone_groups.new(name='Twist Bones')
        gizmo_group.color_set = 'THEME05'
        # Green bones that were not present in the template...
        extra_group = armature.pose.bone_groups.new(name='Extra Bones')
        extra_group.color_set = 'THEME03'
        # Red bones that were not present in the target...
        remove_group = armature.pose.bone_groups.new(name='Remove Bones')
        remove_group.color_set = 'THEME01'
        # add in group for floor bones...
        floor_group = armature.pose.bone_groups.new(name='Other Bones')
        floor_group.color_set = 'THEME04'
    else:
        for p_bone in armature.pose.bones:
            p_bone.bone_group = armature.pose.bone_groups['Auto Bones']
        armature.pose.bone_groups['Auto Bones'].name = 'Control Bones'
        armature.pose.bone_groups['Twist Bones'].name = 'Gizmo Bones'  
        armature.pose.bone_groups['Remove Bones'].name = 'IK Targets'  
        armature.pose.bone_groups['Manual Bones'].name = 'Mechanism Bones'
        armature.pose.bone_groups['Extra Bones'].name = 'Pivot Bones'
        armature.pose.bone_groups['Other Bones'].name = 'Floor Targets'  
        
def Set_Bone_Retarget_Type(armature, template, c_name, d_name, target, subtarget, r_type):
    template_bone = template.pose.bones[c_name]
    deform_bone = armature.pose.bones[d_name]
    # get rid of any constraints...
    for constraint in template_bone.constraints:
        template_bone.constraints.remove(constraint)    
    # set the new location in world space... 
    template_bone.matrix = Get_New_Matrix(deform_bone.matrix.to_translation(), template_bone.matrix.to_scale(), template_bone.matrix.to_quaternion())    
    # if stretch type retargeting...
    if r_type == 'STRETCH':
        template_bone.lock_location = [True, True, True]
        template_bone.ik_stretch = 1.0 #REMEMBER TO TURN OFF!!!
        # add stretching ik... (by default sets target to first child of deform bone)
        ik = template_bone.constraints.new('IK')
        ik.name = "STRETCH"
        ik.show_expanded = False
        ik.target = target        
        ik.subtarget = subtarget
        ik.chain_count = 1
        template_bone.bone_group = template.pose.bone_groups['Auto Bones']
    # if twist hold type...
    elif r_type == 'TWIST_HOLD': 
        template_bone.lock_location = [False, False, False]
        # add damped track... (holding Y is dependent on the tracking Y axis)               
        damped_track = template_bone.constraints.new('DAMPED_TRACK')
        damped_track.name = "TWIST_HOLD"
        damped_track.show_expanded = False
        damped_track.target = target
        damped_track.subtarget = subtarget
        damped_track.head_tail = 1.0
        template_bone.bone_group = template.pose.bone_groups['Twist Bones'] 
    # if twist follow...
    elif r_type == 'TWIST_FOLLOW': 
        template_bone.lock_location = [False, False, False]
        # add copy rotation... (following hand/foot Y is dependent on the hand/foot Y axis)               
        copy_rot = template_bone.constraints.new('COPY_ROTATION')
        copy_rot.name = "TWIST_FOLLOW"
        copy_rot.show_expanded = False
        copy_rot.target = target
        copy_rot.subtarget = subtarget
        copy_rot.target_space = 'LOCAL'
        copy_rot.owner_space = 'LOCAL'
        copy_rot.use_x = False
        copy_rot.use_z = False
        template_bone.bone_group = template.pose.bone_groups['Twist Bones']         
        # add damped track ? ... (just so it can be pointed the right way more easily)               
        #damped_track = template_bone.constraints.new('DAMPED_TRACK')
        #damped_track.name = "TWIST_HOLD"
        #damped_track.target = template
        #damped_track.subtarget = "" 
    elif r_type == 'ROOT_COPY':
        template_bone.lock_location = [True, True, True]
        if subtarget in target.pose.bones:
            copy_rot = template_bone.constraints.new('COPY_ROTATION')
            copy_rot.name = "ROOT_COPY"
            copy_rot.show_expanded = False
            copy_rot.target = target
            copy_rot.subtarget = subtarget
            template_bone.bone_group = template.pose.bone_groups['Other Bones'] 
    elif r_type == 'IK_DEFAULT':
        template_bone.lock_location = [True, True, True]
        if subtarget in target.pose.bones:
            copy_rot = template_bone.constraints.new('COPY_ROTATION')
            copy_rot.name = "IK_DEFAULT"
            copy_rot.show_expanded = False
            copy_rot.target = target
            copy_rot.subtarget = subtarget
            template_bone.bone_group = template.pose.bone_groups['Other Bones'] 
    elif r_type == 'NONE':
        # template_bone.bone.use_inherit_rotation = True
        template_bone.lock_location = [True, True, True]
        template_bone.bone_group = template.pose.bone_groups['Manual Bones']
    elif r_type == 'REMOVE':
        template_bone.bone_group = template.pose.bone_groups['Remove Bones'] 
    # set the retarget type...
    template.JK_MMT.Retarget_data[d_name].Retarget_type = r_type
    # then need to recalaculate matrix for any children...
    for child in deform_bone.children_recursive:
        c_control = template.pose.bones[template.JK_MMT.Retarget_data[child.name].Control_name]
        # update pose for the bone...
        bpy.context.view_layer.update()
        # get the deform bones translation, scale it by the armatures scale...
        #c_loc = c_deform.matrix.to_translation()
        #c_loc_scaled = [c_loc[0] * armature.scale[0], c_loc[1] * armature.scale[1], c_loc[2] * armature.scale[2]] 
        # set the new matrix...
        c_control.matrix = Get_New_Matrix(child.matrix.to_translation(), c_control.matrix.to_scale(), c_control.matrix.to_quaternion())    

def Get_Bone_Retarget_Type(bone):
    # if root is in the name and it has a parent...
    if "ROOT" in bone.name.upper() and bone.parent != None:
        subtarget = bone.parent.name
        r_type = 'ROOT_COPY'
    # if ik is in the name it's probably a built in IK target...
    elif "IK" in bone.name.upper():
        subtarget = ""
        r_type = 'IK_DEFAULT'
    # if the bone only has one child or it has a child with twist in its name...
    elif len(bone.children) == 1 or any("TWIST" in child.name.upper() for child in bone.children):
        for child in bone.children:
            if "TWIST" not in child.name.upper():
                name = child.name
                break
        subtarget = name
        r_type = 'STRETCH'
    # if there are multiple or no children with twist in the name...                
    else:
        subtarget = ""
        r_type = 'NONE'
    return r_type, subtarget 

def Set_Template_Retarget_Data(template, retarget, use_template, extra_bones):
    r_data = template.JK_MMT.Retarget_data
    # if we are using a template and a retarget...
    if use_template and retarget != None:
        mapping = {}
        # iterate through the templates bone data and the retargets bone data...
        for t_data in r_data:
            for s_data in retarget.Bones:
                # if two indices match then add the two names to a mapping dictionary...
                if t_data.Mapping_indices[:] == s_data.Indices[:]:
                    mapping[t_data.name] = s_data.name
        # iterate through the template bone data again...
        for t_data in r_data:
            e_bone = template.data.edit_bones[t_data.Control_name]
            # if it's in the mapping...
            if t_data.name in mapping: 
                # we need to change its name...
                t_data.name = mapping[t_data.name]
                s_data = retarget.Bones[t_data.name]
                t_data.Retarget_method = s_data.Retarget            
                t_data.Retarget_type = s_data.Type
                #t_data.Target = s_data.Target
                # if it's subtarget is also in the mapping dictionary... (subtargets always saved as deform names)   
                if t_data.Subtarget in mapping:
                    t_data.Subtarget = mapping[t_data.Subtarget]
                elif t_data.Subtarget in retarget.Bones:
                    t_data.Subtarget = s_data.Subtarget
            else:
                t_data.Retarget_type, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)
        # and if there are any extra bones we need to set them up too
        for name in extra_bones:
            e_bone = template.data.edit_bones["CB_" + name]
            if name not in r_data:
                t_data = r_data.add()
            else:
                t_data = r_data[name]
            t_data.name = name
            t_data.Control_name = "CB_" + name
            if name in retarget.Bones:
                s_data = retarget.Bones[name]
                t_data.Mapping_indices = s_data.Indices
                t_data.Retarget_method = s_data.Retarget
                t_data.Retarget_type = s_data.Type
                # if it's subtarget is also in the mapping dictionary... (subtargets always saved as deform names)   
                if t_data.Subtarget in mapping:
                    t_data.Subtarget = mapping[t_data.Subtarget]
                elif t_data.Subtarget in retarget.Bones:
                    t_data.Subtarget = s_data.Subtarget 
            else:
                t_data.Retarget_type, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)
    # if we are not using a template but we are using a retarget...
    elif not use_template and retarget != None:
        # iterate through the generated templates bones...
        for e_bone in template.data.edit_bones:
            t_data = r_data.add()
            t_data.name = e_bone.name
            t_data.Control_name = "CB_" + e_bone.name
            # if the bones name is in the retarget...
            if e_bone.name in retarget.Bones:
                s_data = retarget.Bones[e_bone.name]
                t_data.Mapping_indices = s_data.Indices
                t_data.Retarget_method = s_data.Retarget
                t_data.Retarget_type = s_data.Type
                #t_data.Target = s_data.Target
                t_data.Subtarget = s_data.Subtarget
            else:
                t_data.Retarget_type, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)
                #t_data.Retarget_type, t_data.Target, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)        
            e_bone.name = "CB_" + e_bone.name
    # if we are using a template but not a retarget...
    elif use_template and retarget == None:
        # only need to create extra bone data...
        for name in extra_bones:
            e_bone = template.data.edit_bones["CB_" + name]
            if name not in r_data:
                t_data = r_data.add()
            else:
                t_data = r_data[name]
            t_data.name = name
            t_data.Control_name = "CB_" + name
            t_data.Retarget_type, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)
    # if we aren't using either a template or a target...
    else:
        # just set up predicted data for all bones...
        for e_bone in template.data.edit_bones:
            t_data = r_data.add()
            t_data.name = e_bone.name
            t_data.Control_name = "CB_" + e_bone.name
            t_data.Retarget_type, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)
            #t_data.Retarget_type, t_data.Target, t_data.Subtarget = Get_Bone_Retarget_Type(e_bone)
            e_bone.name = "CB_" + e_bone.name

def Set_Template_Hierarchy(template, armature):
    r_data = template.JK_MMT.Retarget_data
    # loop through the targets deform bones...
    for bone in armature.data.edit_bones:
        # getting their control bones...
        c_bone = template.data.edit_bones[r_data[bone.name].Control_name]
        # if the deform bone has a parent...
        if bone.parent != None:
            # set the control bones parent to the control bone used by the parent...
            c_bone.parent = template.data.edit_bones[r_data[bone.parent.name].Control_name]
        # otherwise make sure the control bone has no parent...
        else:
            c_bone.parent = None

# start the retargeting process...
def Start_Rig_Retargeting(armature, template_name, retarget):
    template = None
    scene = bpy.context.scene
    MMT = scene.JK_MMT
    use_template = True if template_name != 'NONE' else False
    default_dir = os.path.join(MMT.MMT_path, "MMT_Stash")    
    unit_scale = scene.unit_settings.scale_length
    if use_template:
        # load the template...    
        with bpy.data.libraries.load(os.path.join(default_dir, template_name + ".blend"), link=False, relative=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name == template_name]
            data_to.texts = [name for name in data_from.texts if name == template_name + ".py"]
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
    else:        
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.duplicate()
        template = bpy.context.object
        template.JK_MMT.Rig_type = 'TEMPLATE'
    # if the template loaded set everything up...
    if template != None:
        bpy.ops.object.mode_set(mode='POSE')
        Set_Bone_Groups_Retarget(template, True)
        armature.data.display_type = 'STICK'
        template.data.display_type = 'OCTAHEDRAL'
        extra_bones = []
        # go into edit mode...
        bpy.ops.object.mode_set(mode='EDIT')
        # if we are using a template...
        if use_template:                   
            # any extra bones should be created...
            if retarget != None:
                extra_bones = [bone.name for bone in armature.data.edit_bones if bone.name not in template.JK_MMT.Retarget_data and bone.name not in retarget.Bones] 
            else:    
                extra_bones = [bone.name for bone in armature.data.edit_bones if bone.name not in template.JK_MMT.Retarget_data]                               
            # add controls and retarget data for any extra bones...
            for name in extra_bones:
                deform_bone = armature.data.edit_bones[name]
                template_bone = template.data.edit_bones.new("CB_" + name)
                template_bone.head = deform_bone.head
                template_bone.tail = deform_bone.tail
                template_bone.roll = deform_bone.roll
                template_bone.use_deform = False
                template_bone.use_inherit_rotation = False
                template_bone.inherit_scale = 'NONE'
                template_bone.layers = [False]*16+[True]+[False]*15
            # if we are using a template we need to setup the retarget data first in order to...
            Set_Template_Retarget_Data(template, retarget, use_template, extra_bones)
            # mimic the deform armatures hierarchy...
            Set_Template_Hierarchy(template, armature)    
        # if we aren't using a template...
        else:
            # set all template bones to be disconnected and not inherit or deform anything...
            for e_bone in template.data.edit_bones:
                e_bone.use_connect = False
                e_bone.use_deform = False
                e_bone.use_inherit_rotation = False
                e_bone.inherit_scale = 'NONE'
        # set up the retarget data... (if using a template we may need to correct it after mimicing hierarchy)
        Set_Template_Retarget_Data(template, retarget, use_template, extra_bones)
        # back to pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # select everything and clear all transforms...
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear() 
        # pose the template roughly to the target armature using the retarget data...
        for data in template.JK_MMT.Retarget_data:
            c_bone = template.pose.bones[data.Control_name]
            target = template if data.Retarget_type in ['ROOT_COPY', 'TWIST_HOLD', 'TWIST_FOLLOW', 'IK_DEFAULT'] else armature
            subtarget = "CB_" + data.Subtarget if data.Retarget_type in ['ROOT_COPY', 'TWIST_HOLD', 'TWIST_FOLLOW', 'IK_DEFAULT'] else data.Subtarget
            if data.name in armature.pose.bones:
                Set_Bone_Retarget_Type(armature, template, data.Control_name, data.name, target, subtarget, data.Retarget_type)
                if data.name in extra_bones:
                    c_bone.bone_group = template.pose.bone_groups["Extra Bones"]
            # if the template bone does not have a deform bone to control...
            else:
                # add to removal bones...
                c_bone.bone_group = template.pose.bone_groups["Remove Bones"]
        # save the name of the armature we are retargeting too...
        template.JK_MMT.Retarget_target = armature.name                    
        template.name = armature.name + "_Retarget"

def Add_Deform_Mechanism(armature, template):
    # in edit mode add all the mechanism bones to the template armature...
    for data in template.JK_MMT.Retarget_data:
        deform_bone = armature.data.edit_bones[data.name]
        # connected deform bones would require an entirely different system...
        deform_bone.use_connect = False
        mech_bone = template.data.edit_bones.new("MB_" + deform_bone.name)
        mech_bone.head = deform_bone.head
        mech_bone.tail = deform_bone.tail
        mech_bone.roll = deform_bone.roll
        mech_bone.parent = template.data.edit_bones[data.Control_name]
        mech_bone.use_deform = False
        mech_bone.use_inherit_rotation = True             
    # in pose mode set up all the deform bones copy transforms constraints
    bpy.ops.object.mode_set(mode='POSE')
    for p_bone in armature.pose.bones:
        copy_trans = p_bone.constraints.new("COPY_TRANSFORMS")
        copy_trans.target = template
        copy_trans.show_expanded = False
        copy_trans.subtarget = "MB_" + p_bone.name   
        p_bone.bone.layers = [False]*8+[True]+[False]*23
        p_bone.custom_shape = bpy.data.objects["B_Shape_Deform"]
        template.pose.bones["MB_" + p_bone.name].bone.layers = [False]*24+[True]+[False]*7
        template.pose.bones["MB_" + p_bone.name].bone_group = template.pose.bone_groups['Mechanism Bones']
        template.pose.bones["MB_" + p_bone.name].custom_shape = bpy.data.objects["B_Shape_Mechanism"]

# apply the retargeted bone transforms...
def Apply_Rig_Retargeting(armature, template, template_name):
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
    # get any the bones that need removing...
    remove_bones = [bone.name for bone in template.pose.bones if bone.bone_group.name == "Remove Bones"]    
    # set bone groups to rigging bone groups...
    Set_Bone_Groups_Retarget(template, False)
    # enter edit mode to get rid of any bones that weren't present in the template...
    bpy.ops.object.mode_set(mode='EDIT')
    for name in remove_bones:
        template.data.edit_bones.remove(template.data.edit_bones[name])
        for i, data in enumerate(template.JK_MMT.Retarget_data):
            if data.Control_name == name:
                template.JK_MMT.Retarget_data.remove(i)
    # back to object mode to select both template and source armatures again..,
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    template.select_set(True)
    bpy.context.view_layer.objects.active = template        
    # now into edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    # symmetrize the bone rolls of the template...
    Base_Functions.Set_Symmetrical_Control_Rolls(template, True)
    # add in the mechanism bones and costrain the deform bones...
    Add_Deform_Mechanism(armature, template)
    # then back to object mode to change modifiers...
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
    # and join the target into the template...        
    bpy.ops.object.join()
    # then back to pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # iterate through all the bones and return their settings to default...
    for p_bone in template.pose.bones:
        p_bone.lock_location = [False, False, False]
        p_bone.ik_stretch = 0.0
        p_bone.bone.use_inherit_rotation = True
        p_bone.bone.inherit_scale = 'FULL'
        # if the pose bone doesn't have a group then it must be a deform bone...
        if p_bone.bone_group == None:
            p_bone.bone_group = template.pose.bone_groups['Deform Bones']
    # finally set the rig type...
    template.JK_MMT.Rig_type = 'CUSTOM'

# force rest locations and/or rotations from the template...
def Force_Template_Pose(target, template_name, force_rot, force_loc):
    scene = bpy.context.scene
    MMT = scene.JK_MMT
    unit_scale = scene.unit_settings.scale_length
    default_dir = os.path.join(MMT.MMT_path, "MMT_Stash")    
    # load the template... (again)    
    with bpy.data.libraries.load(os.path.join(default_dir, template_name + ".blend"), link=False, relative=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name == template_name]
        data_to.texts = [name for name in data_from.texts if name == template_name + ".py"]
    # check and scale it...
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            template = obj
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
        for s_data in target.JK_MMT.Retarget_data:
            for t_data in template.JK_MMT.Retarget_data:
                if s_data.Mapping_indices[:] == t_data.Mapping_indices[:]:
                    s_bone = target.pose.bones[s_data.Control_name]
                    t_bone = template.pose.bones[t_data.Control_name]
                    # if we want template bone rotations...
                    if force_rot:
                        copy_rot = s_bone.constraints.new('COPY_ROTATION')
                        copy_rot.name = "MMT FORCE - Copy Rotation"
                        copy_rot.show_expanded = False
                        copy_rot.target = template
                        copy_rot.subtarget = t_bone.name
                    # if we want template bone locations...
                    if force_loc:
                        copy_loc = s_bone.constraints.new('COPY_LOCATION')
                        copy_loc.name = "MMT FORCE - Copy Location"
                        copy_loc.show_expanded = False
                        copy_loc.target = template
                        copy_loc.subtarget = t_bone.name                                
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
        # clear all constraints...
        #bpy.ops.pose.select_all(action='SELECT')
        for p_bone in target.pose.bones:
            for constraint in p_bone.constraints:
                if constraint.name.startswith("MMT FORCE"):
                    p_bone.constraints.remove(constraint)
        #bpy.ops.pose.constraints_clear()
        
        bpy.data.objects.remove(template)   

# ------------------- Animation Retarget Functions --------------------------------------------------------------

# reorganises animation data to be more iterable...
def Get_Object_Anim_Data(fcurves):
    # declare and prepare keyframe data...
    key_data = {key.co[0] : {} for fcurve in fcurves for key in fcurve.keyframe_points}
    # for each keyframe...
    for key, data in key_data.items():
        # for each fcurve...
        for fcurve in fcurves:
            # get the channel and the channel array index...
            c_name = fcurve.data_path
            c_index = fcurve.array_index
            if c_name not in data:
                data[c_name] = []
            data[c_name].insert(c_index, fcurve)
    return key_data

def Set_Object_Keys_To_Root(source, target, r_name):
    # need a reference to the action...
    s_action = source.animation_data.action
    s_action.use_fake_user = False
    t_action = source.animation_data.action.copy()
    for curve in t_action.fcurves:
        if curve.data_path in ["location", "rotation_quaternion", "rotation_euler", "scale"]:
            t_action.fcurves.remove(curve)
    if target.animation_data is None:
            target.animation_data_create()
    target.animation_data.action = t_action
    # ensure source and target are selected...
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.mode_set(mode='POSE') 
    bpy.ops.pose.select_all(action='DESELECT')
    # get our root bone...
    t_root = target.pose.bones[r_name]
    # make sure it's selected and active...
    bpy.context.active_object.data.bones.active = t_root.bone
    t_root.bone.select = True
    # give it a child of targeting the target armature...
    child_of = t_root.constraints.new(type='CHILD_OF')
    child_of.show_expanded = False
    child_of.name = "MMT - Child Of"
    child_of.target = source
    # copy context and stuff to clear and invert the child of constraint...  
    context_copy = bpy.context.copy()
    context_copy["constraint"] = t_root.constraints["MMT - Child Of"]
    bpy.ops.constraint.childof_clear_inverse(context_copy, constraint="MMT - Child Of", owner='BONE')
    bpy.ops.constraint.childof_set_inverse(context_copy, constraint="MMT - Child Of", owner='BONE')
    # get all the objects keyframes
    curves = [curve for curve in s_action.fcurves if curve.data_path in ["location", "rotation_quaternion", "rotation_euler", "scale"]]
    # get all keyframe data... 
    anim_data = Get_Object_Anim_Data(curves)
    # for each frame...
    for keyframe, key_data in anim_data.items():
        # declare is keyframed dictionary...
        is_keyed = {'location' : False, 'rotation_quaternion' : False, 'rotation_euler' : False, 'scale' : False}
        for c_name, c_curves in key_data.items():
            for c_curve in c_curves:
                if not is_keyed[c_name]:  
                    if any(key.co[0] == keyframe for key in c_curve.keyframe_points):
                        is_keyed[c_name] = True
                exec("source." + c_name + "[" + str(c_curve.array_index) + "] = c_curve.evaluate(keyframe)")
        # clear any transforms left over from last time...
        bpy.ops.pose.transforms_clear()
        # iterate over the is_keyed dictionary...
        for c_name, value in is_keyed.items():
            # if the channel should be keyed...
            if value:
                # key it visually...
                t_root.keyframe_insert(c_name, index=-1, frame=keyframe, group=t_root.name, options={'INSERTKEY_VISUAL'})
    
    t_root.constraints.remove(t_root.constraints["MMT - Child Of"])

# reorganises animation data to be more iterable...
def Get_Anim_Data(action):
    # declare and prepare keyframe data...
    key_data = {key.co[0] : {} for fcurve in action.fcurves for key in fcurve.keyframe_points}
    # for each keyframe...
    for key, data in key_data.items():
        # for each fcurve...
        for fcurve in action.fcurves:
            # get the bone name, the channel and the channel array index...
            b_name = fcurve.data_path.partition('"')[2].split('"')[0]
            c_name = Base_Functions.Get_Fcurve_Channel(fcurve)
            c_index = fcurve.array_index
            # if we have a bone name and a channel name...
            if b_name != '' and c_name != None:
                if b_name not in data:
                    data[b_name] = {}
                if c_name not in data[b_name]:
                    data[b_name][c_name] = []
                data[b_name][c_name].insert(c_index, fcurve)
    return key_data

# create a dictionary of source bones to target bones...
def Get_Mapping_Data(source, target):
    mapping_data = {}
    # if the source has retarget data...
    if len(source.JK_MMT.Retarget_data) > 0:
        # iterate through it and compare with targets retarget data...
        for s_data in source.JK_MMT.Retarget_data:
            for t_data in target.JK_MMT.Retarget_data:
                #print(a_data.Mapping_indices, t_data.Mapping_indices)
                if s_data.Mapping_indices[:] == t_data.Mapping_indices[:]:
                    # get the source bone...
                    s_bone = source.pose.bones[s_data.Control_name]
                    # get the target bone...
                    t_bone = target.pose.bones[t_data.Control_name]
                    # get rotation inheritance to save it for later...
                    inherit_rot = t_bone.bone.use_inherit_rotation
                    # make sure inherit rotation is not on...
                    t_bone.bone.use_inherit_rotation = False
                    # set target bone to rest pose of anim bone...
                    t_bone.matrix = Base_Functions.Get_Scaled_Loc_Matrix(t_bone, s_bone, source)
                    # update the pose bones...
                    bpy.context.view_layer.update()
                    # get the local rotation difference...
                    rot_diff = t_bone.rotation_quaternion.rotation_difference((1, 0, 0, 0))
                    # set the mapping data entry...
                    mapping_data[t_data.Control_name] = [s_data.Control_name, rot_diff, inherit_rot, t_data.Retarget_method]
    # if there is no source retarget data...
    else:
        # iterate through source bones...
        for s_bone in source.pose.bones:
            # try and create mapping from names...
            if s_bone.name in target.JK_MMT.Retarget_data:
                t_data = target.JK_MMT.Retarget_data[s_bone.name]
                # get the target bone...
                t_bone = target.pose.bones[t_data.Control_name]
                # get rotation inheritance...
                inherit_rot = t_bone.bone.use_inherit_rotation
                # make sure inherit rotation is not on...
                t_bone.bone.use_inherit_rotation = False
                # set target bone to rest pose of anim bone...
                t_bone.matrix = Base_Functions.Get_Scaled_Loc_Matrix(t_bone, s_bone, source)
                # update the pose bones...
                bpy.context.view_layer.update()
                # get the local rotation difference...
                rot_diff = t_bone.rotation_quaternion.rotation_difference((1, 0, 0, 0))
                # set the mapping data entry...
                mapping_data[t_data.Control_name] = [s_bone.name, rot_diff, inherit_rot, t_data.Retarget_method]
    
    return mapping_data

# sets the keyframing for a bone relative to another bones matrix...
def Set_Bone_Anim_Matrix(keyframe, m_data, source, s_bone, t_bone, bones_keyed): 
    # if inherit rotation has been set back to true after getting differences..
    if t_bone.bone.use_inherit_rotation:
        # set it back to false...
        t_bone.bone.use_inherit_rotation = False
    # set the target bone to the animation bone...
    t_bone.matrix = Base_Functions.Get_Scaled_Loc_Matrix(t_bone, s_bone, source)
    # fix the local rotation...            
    t_bone.rotation_quaternion = t_bone.rotation_quaternion @ m_data[1]
    # update pose for the bone...
    bpy.context.view_layer.update()
    # if this bone should be using inherit rotation...
    if m_data[2]: 
        # get a copy of the world space matrix with inherit rotation off...
        copy_matrix = t_bone.matrix.copy()
        # set inherit rotation true...
        t_bone.bone.use_inherit_rotation = True
        # return bones world space matrix to what it was without inherited rotation...
        t_bone.matrix = copy_matrix
        # update the view layer again...
        bpy.context.view_layer.update()
    # if this bone is in the keyframed bones...    
    if m_data[0] in bones_keyed:
        # get what channels should be keyframed on the bone...
        is_keyed = bones_keyed[m_data[0]]
        # key channels depending on retarget method... (currently just keying all channels per transform incase bones have very different rest poses)
        for channel, keyed in is_keyed.items():
            if keyed:
                if channel == 'location':
                    if m_data[3] == 'ANIMATION':
                        t_bone.keyframe_insert(channel, index=-1, frame=keyframe, group=t_bone.name, options={'INSERTKEY_VISUAL'})
                else:
                    t_bone.keyframe_insert(channel, index=-1, frame=keyframe, group=t_bone.name, options={'INSERTKEY_VISUAL'})

# retarget an animation from one armature to another by fcurve...
def Anim_Retarget_By_Curve(source, target, a_name, remove_action):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT') 
    # ensure source and target are selected...
    bpy.context.view_layer.objects.active = target
    source.select_set(True)
    target.select_set(True)
    # get a reference to the animation...
    action = source.animation_data.action
    # go into pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # save current then show all armature layers, we might need them all open...
    s_layers = source.data.layers[:]
    source.data.layers = [True]*32
    t_layers = target.data.layers[:]
    target.data.layers = [True]*32
    bpy.ops.pose.reveal(select=True)
    # to select everything and clear all transforms...
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    # then try to set up bone to bone mapping dictionary...
    mapping_data = Get_Mapping_Data(source, target)
    # check there is mapping data to be used...
    if len(mapping_data) == 0:
        # if we couldn't map any bones together return layers...
        bpy.ops.object.mode_set(mode='OBJECT')
        source.data.layers = s_layers
        target.data.layers = t_layers
        Base_Functions.Show_Message(message = "No source bones can be mapped to target bones!", title = "Error", icon = 'ERROR')
    else:
        m_string = str(len(mapping_data)) + " of the source armatures " + str(len(source.data.bones)) + " bones have been mapped to the target."
        Base_Functions.Show_Message(message = m_string, title = "Info", icon = 'INFO')        
        # create a new action and clear all transforms...
        if target.animation_data is None:
            target.animation_data_create()
        target.animation_data.action = bpy.data.actions.new(name=a_name)
        target.JK_MMT.Mute_default_constraints = True
        # get all keyframe data... 
        anim_data = Get_Anim_Data(action)
        # for each frame...
        for keyframe, key_data in anim_data.items():
            # declare the dictionary that will define which bones need keyframing...
            bones_keyed = {}
            # for each bone...
            for bone_name, bone_data in key_data.items():
                # get the imported animation bone...
                s_bone = source.pose.bones[bone_name]
                # declare is keyframed dictionary...
                is_keyed = {'location' : False, 'rotation_quaternion' : False, 'rotation_euler' : False, 'scale' : False}       
                # if the channel has any fcurves, iterate through each transform by channel to recreate the frame..
                if 'location' in bone_data:
                    for loc_curve in bone_data['location']:
                        # if location has not been set as keyed already...
                        if not is_keyed['location']:
                            # check if it should be...
                            if any(key.co[0] == keyframe for key in loc_curve.keyframe_points):
                                is_keyed['location'] = True
                        # set bone location by channel to it's evaluated fcurve...
                        s_bone.location[loc_curve.array_index] = loc_curve.evaluate(keyframe)
                if 'quaternion' in bone_data:
                    for quat_curve in bone_data['quaternion']:
                        # if quaternion has not been set as keyed already...
                        if not is_keyed['rotation_quaternion']:
                            # check if it should be...
                            if any(key.co[0] == keyframe for key in quat_curve.keyframe_points):
                                is_keyed['rotation_quaternion'] = True
                        # set bone quaternion by channel to it's evaluated fcurve...
                        s_bone.rotation_quaternion[quat_curve.array_index] = quat_curve.evaluate(keyframe)
                if 'euler' in bone_data:
                    for euler_curve in bone_data['euler']:
                        # if euler has not been set as keyed already...
                        if not is_keyed['rotation_euler']:
                            # check if it should be...
                            if any(key.co[0] == keyframe for key in euler_curve.keyframe_points):
                                is_keyed['rotation_euler'] = True
                        # set bone euler by channel to it's evaluated fcurve...
                        s_bone.rotation_euler[euler_curve.array_index] = euler_curve.evaluate(keyframe)
                if 'scale' in bone_data:
                    for scale_curve in bone_data['scale']:
                        # if scale has not been set as keyed already...
                        if not is_keyed['scale']:
                            # check if it should be...
                            if any(key.co[0] == keyframe for key in scale_curve.keyframe_points):
                                is_keyed['scale'] = True
                        # set bone scale by channel to it's evaluated fcurve...
                        s_bone.scale[scale_curve.array_index] = scale_curve.evaluate(keyframe)
                # enter bone name and which channels are keyframed into keyframed bones dictionary
                bones_keyed[bone_name] = is_keyed
            # update the view layer to update matrices...    
            bpy.context.view_layer.update()
            # get bones with no parents because it's...
            roots = [bone.name for bone in target.pose.bones if bone.parent == None]
            # more efficient to iterate over everything using hierarchy so we dont re-key anything...
            for t_name in roots:
                t_bone = target.pose.bones[t_name]
                if t_name in mapping_data:
                    m_data = mapping_data[t_name]
                    s_bone = source.pose.bones[m_data[0]]
                    Set_Bone_Anim_Matrix(keyframe, m_data, source, s_bone, t_bone, bones_keyed)
                # if a bone get's set we need to do it's children as well...   
                for t_child in t_bone.children_recursive:
                    if t_child.name in mapping_data and mapping_data[t_child.name][0] in key_data:
                        c_data = mapping_data[t_child.name]
                        s_child = source.pose.bones[c_data[0]]
                        Set_Bone_Anim_Matrix(keyframe, c_data, source, s_child, t_child, bones_keyed)
        # KEY INTERPOLATION NOT SUPPORTED FIGURE THIS OUT AT SOME POINT!!!
        # iterate through the converted animations fcurves to set up interpolation...        
        #for fcurve in target.animation_data.action.fcurves:
            #name = fcurve.data_path.partition('"')[2].split('"')[0]
            #for key in fcurve.keyframe_points:        
                #key.interpolation = anim_data[key.co[0]][mapping_data[name][0]][Base_Functions.Get_Fcurve_Channel(fcurve)][1]    
        
        # select all bones and clear transforms to get rid of any unkeyed locations...
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()  
        # reset the target and source layers to what was open when we started...
        target.data.layers = t_layers
        source.data.layers = s_layers
        # if we want to remove the source animation...
        if remove_action:
            bpy.data.actions.remove(action)
        # return to object mode...
        bpy.ops.object.mode_set(mode='OBJECT')