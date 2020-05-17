import bpy
import os
from bpy.props import (FloatVectorProperty, StringProperty)
from . import Base_Functions

class JK_OT_Export_Add_Settings(bpy.types.Operator):
    """Add custom export settings"""
    bl_idname = "jk.export_add_settings"
    bl_label = "Add Custom"

    Name: StringProperty(
        name="Name",
        description="The name of the export settings",
        default="",
        )
    
    def execute(self, context):
        MMT = bpy.context.scene.JK_MMT
        if self.Name not in MMT.Export_props:
            e_new_props = MMT.Export_props.add()
            e_new_props.name = self.Name
            # if we have some active propeties when we create a new entry...
            if MMT.Export_active in MMT.Export_props:
                # get the current props...
                e_current_props = MMT.Export_props[MMT.Export_active]
                # iterate through the RNA properties...
                for prop in e_new_props.bl_rna.properties:
                    # if the property is not the name or RNA type...
                    if prop.identifier not in ["rna_type", "name", "Animation_fbxs", "Mesh_fbxs"]:
                        #print(prop.identifier)
                        # set the new property to the current property... (there might be a better way to do this but i like my sneaky exec() trick)
                        exec("e_new_props." + prop.identifier + " = e_current_props." + prop.identifier)
            MMT.Export_active = self.Name
        else:
            print(self.Name, "is already being used to label export settings!")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "Name")

class JK_OT_Export_Remove_Settings(bpy.types.Operator):
    """Remove custom export settings"""
    bl_idname = "jk.export_remove_settings"
    bl_label = "Remove Custom"

    Name: StringProperty(
        name="Name",
        description="The name of the import settings",
        default="",
        )
    
    def execute(self, context):
        MMT = bpy.context.scene.JK_MMT
        MMT.Export_props.remove(MMT.Export_props.find(self.Name))
        MMT.Export_active = "Default"
        return {'FINISHED'}

class JK_OT_Export_Mesh_FBX(bpy.types.Operator):
    """Exports mesh and skeleton .FBX files with the selected animation export settings"""
    bl_idname = "jk.export_mesh_fbx"
    bl_label = "Export FBX"

    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT.Export_props[scene.JK_MMT.Export_active]
        active = bpy.context.object
        selected = bpy.context.selected_objects
        # set object scale for export...
        bpy.ops.jk.scale_selected(Scaled=MMT.Animations)
        # iterate over selected objects...
        for obj in selected:
            print(obj.name)
            # only deselect if batch exporting meshes...
            if MMT.Batch_meshes:
                # deselect everything each loop so everything stays seperate...
                bpy.ops.object.select_all(action='DESELECT')
            else:
                # or reselect them after scaling operator has changed selection...
                for mesh in selected:
                    mesh.select_set(True)
            # if an object has any armature modifiers...
            if any(mod.type == 'ARMATURE' for mod in obj.modifiers) and obj.type == 'MESH':
                # select only the object...
                obj.select_set(True)
                # get the armature from the modifier...
                T = obj.modifiers['Armature'].object
                # select the armature target so it gets exported with the object...           
                T.select_set(True)
                # save armatures name...
                T_name = T.name
                # if there is more than one armature modifier then only one will not generate an extra root bone...
                T.name = 'Armature'
                # set object to active... (might not be necessery??)
                bpy.context.view_layer.objects.active = obj 
                if not active.JK_MMT.Character_props.Is_female:
                    if "breast_l" in obj.vertex_groups: 
                        obj.vertex_groups.remove(obj.vertex_groups["breast_l"])
                    if "breast_r" in obj.vertex_groups:
                        obj.vertex_groups.remove(obj.vertex_groups["breast_r"])
                # assemble the filepath/name...
                if MMT.Batch_meshes:
                    path = os.path.join(bpy.path.abspath(MMT.Path_meshes), obj.name + ".FBX")
                else:
                    path = os.path.join(bpy.path.abspath(MMT.Path_meshes), T_name + "_" + str(len(selected) - 1) + ".FBX")
                # export without animation...
                Base_Functions.Export_FBX(path, MMT, False)
                # after object has been exported return armature name...
                T.name = T_name
                # break if not batch exporting meshes...
                if not MMT.Batch_meshes:
                    break
            else:
                if obj.type != 'ARMATURE':
                    if obj.type == 'MESH':
                        print(obj.name + " does not have the correct armature modifier!")
                    else:
                        print(obj.name + " is a " + obj.type + " not a MESH!")    
        # once batch has been exported reselect the original selection...
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
        return {'FINISHED'}

