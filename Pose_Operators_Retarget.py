import bpy
import os
import importlib

from . import (Base_Functions, Pose_Properties_Retarget, Pose_Functions_Retarget)

from bpy.props import (IntVectorProperty, IntProperty, StringProperty, BoolProperty, EnumProperty)

class JK_OT_Retarget_Force_Naming(bpy.types.Operator):
    """Sets deform and mechanism names to use names from a retarget"""
    bl_idname = "jk.force_retarget_names"
    bl_label = "Force Retarget Names"

    Retarget: StringProperty(
        name="Retarget",
        description="Name of the retarget to set naming from",
        default="",
        maxlen=1024,
        )

    def execute(self, context):
        armature = bpy.context.object
        retarget = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets[self.Retarget]
        if len(armature.JK_MMT.Retarget_data) > 0:
            MMT = armature.JK_MMT
            for bone in retarget.Bones:
                for data in MMT.Retarget_data:
                    if bone.Indices[:] == data.Mapping_indices[:]:
                        d_bone = armature.pose.bones[data.name]
                        m_bone = armature.pose.bones["MB_" + data.name]
                        d_bone.name = bone.name
                        m_bone.name = "MB_" + bone.name
                        data.name = bone.name

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        #row = layout.row()
        layout.prop_search(self, "Retarget", prefs, "Retargets")

class JK_OT_Retargets_Write(bpy.types.Operator):
    """Write current retargets to a text file"""
    bl_idname = "jk.write_retargets"
    bl_label = "Write"

    def execute(self, context):
        retargets = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets
        Pose_Functions_Retarget.Write_Retargets(retargets)
        return {'FINISHED'}

class JK_OT_Retargets_Reset(bpy.types.Operator):
    """Reset retargets to default"""
    bl_idname = "jk.reset_retargets"
    bl_label = "Reset"

    Retargets = Pose_Properties_Retarget.Default_retargets
    Clear = True

    def execute(self, context):
        retargets = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets
        Pose_Functions_Retarget.Set_New_Retargets(retargets, self.Retargets, self.Clear)
        return {'FINISHED'}

class JK_OT_Retargets_Clear(bpy.types.Operator):
    """Clear all retargets"""
    bl_idname = "jk.clear_retargets"
    bl_label = "Clear"

    def execute(self, context):
        bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets.clear() 
        return {'FINISHED'}

class JK_OT_Retargets_Add(bpy.types.Operator):
    """Add retarget entry"""
    bl_idname = "jk.add_retarget"
    bl_label = "Add"

    Retarget: StringProperty(
        name="Retarget",
        description="Name of the retarget to be added",
        default="",
        maxlen=1024,
        )

    Bone: StringProperty(
        name="Bone",
        description="Name of the bone to be added",
        default="",
        maxlen=1024,
        )

    Parent: StringProperty(
        name="Parent",
        description="Name of the parent bone to add to. (if any)",
        default="",
        maxlen=1024,
        )

    Indices: IntVectorProperty(
        name="Indices",
        description="Indices to map to the bones name",
        default=(-1, -1, -1),
        size=3,
        )

    def execute(self, context):
        retargets = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets
        if self.Retarget != "":
            if self.Bone in retargets[self.Retarget].Bones:
                Base_Functions.Show_Message(message = "Bones must have unique names!", title = "Name already exsists!", icon = 'ERROR')
            else:
                bone = retargets[self.Retarget].Bones.add()
                # if bone is added without a name set name from length of bones...
                bone.name = self.Bone if self.Bone != "" else "Bone " + str(len(retargets[self.Retarget].Bones))
                bone.Indices = self.Indices
                bone.Parent = self.Parent
        else:
            if self.Retarget in retargets:
                Base_Functions.Show_Message(message = "Retargets must have unique names!", title = "Name already exsists!", icon = 'ERROR')
            else:
                retarget = retargets.add()
                # if retarget is added without a name set name from length of retargets...
                retarget.name = self.Retarget if self.Retarget != "" else "Retarget " + str(len(retargets))
        return {'FINISHED'}

class JK_OT_Retargets_Remove(bpy.types.Operator):
    """Remove retargets entry"""
    bl_idname = "jk.remove_retarget"
    bl_label = "Remove"

    Retarget: StringProperty(
        name="Name",
        description="Name of the retarget to be removed",
        default="",
        maxlen=1024,
        )

    Bone: StringProperty(
        name="Name",
        description="Name of the bone or retarget to be removed",
        default="",
        maxlen=1024,
        )

    def execute(self, context):
        retargets = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets
        if self.Bone in retargets[self.Retarget].Bones:
            # need to remove any children first... (maybe make this an option?)
            children = [bone.name for bone in retargets[self.Retarget].Bones if bone.Parent == self.Bone]
            for name in children:
                retargets[self.Retarget].Bones.remove(retargets[self.Retarget].Bones.find(name))
            retargets[self.Retarget].Bones.remove(retargets[self.Retarget].Bones.find(self.Bone))
        else:
            retargets.remove(retargets.find(self.Retarget))
        return {'FINISHED'}


