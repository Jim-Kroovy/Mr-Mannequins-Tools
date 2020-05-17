import bpy

from bl_ui.properties_constraint import ConstraintButtonsPanel

def Display_Bone_IK(box, armature, name, is_limb):
    control = armature.pose.bones[name]
    box.label(text="Inverse Kinematics: " + name)
    if is_limb:
        gizmo = armature.pose.bones["GB" + name[2:]]
        if "Copy Rotation" in control.constraints:
            copy_rot = control.constraints["Copy Rotation"]
        copy_scale = gizmo.constraints["Copy Scale"]
        limit_scale = gizmo.constraints["Limit Scale"]
        row = box.row()
        if "Copy Rotation" in control.constraints:
            row.prop(copy_rot, "mix_mode", text="")
        row.prop(control, "ik_stretch", text="Stretch")
        row = box.row()
        row.prop(copy_scale, "power")
        row.prop(limit_scale, "max_y", text="Max Y")
    row_top = box.row()
    col = row_top.column(align=True)
    row = col.row(align=True)
    row.prop(control, "lock_ik_x", text="")
    row.prop(control, "use_ik_limit_x", text="", icon='CON_ROTLIMIT')
    row = col.row(align=True)
    row.prop(control, "lock_ik_y", text="")
    row.prop(control, "use_ik_limit_y", text="", icon='CON_ROTLIMIT')
    row = col.row(align=True)
    row.prop(control, "lock_ik_z", text="")
    row.prop(control, "use_ik_limit_z", text="", icon='CON_ROTLIMIT')
    
    col = row_top.column(align=True)
    col.prop(control, "ik_stiffness_x", text="")
    col.prop(control, "ik_stiffness_y", text="")
    col.prop(control, "ik_stiffness_z", text="")
    
    col = row_top.column(align=True)
    row = col.row(align=True)
    row.prop(control, "ik_min_x", text="")
    row.prop(control, "ik_max_x", text="")
    row = col.row(align=True)
    row.prop(control, "ik_min_y", text="")
    row.prop(control, "ik_max_y", text="")
    row = col.row(align=True)
    row.prop(control, "ik_min_z", text="")
    row.prop(control, "ik_max_z", text="")

