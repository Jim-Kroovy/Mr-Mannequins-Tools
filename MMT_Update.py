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