class JK_OT_Retarget_Save(bpy.types.Operator):
    """Adds retarget data from the active armature to either a new saved retarget or existing one. (already existing bones gets overwritten)"""
    bl_idname = "jk.save_retarget_data"
    bl_label = "Save Retarget Data"
    
    New: BoolProperty(
        name="New Retarget",
        description="Create new or use existing retarget",
        default = False
        )

    Selected: BoolProperty(
        name="Selected",
        description="Save only selected bones",
        default = False
        )

    Recursive: BoolProperty(
        name="Children",
        description="Also save recursive children of selected bones",
        default = False
        )

    Name: StringProperty(
        name="Name",
        description="Name of the retarget",
        default="",
        maxlen=1024,
        )
    # has issues with saving from selected (FIX AT SOME POINT!)
    def execute(self, context):
        retargets = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Retargets
        obj = bpy.context.object
        # if we are adding a new retarget...
        if self.New:
            retarget = retargets.add()
            retarget.name = self.Name if self.Name not in retargets else self.Name + "_" + str(len(retargets))
        else:
            retarget = retargets[self.Name]
        # if we only want to save selected bones...
        if self.Selected:
            # and if we want to save their children...
            if self.Recursive:
                for p_bone in bpy.context.selected_pose_bones:
                    for child in p_bone.children_recursive:
                        for data in obj.JK_MMT.Retarget_data:
                            if child.name == data.Control_name:
                                if data.name in retarget.Bones:
                                    bone = retarget.Bones[data.name]
                                else:
                                    bone = retarget.Bones.add()
                                    bone.name = data.name
                                d_bone = obj.pose.bones[data.name]
                                bone.Parent = d_bone.parent.name if d_bone.parent != None else ""
                                bone.Indices = data.Mapping_indices
                                bone.Retarget = data.Retarget_method
                                bone.Type = data.Retarget_type
                                bone.Subtarget = data.Subtarget
            # or if we only want to save selected...
            else:
                for p_bone in bpy.context.selected_pose_bones:
                    for data in obj.JK_MMT.Retarget_data:
                        if p_bone.name == data.Control_name:
                            if data.name in retarget.Bones:
                                bone = retarget.Bones[data.name]
                            else:
                                bone = retarget.Bones.add()
                                bone.name = data.name
                            d_bone = obj.pose.bones[data.name]
                            bone.Parent = d_bone.parent.name if d_bone.parent != None else ""
                            bone.Indices = data.Mapping_indices
                            bone.Retarget = data.Retarget_method
                            bone.Type = data.Retarget_type
                            bone.Subtarget = data.Subtarget
        # if we want to save all bones...
        else:
            for data in obj.JK_MMT.Retarget_data:
                if data.name in retarget.Bones:
                    bone = retarget.Bones[data.name]
                else:
                    bone = retarget.Bones.add()
                    bone.name = data.name
                d_bone = obj.pose.bones[data.name]
                bone.Parent = d_bone.parent.name if d_bone.parent != None else ""
                bone.Indices = data.Mapping_indices
                bone.Retarget = data.Retarget_method
                bone.Type = data.Retarget_type
                bone.Subtarget = data.Subtarget
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        layout = self.layout
        row = layout.row()
        row.prop(self, "New")
        if self.New:
            row.prop(self, "Name")
        else:
            row.prop_search(self, "Name", prefs, "Retargets")
        #layout.prop(self, "Selected")
        #if self.Selected:
            #layout.prop(self, "Recursive")

class JK_OT_Retarget_Rig(bpy.types.Operator):
    """Still a work in progress - please check the update video for how to use this!"""
    bl_idname = "jk.c_retargetrig"
    bl_label = "Retarget Rig"
    
    Template: EnumProperty(
        name="Template",
        description="Choose an existing template to create control bones or generate them. (any existing bones not in a template will be generated)",
        items=[('NONE', 'Generated', "Generated control bones from the existing armatures bones"),
        ('TEMPLATE_UE4_Mannequin', 'UE4 Mannequin', "Use Mr Mannequins control bones")],
        default='NONE'
        )
    
    Retarget: StringProperty(
        name="Retarget",
        description="Name of the retarget to use for ",
        default="",
        maxlen=1024,
        )

    def execute(self, context):
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        retarget = prefs.Retargets[self.Retarget] if self.Retarget != "" else None
        importlib.reload(Pose_Functions_Retarget)
        obj = bpy.context.object
        if bpy.context.object.JK_MMT.Rig_type == 'TEMPLATE':
            Pose_Functions_Retarget.Apply_Rig_Retargeting(bpy.data.objects[obj.JK_MMT.Retarget_target], obj, self.Template)
            # if we want to force the template pose...
            if self.Template != 'NONE':
                if obj.JK_MMT.Force_template_rotations or obj.JK_MMT.Force_template_locations:
                    Pose_Functions_Retarget.Force_Template_Pose(obj, self.Template, obj.JK_MMT.Force_template_rotations, obj.JK_MMT.Force_template_locations)
    
        else:
            Base_Functions.Get_Custom_Shapes(os.path.join(bpy.context.scene.JK_MMT.MMT_path, "MMT_Stash\\SHAPES_Default.blend"), bpy.context.scene.unit_settings.scale_length)   
            Pose_Functions_Retarget.Start_Rig_Retargeting(obj, self.Template, retarget)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        rig = bpy.context.object
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        layout = self.layout
        layout.prop(self, "Template")
        if rig.JK_MMT.Rig_type == 'TEMPLATE' and self.Template != 'NONE':
            layout.prop(rig.JK_MMT, 'Force_template_rotations')
            layout.prop(rig.JK_MMT, 'Force_template_locations')
        else:
            layout.prop_search(self, "Retarget", prefs, "Retargets")
        