# rig options interace panel...            
class JK_PT_MMT_Rig_Options(bpy.types.Panel):    
    bl_label = "Options"
    bl_idname = "JK_PT_MMT_Rig_Options"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'posemode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = bpy.context.object
        MMT = armature.JK_MMT
        active_bone = bpy.context.active_pose_bone
        selected = bpy.context.selected_pose_bones
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE':
                if armature.JK_MMT.Rig_type == 'CUSTOM' or armature.JK_MMT.Rig_type == 'MANNEQUIN':
                    layout.prop(MMT, "Character_meshes") 
                    if active_bone != None:
                        layout.operator("jk.add_head_controls") 
                        layout.operator("jk.add_twist_controls")
                        layout.operator("jk.add_digit_controls")
                        layout.operator("jk.add_ik_chain")
                    
                    for chain in armature.JK_MMT.IK_chain_data:
                        bone_data = chain.Chain_data
                        end_data = chain.End_data
                        name_list = [chain.name, end_data.name, bone_data.name, bone_data.Control, bone_data.Control_local, bone_data.Control_root, bone_data.Pole, bone_data.Pole_local, bone_data.Pole_root]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            row = box.row()
                            row.label(text="IK chain at: " + chain.name)
                            row.operator("jk.remove_ik_chain").Name = chain.name
                            box.prop_search(bone_data, "Root", armature.pose, "bones")
                            if bone_data.Root != "":
                                box.prop(chain, "IK_parenting")
                            box.prop(chain, "IKvsFK_limbs")
                            #first_rot = armature.pose.bones[chain.name].constraints["Copy Rotation"]
                            #second_rot = armature.pose.bones[bone_data.name].constraints["Copy Rotation"]
                            #row.prop(first_rot, "mix_mode")
                            #row.prop(second_rot, "mix_mode")
                            if chain.Chain_type == 'LEG':
                                if chain.End_data.Pivot == "":
                                    box.operator("jk.add_ankle_controls").Name = chain.name
                                else:
                                    box.operator("jk.remove_ankle_controls").Name = chain.name
                    
                    for twist in armature.JK_MMT.Twist_bone_data:
                        name_list = [twist.name, twist.Target, "PB" + twist.name[2:] if twist.Has_pivot else ""]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            box.label(text="Twist rigging at: " + twist.name)
                            box.operator("jk.remove_twist_controls").Name = twist.name

                    for head in armature.JK_MMT.Head_tracking_data:
                        name_list = [head.name, head.Target, head.Stretch, head.Neck, head.Spine]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            box.label(text="Head tracking at: " + head.name)
                            box.operator("jk.remove_head_controls").Name = head.name
                        
                    for digit in armature.JK_MMT.Digit_bone_data:
                        name_list = [digit.name, digit.Proximal, digit.Medial, digit.Distal, "AT_" + digit.Distal[2:] if digit.IKvsFK == 'OFFSET' else ""]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            box.label(text="Digit controls at: " + digit.name)
                            box.prop(digit, "IKvsFK")
                            box.operator("jk.remove_digit_controls").Name = digit.name
               
                elif armature.JK_MMT.Rig_type == 'GUN':
                    layout.label(text="Sorry no gun options... yet!")
                elif armature.JK_MMT.Rig_type == 'BOW':
                    layout.label(text="Sorry no bow options... yet!")
                elif armature.JK_MMT.Rig_type == 'TEMPLATE': 
                    if armature.JK_MMT.Retarget_target != "":
                        target = bpy.data.objects[armature.JK_MMT.Retarget_target]
                    layout.operator("jk.c_retargetrig", text=("Apply Controls"))
                    for bone in bpy.context.selected_pose_bones:
                        for data in MMT.Retarget_data:
                            if bone.name == data.Control_name:
                                box = layout.box()
                                box.label(text=bone.name)
                                row = box.row()
                                row.prop(data, "Retarget_type", text="")
                                if data.Retarget_type != 'NONE':
                                    row.prop_search(data, "Subtarget", target.data, "bones")
                                op = row.operator("jk.retarget_type", text="", icon='FILE_REFRESH')
                                op.Control = data.Control_name
                                op.Deform = data.name
                                op.Retarget_type = data.Retarget_type
                                op.Subtarget = data.Subtarget
                                row = box.row()
                                row.prop(bone.bone, "use_inherit_rotation")
                                row.prop(bone.bone, "inherit_scale")
                                row = box.row()
                                row.prop(bone, "custom_shape", text="Shape:")
                                row.prop(bone, "custom_shape_scale", text="Scale:")  
                elif armature.JK_MMT.Rig_type == 'NONE':
                    layout.operator("jk.c_retargetrig", text=("Build Controls"))
                else:
                    layout.label(text="Please select a Mr Mannequin rig for options")
            else:
                layout.label(text="Please select a Mr Mannequin rig for options")
        else:
            layout.label(text="Please select a Mr Mannequin rig for options")
                
