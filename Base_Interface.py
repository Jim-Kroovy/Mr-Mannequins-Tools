import bpy

from . import (Pose_Functions_Mapping, Pose_Properties_Mapping, Pose_Properties_Retarget)

# add-on preferences... stores all the stash file paths, mapping and retargets between .blends...    
class JK_MMT_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "MrMannequinsTools"
    
    Dev_mode: bpy.props.BoolProperty(
        name="Dev Mode",
        description="Lets you change a few properties that you otherwise wouldn't be able to without using Python. WARNING! Use at your own risk! I will not be supporting issues caused by enabling this setting!",
        default = False
        )
    
    Show_pose_props: bpy.props.BoolProperty(
        name="Expand",
        description="Expose pose mode properties",
        default = False
        )

    Show_retargets: bpy.props.BoolProperty(
        name="Show Retargets",
        description="Show the retargets",
        default = False
        )

    Show_mapping: bpy.props.BoolProperty(
        name="Show Mapping",
        description="Show the mapping",
        default = False
        )

    # stores file string sets for stash enum...
    S_paths = []
    # the bone mapping being used across .blend files...
    Mapping: bpy.props.CollectionProperty(type=Pose_Properties_Mapping.JK_MMT_Part_Mapping)
    # the deault retargets + any user added ones...
    Retargets: bpy.props.CollectionProperty(type=Pose_Properties_Retarget.JK_MMT_Retarget_Dictionary)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        # mapping column...
        m_col = row.column()
        m_box = m_col.box()
        m_box.alignment = 'LEFT'
        m_row = m_box.row()
        m_row.alignment = 'LEFT'
        m_row.label(text="Bone Mapping")
        m_row.prop(self, "Show_mapping", text="", icon='DOWNARROW_HLT')
        m_row.operator("jk.clear_mapping", text="", icon='TRASH')
        m_row.operator("jk.add_mapping", text="", icon='COLLECTION_NEW').Indices = (-1, -1, -1)
        m_row.operator("jk.reset_mapping", text="", icon='FILE_REFRESH')
        m_row.operator("jk.write_mapping", text="", icon='TEXT')
        # retarget column...
        r_col = row.column()
        r_box = r_col.box()
        r_box.alignment = 'LEFT'
        r_row = r_box.row()
        r_row.alignment = 'LEFT'
        r_row.label(text="Saved Retargets")
        r_row.prop(self, "Show_retargets", text="", icon='DOWNARROW_HLT')
        r_row.operator("jk.clear_retargets", text="", icon='TRASH')
        r_row.operator("jk.add_retarget", text="", icon='COLLECTION_NEW').Retarget = ""
        r_row.operator("jk.reset_retargets", text="", icon='FILE_REFRESH')
        r_row.operator("jk.write_retargets", text="", icon='TEXT')
        # other settings column...
        d_col = row.column()
        d_box = d_col.box()
        d_box.alignment = 'LEFT'
        d_row = d_box.row()
        d_row.alignment = 'LEFT'
        d_row.label(text="Settings")
        # mapping display...
        if self.Show_mapping:
            for i1, part in enumerate(self.Mapping):
                box1 = m_box.box()
                box1.alignment = 'LEFT'
                b_row1 = box1.row()
                b_row1.alignment = 'LEFT'
                b_row1.prop(part, "Part", text="[" + str(i1) + "]")
                b_row1.prop(part, "First", text="")
                b_row1.prop(part, "Second", text="")
                b_row1.prop(part, "Show_joints", text="", icon='DOWNARROW_HLT')
                b_row1.operator("jk.remove_mapping", text="", icon='TRASH').Indices = (i1, -1, -1)
                b_row1.operator("jk.add_mapping", text="", icon='COLLECTION_NEW').Indices = (i1, -1, -1)
                if part.Show_joints:                                
                    for i2, joint in enumerate(part.Joints):
                        row2 = box1.row()
                        row2.alignment = 'LEFT'
                        row2.separator(factor=3)
                        box2 = row2.box()
                        box2.alignment = 'LEFT'
                        b_row2 = box2.row()
                        b_row2.alignment = 'LEFT'
                        b_row2.prop(joint, "Joint", text="[" + str(i1) + "][" + str(i2) + "]")
                        b_row2.prop(joint, "First", text="")
                        b_row2.prop(joint, "Second", text="")
                        b_row2.prop(joint, "Show_sections", text="", icon='DOWNARROW_HLT')
                        b_row2.operator("jk.remove_mapping", text="", icon='TRASH').Indices = (i1, i2, -1)
                        b_row2.operator("jk.add_mapping", text="", icon='COLLECTION_NEW').Indices = (i1, i2, -1)
                        if joint.Show_sections:
                            for i3, section in enumerate(joint.Sections):
                                row3 = box2.row()
                                row3.alignment = 'LEFT'
                                row3.separator(factor=3)
                                box3 = row3.box()
                                box3.alignment = 'LEFT'
                                b_row3 = box3.row()
                                b_row3.alignment = 'LEFT'
                                b_row3.label(text="[" + str(i1) + "][" + str(i2) + "][" + str(i3) + "]")
                                #b_row3.label(text=Get_Mapping_Name((i1, i2, i3), self.Mapping)) add in labels at some point?
                                b_row3.prop(section, "Section", text="")
                                b_row3.prop(section, "First", text="")
                                b_row3.prop(section, "Second", text="")    
                                b_row3.operator("jk.remove_mapping", text="", icon='TRASH').Indices = (i1, i2, i3) 
                            
        # retargets display...
        if self.Show_retargets:
            for retarget in self.Retargets:
                box = r_box.box()
                box.alignment = 'LEFT'
                row = box.row()
                row.alignment = 'LEFT'
                row.prop(retarget, "name", text="")
                row.prop(retarget, "Show_bones", text="", icon='DOWNARROW_HLT')
                r_r_op = row.operator("jk.remove_retarget", text="", icon='TRASH')
                r_r_op.Retarget = retarget.name
                r_r_op.Bone = ""
                r_a_op = row.operator("jk.add_retarget", text="", icon='COLLECTION_NEW')
                r_a_op.Retarget = retarget.name
                r_a_op.Bone = ""
                r_a_op.Parent = ""
                if retarget.Show_bones:                 
                    # get a list of all the bones without parents... (need a starting point to create a hierarchy)
                    parents = [bone.name for bone in retarget.Bones if bone.Parent == ""]
                    # iterate over it...
                    for parent in parents:
                        # get the retarget entry of the parent...
                        bone = retarget.Bones[parent]
                        # get parents direct children...
                        children = [child.name for child in retarget.Bones if child.Parent == bone.name]
                        # set up it's display...
                        row1 = box.row()
                        row1.alignment = 'LEFT'
                        box1 = row1.box()
                        box1.alignment = 'LEFT'
                        b_row = box1.row()
                        b_row.alignment = 'LEFT'
                        b_row.prop(bone, "name", text="")
                        b_row.prop(bone, "Indices", text="")
                        b_row.prop(bone, "Retarget", text="")
                        b_row.prop(bone, "Type", text="")
                        b_row.prop(bone, "Subtarget", text="")
                        # if this bone has any children...
                        if len(children) > 0:
                            # expose its show children property...
                            b_row.prop(bone, "Show_children", text="", icon='DOWNARROW_HLT')
                        b_r_op = b_row.operator("jk.remove_retarget", text="", icon='TRASH')
                        b_r_op.Retarget = retarget.name
                        b_r_op.Bone = bone.name
                        b_a_op = b_row.operator("jk.add_retarget", text="", icon='COLLECTION_NEW')
                        b_a_op.Retarget = retarget.name
                        b_a_op.Bone = ""
                        b_a_op.Parent = bone.name
                        # also if there are any children and the bones show children bool is true...
                        if len(children) > 0 and bone.Show_children:
                            # we should iterate over them...
                            i = 0
                            while i < len(children):
                                child = children[i]
                                i = i + 1
                                # get the retarget entry of the child...
                                bone = retarget.Bones[child]
                                # get the direct children of the child...
                                next_children = [child.name for child in retarget.Bones if child.Parent == bone.name]
                                # while loop through bones parenting to get indentation...
                                space = 1
                                if bone.Parent != "":
                                    iter = retarget.Bones[bone.Parent]
                                    while iter.Parent != "":
                                        space = space + 1
                                        iter = retarget.Bones[iter.Parent]
                                # set up it's display...
                                row1 = box.row()
                                row1.alignment = 'LEFT'
                                # set indentation...
                                for int in range(0, space):
                                #row1.label(text=space)
                                    row1.separator(factor=3)
                                box1 = row1.box()
                                box1.alignment = 'LEFT'
                                b_row = box1.row()
                                b_row.alignment = 'LEFT'
                                b_row.prop(bone, "name", text="")
                                b_row.prop(bone, "Indices", text="")
                                b_row.prop(bone, "Retarget", text="")
                                b_row.prop(bone, "Type", text="")
                                b_row.prop(bone, "Subtarget", text="")
                                # if this bone has any children...
                                if len(next_children) > 0:
                                    # expose its show children property...
                                    b_row.prop(bone, "Show_children", text="", icon='DOWNARROW_HLT')
                                # set up deletion operator...
                                b_r_op = b_row.operator("jk.remove_retarget", text="", icon='TRASH')
                                b_r_op.Retarget = retarget.name
                                b_r_op.Bone = bone.name
                                b_a_op = b_row.operator("jk.add_retarget", text="", icon='COLLECTION_NEW')
                                b_a_op.Retarget = retarget.name
                                b_a_op.Bone = ""
                                b_a_op.Parent = bone.name
                                # if the child is showing it's children... (and has any)
                                if bone.Show_children and len(next_children) > 0:
                                    # iterate over them backwards...
                                    next_children.reverse()
                                    for name in next_children:
                                        # and extend the list of parents children by inserting more names... (reversing and inserting at the next index to maintain order)
                                        children.insert(i, name)       
        # other settings display...
        box = d_box.box()
        box.alignment = 'LEFT'
        box.prop(self, "Dev_mode")