class JK_OT_Retarget_Anim(bpy.types.Operator):
    """Retarget animation from the selected armature to the active armature"""
    bl_idname = "jk.retarget_anim"
    bl_label = "Retarget Animation"
    
    Remove: BoolProperty(
        name="Remove Action",
        description="Removes the source action after retargeting",
        default = False
        )

    Name: StringProperty(
        name="Name",
        description="The name of the new action",
        default="",
        maxlen=1024,
        )
    
    Source: StringProperty(
        name="Source",
        description="Source armature",
        default="",
        maxlen=1024,
        )
    
    Target: StringProperty(
        name="Target",
        description="Target armature",
        default="",
        maxlen=1024,
        )

    def execute(self, context):
        #scene = context.scene
        #MMT = scene.JK_MMT
        source = bpy.data.objects[self.Source]
        target = bpy.data.objects[self.Target]
        Pose_Functions_Retarget.Anim_Retarget_By_Curve(source, target, self.Name, self.Remove)
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = bpy.context.object
        selected = bpy.context.selected_objects
        self.Target = obj.name
        self.Source = selected[1].name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(self, "Name")
        layout.prop_search(self, "Source", scene, "objects")
        layout.prop_search(self, "Target", scene, "objects")
        layout.prop(self, "Remove")

    
class JK_OT_Retarget_Type(bpy.types.Operator):
    """Change the retargeting type of the selected bone"""
    bl_idname = "jk.retarget_type"
    bl_label = "Set Retarget Type"
    
    Control: StringProperty(
        name="Control",
        description="The name of the bone we are changing",
        default="",
        maxlen=1024,
        )

    Deform: StringProperty(
        name="Deform",
        description="The name of the bone that it deforms",
        default="",
        maxlen=1024,
        )
    
    Subtarget: StringProperty(
        name="Subtarget",
        description="Subtarget for new constraints",
        default="",
        maxlen=1024,
        )

    Retarget_type:  EnumProperty(
        name="Retarget Type",
        description="Sets the type for retargeting",
        items=[('NONE', 'Manual', "Manually assign rotation"),
        ('STRETCH', 'Stretch', "Stretches to target"),
        ('TWIST_HOLD', 'Twist Hold', "Holds back the Y rotation. (eg: Upper Arm Twist)"),
        ('TWIST_FOLLOW', 'Twist Follow', "Follows targets Y rotation. (eg: Lower Arm Twist)"),
        ('ROOT_COPY', 'Root Copy', "Copies world space rotation of it's parent"),
        ('IK_DEFAULT', 'IK Default', "Is an IK deform bone present in the default rig. (You will need to remove/set this bone up yourself)"),
        ('REMOVE', 'Remove', "Get rid of this bone when applying control bones")],
        default='NONE',
        )

    def execute(self, context):
        #scene = context.scene
        #MMT = scene.JK_MMT
        template = bpy.context.object
        armature = bpy.data.objects[template.JK_MMT.Retarget_target]
        target = template if self.Retarget_type in ['ROOT_COPY', 'TWIST_HOLD', 'TWIST_FOLLOW', 'IK_DEFAULT'] else armature
        subtarget = "CB_" + self.Subtarget if self.Retarget_type in ['ROOT_COPY', 'TWIST_HOLD', 'TWIST_FOLLOW', 'IK_DEFAULT'] else self.Subtarget
        Pose_Functions_Retarget.Set_Bone_Retarget_Type(armature, template, self.Control, self.Deform, target, subtarget, self.Retarget_type)
        return {'FINISHED'}

    #def invoke(self, context, event):
        #template = bpy.context.object
        #retarget = bpy.data.objects[template.JK_MMT.Retarget_target]
        #bone = bpy.context.active_pose_bone
        #wm = context.window_manager
        #return wm.invoke_props_dialog(self)

    #def draw(self, context):
        #layout = self.layout
        #scene = context.scene
        #template = bpy.context.object
        #target = bpy.data.objects[template.JK_MMT.Retarget_target]
        #layout.prop(self, 'Retarget_type')
        #layout.prop_search(self, "Control", template.pose, "bones")
        #if self.Retarget_type != 'NONE':
            #layout.prop(self, "Target")
            #layout.prop_search(self, "Subtarget", target.data if self.Target == 'TARGET' else template.data, "bones")
                
    