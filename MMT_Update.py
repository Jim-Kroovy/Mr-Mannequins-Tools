import bpy
import os

#---------- NOTES -----------------------------------------------------------------------------

# Okay so i tried a few different ways of updating the rig and creating a seperate update script turns out to be the least destructive...
# and will save me from filling up the __init__ file with loads of functions in the future as well as leaving me open for any updates...

# It gives me a place to store all the scripture need to update through from any version to the current one...
# The operator that fires these functions in the __init__.py can be conditioned to only show in the interface when an update is required...
# And to only fire off the needed update functions to update stuff to the current add-on version...

# There may still need to be some user input in order to do updates but i will try to keep that to a minimum...

#---------- EXECUTION -------------------------------------------------------------------------

# updates a mannequin rig from v1.0 to v1.1...
def Update_1_1(armature, MMT):
    layers = armature.data.layers[:]
    armature.data.layers = [True]*32
    # jump into edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    # add the hand floor targets...
    for name in ["FT_hand_l", "FT_hand_r"]:
        e_bone = armature.data.edit_bones.new(name)
        if "_l" in name:
            e_bone.head = [0.6, 0, 0]
            e_bone.tail = [0.6, 0, -0.1]
        else:
            e_bone.head = [-0.6, 0, 0]
            e_bone.tail = [-0.6, 0, -0.1]
        e_bone.roll = 0
    # switch to object mode to load the custom shapes for the hand floor targets...    
    bpy.ops.object.mode_set(mode='OBJECT')
    default_dir = os.path.join(MMT.MMT_path, "MMT_Stash")    
    with bpy.data.libraries.load(os.path.join(default_dir, "ARMATURE_UE4_Mannequin_Skeleton.blend"), link=False, relative=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if "B_Shape_HandFloor" in name]
    # usually here's where we would link appended objects to the current scene/collection but the custom shapes are only for bone displays...
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.reveal(select=True)
    for obj in data_to.objects:
        if obj is not None:
            # set the recently loaded custom shape...
            armature.pose.bones["FT_hand_" + ("l" if obj.name.endswith("_L") else "r")].custom_shape = obj
            armature.pose.bones["FT_hand_" + ("l" if obj.name.endswith("_L") else "r")].custom_shape_scale = 1.5
            armature.pose.bones["FT_hand_" + ("l" if obj.name.endswith("_L") else "r")].bone_group = armature.pose.bone_groups["Floor Targets"]
            # give the hand IK target a floor constraint...
            constraint = armature.pose.bones["AT_hand_" + ("l" if obj.name.endswith("_L") else "r")].constraints.new("FLOOR")
            constraint.target = armature
            constraint.subtarget = "FT_hand_" + ("l" if obj.name.endswith("_L") else "r")
            constraint.use_rotation = True
            constraint.floor_location = 'FLOOR_NEGATIVE_Y'
            constraint.offset = -0.03
    # iterate through pose bones...    
    for p_bone in armature.pose.bones:
        # if control bone or IK target bone add default constraint mute driver to all constraints...
        if "CB" in p_bone.name or "AT" in p_bone.name or "LT" in p_bone.name:                
            # remove child ofs from ik targets...
            if "AT" in p_bone.name or "LT" in p_bone.name:
                if "Child Of" in p_bone.constraints:
                    p_bone.constraints.remove(p_bone.constraints["Child Of"])
            # set up ik chain data in armatures property group...            
            elif "lowerarm" in p_bone.name or "calf" in p_bone.name:
                if "twist" not in p_bone.name:
                    constraint = p_bone.constraints["IK"]
                    data = armature.JK_MMT.IK_chain_data.add()
                    data.Owner_name = p_bone.name
                    if armature.pose.bones[constraint.subtarget].parent == None:
                        data.Parent_name = constraint.subtarget
                    else:
                        parent_bone = armature.pose.bones[constraint.subtarget]
                        while parent_bone.parent != None:
                            parent_bone = parent_bone.parent
                        data.Parent_name = parent_bone.name  
                    data.Target_name = constraint.subtarget
                    data.Pole_name = constraint.pole_subtarget
                    data.Pole_angle = constraint.pole_angle        
                    data.Root_name = ("CB_ik_hand_root" if "arm" in p_bone.name else "CB_ik_foot_root")
                    data.Chain_name = ("Left " if p_bone.name.endswith("_l") else "Right ") + ("Arm" if "arm" in p_bone.name else "Leg")
            # add mute default constraints driver to all constraints...
            for constraint in p_bone.constraints:
                driver = constraint.driver_add("mute")       
                var = driver.driver.variables.new()
                var.name = "Master_Mute"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = armature
                var.targets[0].data_path = "JK_MMT.Mute_default_constraints"
                driver.driver.expression = "Master_Mute"
                if len(driver.modifiers) > 0:
                    driver.modifiers.remove(driver.modifiers[0])
        # else if deform or mechanism bone add the hide driver...
        elif not any(p_bone.name.startswith(prefix) for prefix in ["CB", "GB", "AT", "LT", "FT", "PB", "HT"]):
            driver = p_bone.bone.driver_add("hide")       
            var = driver.driver.variables.new()
            var.name = "Hide_Deform_Bones"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = armature
            var.targets[0].data_path = "JK_MMT.Hide_deform_bones"
            driver.driver.expression = "Hide_Deform_Bones"
            if len(driver.modifiers) > 0:
                driver.modifiers.remove(driver.modifiers[0])
    # go back to object mode and delete old custom property and set the new one...
    bpy.ops.object.mode_set(mode='OBJECT')
    del armature["MrMannequinRig"]
    armature.JK_MMT.Rig_type = 'MANNEQUIN'
    # return layers to original...
    armature.data.layers = layers