class JK_PT_MMT_Object(bpy.types.Panel):    
    bl_label = "Object Menu"
    bl_idname = "JK_PT_MMT_Object"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'objectmode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"    
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.unit_settings, "scale_length")
        layout.prop(scene.render, "fps")

class JK_PT_MMT_Pose(bpy.types.Panel):    
    bl_label = "Pose Menu"
    bl_idname = "JK_PT_MMT_Pose"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'posemode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"    
    
    def draw(self, context):
        layout = self.layout
        #scene = context.scene
        armature = bpy.context.object
        active_bone = bpy.context.active_pose_bone
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        layout.label(text="Display")
        box = layout.box()
        box.prop(armature, "display_type", text="Armature")
        box.prop(armature.data, "display_type", text="Bones")
        row = box.row()
        row.prop(armature.data, "show_bone_custom_shapes", text="Shapes")
        row.prop(armature.data, "show_axes", text="Axes")
        row.prop(armature, "show_in_front", text="In Front")
        
        if prefs.Dev_mode:
            layout.prop(armature.JK_MMT, "Rig_type")
            layout.prop(armature.JK_MMT, "Retarget_target")
            layout.prop(active_bone, "name")
            
            #layout.prop(prefs, "Show_pose_props")
        if armature.JK_MMT.Rig_type == 'TEMPLATE':
            target = bpy.data.objects[armature.JK_MMT.Retarget_target]
            layout.label(text="Target Display")
            box = layout.box()
            box.prop(target, "display_type", text="Armature")
            box.prop(target.data, "display_type", text="Bones")
        