class JK_OT_Export_Anim_FBX(bpy.types.Operator):
    """Exports animation .FBX files with the selected animation export settings"""
    bl_idname = "jk.export_anim_fbx"
    bl_label = "Export FBX"

    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT.Export_props[scene.JK_MMT.Export_active]
        armature = bpy.context.view_layer.objects.active
        selected = bpy.context.selected_objects
        if armature.animation_data:
            if armature.animation_data.action:
                actions = []
                # save reference to armature layers...
                layers = armature.data.layers[:]
                # show all armature layers, we need them all open to prepare animations for export...
                armature.data.layers = [True]*32
                # deselect everything to make sure the armature stays seperate...
                bpy.ops.object.select_all(action='DESELECT')
                # select only the armature...
                armature.select_set(True)
                # save armatures name...
                A_name = armature.name
                # rename armature for export to avoid the extra root bone being created when importing to UE4...
                armature.name = "Armature"
                # hop into pose mode...
                bpy.ops.object.mode_set(mode='POSE')
                # unhide anything that's hidden...
                bpy.ops.pose.reveal(select=False)
                # get all the deform bones...
                deform_bones = [bone for bone in armature.pose.bones if bone.bone.use_deform]
                # if we want to export each animation to its own FBX...
                if MMT.Batch_animations:
                    # get name references for all pose bones...
                    bone_names = [bone.name for bone in armature.pose.bones]
                    # check every action in the blend...
                    for action in bpy.data.actions:
                        # if the action could be used by any bones in the armature...
                        if any(name in fcurve.data_path for fcurve in action.fcurves for name in bone_names):
                            armature.animation_data.action = action
                            # if we want to pre-bake the action...
                            if MMT.Bake_deforms:
                                bpy.ops.pose.select_all(action='DESELECT')
                                for p_bone in deform_bones:
                                    p_bone.bone.select = True
                                # bake everything to the deform bones...
                                bpy.ops.nla.bake(frame_start=action.frame_range[0], frame_end=action.frame_range[1], step=MMT.Bake_step, only_selected=True, 
                                    visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
                            # scale all the keyframes...
                            bpy.ops.jk.scale_anim(Action=action.name)
                            # append the action to the action list...
                            actions.append(action)        
                # if we aren't batch exporting...            
                else:
                    # get the active action...
                    action = armature.animation_data.action
                    # if we want to pre-bake the action...
                    if MMT.Bake_deforms:
                        bpy.ops.pose.select_all(action='DESELECT')
                        for p_bone in deform_bones:
                            p_bone.bone.select = True
                        # bake everything to the deform bones...
                        bpy.ops.nla.bake(frame_start=action.frame_range[0], frame_end=action.frame_range[1], step=MMT.Bake_step, only_selected=True, 
                            visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
                    # scale all the keyframes...
                    bpy.ops.jk.scale_anim(Action=action.name)
                    # append the action to the action list...
                    actions.append(action)
                # if we pre-baked the deform bones...
                if MMT.Bake_deforms:
                    # clear all constraints...
                    bpy.ops.pose.select_all(action='SELECT')
                    bpy.ops.pose.constraints_clear()
                # back to object mode...
                bpy.ops.object.mode_set(mode='OBJECT')
                # set armature scale for export...
                bpy.ops.jk.scale_selected(Scaled=False)
                # for each action...
                for action in actions:
                    # set it be the active one...
                    armature.animation_data.action = action
                    # prepare it for export...
                    bpy.ops.jk.prep_anim(Action=action.name)
                    # assemble the filepath/name...
                    path = os.path.join(bpy.path.abspath(MMT.Path_animations), A_name + "_" + action.name + ".FBX")
                    # export...
                    if MMT.Use_most_host and 'ue4curves' in bpy.context.preferences.addons.keys():
                        Base_Functions.Export_FBX_Anim_Most_Host(path, MMT)
                    else:
                        Base_Functions.Export_FBX(path, MMT, True)
                # after animation has been exported return armature name...
                armature.name = A_name                
                # and reselect the original selection...
                for obj in selected:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = armature
                armature.data.layers = layers
            else:
                Base_Functions.Show_Message(message = "No active action to export with the armature", title = "Export Error", icon = 'ERROR')
                print("No active action to export with the armature!")
        else:
            Base_Functions.Show_Message(message = "No animation data to export with the armature", title = "Export Error", icon = 'ERROR')
            print("No animation data to export with the armature!")
        return {'FINISHED'}

# FBX export operator...       
class JK_OT_Export_FBX(bpy.types.Operator):
    """Exports FBX(s) that are directly compatible with their source skeletons in UE4. No retargeting necessery!"""
    bl_idname = "jk.e_fbx"
    bl_label = "Export FBX"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT.Export_props[scene.JK_MMT.Export_active]
        armature = bpy.context.object
        # need to be able to save the .blend...
        if bpy.data.is_saved:
            # save everything...
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            # if there is an object named "Armature" ...
            if "Armature" in bpy.data.objects:
                # rename it so we can name any armature we are exporting correctly for UE4...
                bpy.data.objects["Armature"].name = bpy.context.active_object.name
            # if auto-keying is on it should be turned off...
            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            # if we want to export animation...
            if MMT.Animations:
                bpy.ops.jk.export_anim_fbx()
            # if we want to export meshes...
            if MMT.Meshes:
                bpy.ops.jk.export_mesh_fbx()
            # it's much easier to just reload the .blend after export than reversing the scaling, keyframing etc...
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
        # tell the user they need to save if they haven't already...
        else:
            Base_Functions.Show_Message(message = "Unable to save unsaved .blend, export requires you to of saved at least once", title = "Export Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, export requires you to of saved at least once")
        return {'FINISHED'}