# rig options interface panel...            
class JK_PT_MMT_Rig_Controls(bpy.types.Panel):    
    bl_label = "Controls"
    bl_idname = "JK_PT_MMT_Rig_Controls"
    bl_space_type = 'VIEW_3D'    
    bl_context= 'posemode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = bpy.context.object
        MMT = armature.JK_MMT
        if armature != None and len(bpy.context.selected_objects) > 0:
            selected = bpy.context.selected_pose_bones
            if armature.type == 'ARMATURE':
                row = layout.row()
                # if it's a mannequin or custom rig...
                if MMT.Rig_type == 'MANNEQUIN' or MMT.Rig_type == 'CUSTOM':
                    row.prop(MMT, 'Hide_deform_bones', icon=('HIDE_ON' if MMT.Hide_deform_bones else 'HIDE_OFF'))
                    row.prop(MMT, 'Mute_default_constraints', icon=('HIDE_ON' if MMT.Mute_default_constraints else 'HIDE_OFF'))
                    for head in MMT.Head_tracking_data:
                        name_list = [head.name, head.Target, head.Stretch, head.Neck, head.Spine]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            box.label(text="Head tracking for: " + head.name)
                            for bone in [head.name, head.Neck, head.Spine]:
                                p_bone = armature.pose.bones[bone]
                                box1 = box.box()
                                for constraint in p_bone.constraints:
                                    con = box1.template_constraint(constraint)
                                    if con:
                                        getattr(ConstraintButtonsPanel, constraint.type)(ConstraintButtonsPanel, context, con, constraint)
                                    box1.prop(constraint, "influence") 
                                    if constraint.type == 'IK':
                                        Display_Bone_IK(box1, armature, bone, False)

                    for chain in MMT.IK_chain_data:
                        end_data = chain.End_data
                        bone_data = chain.Chain_data
                        name_list = [chain.name, end_data.name, bone_data.name, bone_data.Control, bone_data.Control_root, bone_data.Pole, bone_data.Pole_root]
                        if any(bone.name in name_list for bone in selected):
                            p_bone = armature.pose.bones[chain.name]
                            
                            box = layout.box()
                            box.label(text="IK chain at: " + chain.name)
                            if chain.IKvsFK_limbs == 'SWITCHABLE':
                                box.prop(chain, 'Chain_use_fk', text="Use FK")
                            if chain.IK_parenting == 'SWITCHABLE':
                                box.prop(chain, 'Chain_use_parent', text="Use Parent")
                            row = box.row()
                            
                            row.prop(chain, 'Chain_ik_influence', text="Influence")
                            row.prop(chain, 'Chain_pole_angle', text="Pole Angle")
                            Display_Bone_IK(box, armature, chain.name, True)
                            Display_Bone_IK(box, armature, bone_data.name, True)

                    for twist in MMT.Twist_bone_data:
                        p_bone = armature.pose.bones[twist.name]
                        name_list = [twist.name, twist.Parent, twist.Target]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            box.label(text="Twist controls at: " + twist.name)
                            for constraint in p_bone.constraints:
                                con = box.template_constraint(constraint)
                                if con:
                                    getattr(ConstraintButtonsPanel, constraint.type)(ConstraintButtonsPanel, context, con, constraint)
                                box.prop(constraint, "influence")
                            if twist.Type == 'TAIL_FOLLOW':
                                Display_Bone_IK(box, armature, twist.name, False)

                    for digit in MMT.Digit_bone_data:
                        name_list = [digit.name, digit.Proximal, digit.Medial, digit.Distal, "DT" + digit.name[2:]]
                        if any(bone.name in name_list for bone in selected):
                            box = layout.box()
                            box.label(text="Digit controlled by: " + digit.name)
                            for name in [digit.Proximal, digit.Medial, digit.Distal]:
                                box1 = box.box()
                                box1.label(text=name)
                                p_bone = armature.pose.bones[name]
                                for constraint in p_bone.constraints:
                                    con = box1.template_constraint(constraint)
                                    if con:
                                        getattr(ConstraintButtonsPanel, constraint.type)(ConstraintButtonsPanel, context, con, constraint)
                                    box1.prop(constraint, "influence")
                
                # if it's a gun rig...
                elif MMT.Rig_type == 'GUN':
                    row.prop(MMT, 'Hide_deform_bones', icon=('HIDE_ON' if MMT.Hide_deform_bones else 'HIDE_OFF'))
                    row.prop(MMT, 'Mute_default_constraints', icon=('HIDE_ON' if MMT.Mute_default_constraints else 'HIDE_OFF'))
                    layout.prop(armature.pose.bones["CB_Trigger_Bone"].constraints["Limit Rotation"], 'influence', text="Trigger - Limit Rotation")
                    layout.prop(armature.pose.bones["CB_Slide_Bone"].constraints["Limit Location"], 'influence', text="Slide - Limit Location")
                    layout.prop(armature.pose.bones["CB_Ammo"].constraints["Limit Location"], 'influence', text="Ammo - Limit Location") 
                # if it's a bow rig...
                elif MMT.Rig_type == 'BOW':
                    row.prop(MMT, 'Hide_deform_bones', icon=('HIDE_ON' if MMT.Hide_deform_bones else 'HIDE_OFF'))
                    row.prop(MMT, 'Mute_default_constraints', icon=('HIDE_ON' if MMT.Mute_default_constraints else 'HIDE_OFF'))
                # if it's a template rig...
                elif MMT.Rig_type == 'TEMPLATE':
                    for bone in bpy.context.selected_pose_bones:
                        box = layout.box()
                        box.label(text=bone.name)
                        for constraint in bone.constraints:
                            con = box.template_constraint(constraint)
                            if con:
                                getattr(ConstraintButtonsPanel, constraint.type)(ConstraintButtonsPanel, context, con, constraint)
                else:
                    layout.label(text="No controls to display...")
            else:
                layout.label(text="Please select an armature for controls")
        else:
            layout.label(text="Please select a armature for controls")