# updates a mannequin rig from v1.1 to v1.2...    
def Update_1_2(armature, MMT):
    if armature.get("MMT Rig Version") == None and armature.JK_MMT.Rig_type != 'NONE':
        lower_twist_controls = ["CB_lowerarm_twist_01_l", "CB_lowerarm_twist_01_r", "CB_calf_twist_01_l", "CB_calf_twist_01_r"]
        breast_bones = ["CB_breast_l", "CB_breast_r", "MB_breast_l", "MB_breast_r", "breast_l", "breast_r"]
        
        bpy.ops.object.mode_set(mode='EDIT')
        for name in lower_twist_controls:
            twist_control = armature.data.edit_bones[name]
            twist_pivot = armature.data.edit_bones.new("PB" + name[2:])
            twist_pivot.head = twist_control.head
            twist_pivot.tail = twist_control.tail
            twist_pivot.roll = twist_control.roll
            twist_pivot.parent = twist_control.parent
            twist_pivot.use_deform = False
            twist_control.parent = twist_pivot
            twist_pivot.layers = [False]*17+[True]+[False]*14
        
        for name in breast_bones:
            if not name.startswith("CB"):                    
                breast_bone = armature.data.edit_bones.new(name)                    
                breast_bone.head = [0.09882199764251709 if "_l" in name else -0.09882199764251709, -0.0955442488193512, 1.3807976245880127]
                breast_bone.tail = [0.09882199764251709 if "_l" in name else -0.09882199764251709, -0.0955442488193512, 1.5214824676513672]
                breast_bone.roll = -1.2863081693649292 if "_l" in name else 1.2863081693649292
                breast_bone.parent = armature.data.edit_bones["spine_03"]
                if name.startswith("MB"):
                    breast_bone.parent = armature.data.edit_bones["CB" + name[2:]]                        
                    breast_bone.use_deform = False
                    breast_bone.layers = [False]*24+[True]+[False]*7
                else:
                    breast_bone.parent = armature.data.edit_bones["spine_03"]
                    breast_bone.use_deform = True
                    breast_bone.layers = [False]*8+[True]+[False]*23
            else:
                breast_bone = armature.data.edit_bones.new(name)                    
                breast_bone.head = [0.09882199764251709 if "_l" in name else -0.09882199764251709, -0.0955442488193512, 1.3807976245880127]
                breast_bone.tail = [0.1383073627948761 if "_l" in name else -0.1383073627948761, -0.2305743247270584, 1.3807976245880127]
                breast_bone.roll = 1.5707963705062866 if "_l" in name else -1.5707963705062866
                breast_bone.parent = armature.data.edit_bones["CB_spine_03"]
                breast_bone.use_deform = False
                breast_bone.layers = [False]*1+[True]+[False]*30
                            
        bpy.ops.object.mode_set(mode='POSE')
        for name in lower_twist_controls:
            p_bone = armature.pose.bones["PB" + name[2:]]
            p_bone.custom_shape = bpy.data.objects["B_Shape_Bracket"]
            p_bone.custom_shape_scale = 0.5
            p_bone.bone_group = armature.pose.bone_groups["Pivot Bones"]
            
        for name in breast_bones:
            p_bone = armature.pose.bones[name]
            if name.startswith("CB"):
                p_bone.bone_group = armature.pose.bone_groups["Control Bones"]
                p_bone.custom_shape = bpy.data.objects["B_Shape_Bracket"]
                p_bone.custom_shape_scale = 0.5
                driver = p_bone.bone.driver_add("hide")       
                var = driver.driver.variables.new()
                var.name = "Use_Female_Bones"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = armature
                var.targets[0].data_path = "JK_MMT.Character_props.Is_female"
                driver.driver.expression = "not Use_Female_Bones"
                if len(driver.modifiers) > 0:
                    driver.modifiers.remove(driver.modifiers[0])
            elif name.startswith("MB"):
                p_bone.bone_group = armature.pose.bone_groups["Mechanism Bones"]                     
            else:
                p_bone.bone_group = armature.pose.bone_groups["Deform Bones"]
                constraint = p_bone.constraints.new('COPY_TRANSFORMS')
                constraint.target = armature
                constraint.subtarget = "MB_" + name
                driver = p_bone.bone.driver_add("hide")       
                var = driver.driver.variables.new()
                var.name = "Hide_Deform_Bones"
                var.type = 'SINGLE_PROP'
                var.targets[0].id = armature
                var.targets[0].data_path = "JK_MMT.Hide_deform_bones"
                driver.driver.expression = "Hide_Deform_Bones"
                if len(driver.modifiers) > 0:
                    driver.modifiers.remove(driver.modifiers[0])
                
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE':
                    if mod.object == armature:                
                        obj.data.JK_MMT.Character_type = "MANNEQUIN"
                        obj.data.JK_MMT.Character_name = "Mr Mannequin"
                        obj.data.JK_MMT.Is_default = False
                        obj.data.JK_MMT.Is_female = False
                        break            
    
    armature["MMT Rig Version"] = 1.2
    if "_RNA_UI" not in armature.keys():
        armature["_RNA_UI"] = {}
    armature["_RNA_UI"].update({"MMT Rig Version" : {"min" : 1.2, "max" : 1.2, "soft_min" : 1.2, "soft_max" : 1.2, "description" : "Do not edit! The current MMT version of the rig"}})
