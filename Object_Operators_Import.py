import bpy
import os
from bpy.props import (StringProperty, BoolProperty)
from . import (Pose_Functions_Retarget, Base_Functions)

class JK_OT_Import_Add_Settings(bpy.types.Operator):
    """Add custom import settings"""
    bl_idname = "jk.import_add_settings"
    bl_label = "Add Custom"

    Name: StringProperty(
        name="Name",
        description="The name of the import settings",
        default="",
        )
    
    def execute(self, context):
        MMT = bpy.context.scene.JK_MMT
        if self.Name not in MMT.Import_props:
            i_new_props = MMT.Import_props.add()
            i_new_props.name = self.Name
            # if we have some active propeties when we create a new entry...
            if MMT.Import_active in MMT.Import_props:
                # get the current props...
                i_current_props = MMT.Import_props[MMT.Import_active]
                # iterate through the RNA properties...
                for prop in i_new_props.bl_rna.properties:
                    # if the property is not the name or RNA type...
                    if prop.identifier not in ["rna_type", "name", "Animation_fbxs", "Mesh_fbxs"]:
                        # set the new property to the current property... (there might be a better way to do this but i like my sneaky exec() trick)
                        exec("i_new_props." + prop.identifier + " = i_current_props." + prop.identifier)
            MMT.Import_active = self.Name
        else:
            print(self.Name, "is already being used to label import settings!")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "Name")

class JK_OT_Import_Remove_Settings(bpy.types.Operator):
    """Remove custom import settings"""
    bl_idname = "jk.import_remove_settings"
    bl_label = "Remove Custom"

    Name: StringProperty(
        name="Name",
        description="The name of the import settings",
        default="",
        )
    
    def execute(self, context):
        MMT = bpy.context.scene.JK_MMT
        MMT.Import_props.remove(MMT.Import_props.find(self.Name))
        MMT.Import_active = "Default"
        return {'FINISHED'}

class JK_OT_Import_Mesh_FBX(bpy.types.Operator):
    """Imports mesh and skeleton animations with the selected mesh import settings"""
    bl_idname = "jk.import_mesh_fbx"
    bl_label = "Import FBX"

    Name: StringProperty(
        name="Name",
        description="The name of the animation fbx",
        default="",
        )

    Remove: BoolProperty(
        name="Remove",
        description="Remove everything that isn't a mesh after import process",
        default=False,
        )

    def execute(self, context):
        name = self.Name
        scene = context.scene
        MMT = scene.JK_MMT.Import_props[scene.JK_MMT.Import_active]
        target = bpy.context.object
        # import the .fbx without animation and apply everything...    
        Base_Functions.Import_FBX(os.path.join(bpy.path.abspath(MMT.Path_meshes), name), MMT, False)
        # once imported all new objects will be selected so save a reference to them...
        new_objects = bpy.context.selected_objects                  
        # we will need to find the armature...
        new_armature = None
        # for each new object...
        for obj in bpy.context.selected_objects:
            # if it's a mesh remove it from new objects... 
            if obj.type == 'MESH':
                new_objects.remove(obj)
                # iterate through modifiers...
                for modifier in obj.modifiers:
                    # if the modifier is an armature one...
                    if modifier.type == 'ARMATURE':
                        # assign the new armature if it hasn't been assigned...
                        if new_armature == None:
                            new_armature = modifier.object
                            # if we want to add a root bone...
                            if MMT.Add_root:
                                # hop into edit mode because...
                                bpy.ops.object.mode_set(mode='EDIT')
                                # when importing most fbxs exported from UE4 the root bone gets turned into the armature object... (sort of)
                                if new_armature.name not in new_armature.data.edit_bones:
                                    root = new_armature.data.edit_bones.new(new_armature.name)
                                    root.head = [0, 0, 0]
                                    root.tail = [0, 0.23196600377559662, 0]
                                    root.matrix = new_armature.matrix_world.inverted()
                                    root.roll = 0
                                    no_parents = [bone for bone in new_armature.data.edit_bones if bone.parent == None]
                                    for e_bone in no_parents:
                                        e_bone.parent = root
                                # then go back to object mode...
                                bpy.ops.object.mode_set(mode='OBJECT')
                        # if the modifiers target object is the new armature...
                        if modifier.object == new_armature:
                            # make sure the modifier is named to default...
                            modifier.name = "Armature"
        # apply the scale and rotation... (TEST SOME ROTATION THINGS!!!)
        bpy.ops.object.transform_apply(location=MMT.Apply_location, rotation=MMT.Apply_rotation, scale=MMT.Apply_scale)
        # clean up anything we don't want to keep...    
        if MMT.Clean_up:
            for obj in new_objects:
                if obj != new_armature:        
                    bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}

class JK_OT_Import_Anim_FBX(bpy.types.Operator):
    """Imports animation .FBX files with the selected animation import options"""
    bl_idname = "jk.import_anim_fbx"
    bl_label = "Import FBX"

    Name: StringProperty(
        name="Name",
        description="The name of the animation fbx",
        default="",
        )

    Remove: BoolProperty(
        name="Remove",
        description="Clean up after importing and converting?",
        default=False,
        )

    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT.Import_props[scene.JK_MMT.Import_active]
        active = bpy.context.object
        # get the render FPS before importing...
        pre_import_fps = scene.render.fps
        # import the fbx...
        if MMT.Use_most_host and 'ue4curves' in bpy.context.preferences.addons.keys():
            Base_Functions.Import_FBX_Anim_Most_Host(os.path.join(bpy.path.abspath(MMT.Path_animations), self.Name), MMT)
        else:
            Base_Functions.Import_FBX(os.path.join(bpy.path.abspath(MMT.Path_animations), self.Name), MMT, True)                  
        # once imported all new objects will be selected so save a reference to them...
        new_objects = bpy.context.selected_objects
        # get the render FPS after importing...
        post_import_fps = bpy.context.scene.render.fps
        # get a reference to the imported armature... (There shouldn't be more than one armature, if there is get the first one with animation data)            
        anim_armature = None
        for obj in bpy.context.selected_objects:
            if obj.type == 'ARMATURE' and obj.animation_data:
                anim_armature = obj
                break    
        # if an armature was imported...
        if anim_armature != None:
             # and it has animation data...
            if anim_armature.animation_data != None:
                # get the active action...
                action = anim_armature.animation_data.action
                # import a copy of the animation armature with no animation...
                Base_Functions.Import_FBX(os.path.join(bpy.path.abspath(MMT.Path_animations), self.Name), MMT, False)
                t_armature = None
                for obj in bpy.context.selected_objects:
                    if obj.type == 'ARMATURE':
                        t_armature = obj
                        break
                new_objects = new_objects + bpy.context.selected_objects
                # if we want to add a root bone...
                if MMT.Add_root:
                    # hop into edit mode...
                    bpy.ops.object.mode_set(mode='EDIT')
                    # add a root bone named after the armature...
                    if anim_armature.name not in t_armature.data.edit_bones:
                        root = t_armature.data.edit_bones.new(anim_armature.name)
                        root.head = [0, 0, 0]
                        root.tail = [0, 0.23196600377559662, 0]
                        root.matrix = t_armature.matrix_world.inverted()
                        root.roll = 0
                        no_parents = [bone for bone in t_armature.data.edit_bones if bone.parent == None]
                        for e_bone in no_parents:
                            e_bone.parent = root    
                    # return to object mode...
                    bpy.ops.object.mode_set(mode='OBJECT')
                    # check for any animation data on the armature object...
                    if any(curve.data_path in ["location", "rotation_quaternion", "rotation_euler", "scale"] for curve in action.fcurves):
                        Pose_Functions_Retarget.Set_Object_Keys_To_Root(anim_armature, t_armature, anim_armature.name)
                else:
                    for curve in action.fcurves:
                        if curve.data_path in ["location", "rotation_quaternion", "rotation_euler", "scale"]:
                            action.fcurves.remove(curve)
                    if t_armature.animation_data is None:
                            t_armature.animation_data_create()
                    t_armature.animation_data.action = action
                # if want to apply the scaling to an armature with animation...
                if MMT.Apply_scale:
                    # scale the animation by the armatures scale...
                    bpy.ops.jk.scale_anim(Action=t_armature.animation_data.action.name, Reverse=True)
                # then apply any transforms we want to apply...
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.transform_apply(location=MMT.Apply_location, rotation=MMT.Apply_rotation, scale=MMT.Apply_scale)
                bpy.ops.object.mode_set(mode='POSE')
                # scale keyframes to our framerate...
                bpy.ops.jk.scale_keyframes(Start=pre_import_fps, End=post_import_fps, Offset=MMT.Frame_offset)
                # if we want to retarget...
                if MMT.Anim_to_active: 
                    # try and retarget the animation to the active armature...
                    Pose_Functions_Retarget.Anim_Retarget_By_Curve(t_armature, active, self.Name[:-4], MMT.Clean_up)
                # if we aren't retargeting remove the target armature from the clean up list...
                else:
                    new_objects.remove(t_armature)
            # if there was no animation data let us know...
            else:
                print("No animation data imported!")
        # if there was no anim armature let us know...
        else:
            print("No animation armature imported!")
        # if we want to clean up imported armatures and meshes...
        if MMT.Clean_up:
            # clean up anything we don't want to keep...    
            for obj in new_objects:       
                bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}

# FBX import operator...       
class JK_OT_Import_FBX(bpy.types.Operator):
    """Imports FBX(s) with the chosen import options"""
    bl_idname = "jk.i_fbx"
    bl_label = "Import FBX"

    def execute(self, context):
        # need to be able to save the .blend...
        if bpy.data.is_saved:
            # save everything just incase we crash...
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            scene = context.scene
            MMT = scene.JK_MMT.Import_props[scene.JK_MMT.Import_active]
            target = bpy.context.object
            # if we want to import meshes...        
            if MMT.Meshes:
                # if batch importing...
                if MMT.Batch_meshes:
                    # for each file in the import folder...
                    for name in os.listdir(bpy.path.abspath(MMT.Path_meshes)):
                        # if the file is an FBX...
                        if name.upper().endswith(".FBX"):
                            bpy.ops.jk.import_mesh_fbx(Name=name, Remove=False)
                else:
                    bpy.ops.jk.import_mesh_fbx(Name=bpy.path.basename(MMT.Mesh_fbxs), Remove=False)
            # if we want to import animations...
            if MMT.Animations:
                # if batch importing...
                if MMT.Batch_animations:
                    # for each file in the import folder...
                    for name in os.listdir(bpy.path.abspath(MMT.Path_animations)):
                        # if the file is an FBX...
                        if name.upper().endswith(".FBX"):
                            bpy.ops.jk.import_anim_fbx(Name=name, Remove=False)
                else:
                    bpy.ops.jk.import_anim_fbx(Name=bpy.path.basename(MMT.Animation_fbxs), Remove=False)           
        # tell the user they need to save if they haven't already...
        else:
            Base_Functions.Show_Message(message = "Unable to save unsaved .blend, import requires you to of saved at least once", title = "Import Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, import requires you to of saved at least once")
        
        return {'FINISHED'}


        


