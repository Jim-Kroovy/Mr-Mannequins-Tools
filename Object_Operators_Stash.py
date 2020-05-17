import bpy
import os
import importlib
from . import (Object_Functions_Stash, Base_Functions)

# adds selected meshes to saved files...    
class JK_OT_Add_Stash(bpy.types.Operator):
    """Adds a stash folder to the selected location"""
    bl_idname = "jk.a_stash"
    bl_label = "Add Stash"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        prefs = context.preferences.addons["MrMannequinsTools"].preferences
        if os.path.exists(bpy.path.abspath(MMT.S_path_add)):
            if MMT.MMT_path not in bpy.path.abspath(MMT.S_path_add):
                if MMT.S_path_folder not in os.listdir(bpy.path.abspath(MMT.S_path_add)):
                    try:
                        os.mkdir(os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder))
                        prefs.S_paths.append((os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder), MMT.S_path_folder, os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder)))
                    except:
                        Base_Functions.Show_Message(message = "Unable to create folder here, check your folder/drive permissions or try running blender as administrator", title = "Write Error", icon = 'ERROR')
                        print("Unable to create folder here, check your folder/drive permissions or try running blender as administrator")
                else:
                    if MMT.S_path_folder not in [stash[1] for stash in prefs.S_paths]:
                        prefs.S_paths.append((os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder), MMT.S_path_folder, os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder)))
                    else:
                        Base_Functions.Show_Message(message = "Stash already exists", title = "Stash Error", icon = 'ERROR')
                        print("Stash already exists")
            else:
                Base_Functions.Show_Message(message = "Stash paths should not be in the add-ons folder! (updates could delete anything saved here)", title = "Stash Error", icon = 'ERROR')
                print("Stash paths should not be in the add-ons folder! (updates could delete anything saved here)")
        else:
            Base_Functions.Show_Message(message = "Path does not exist!", title = "Write Error", icon = 'ERROR')
            print("Path does not exist!")
    
        return {'FINISHED'}

#removes selected mesh from saved files... 
# not currently working properly... try/except still pulling os.remove permission error... 
class JK_OT_Remove_Stash(bpy.types.Operator):
    """Removes the selected mesh from current stash. Will not delete default meshes"""
    bl_idname = "jk.r_stash"
    bl_label = "Delete Stash"
        
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        if os.path.exists(MMT.S_path):
            try:
                os.remove(MMT.S_path)
            except:
                for stash in prefs.S_paths:
                    if stash[0] == MMT.S_path:
                        prefs.S_paths.remove(stash)
                        Base_Functions.Show_Message(message = stash[1] + " has been removed from stashes but the folder and library .blends must be deleted manually", title = "Stash Info", icon = 'INFO')
                        print(stash[1] + " has been removed from stashes but the folder and library .blends must be deleted manually")
        return {'FINISHED'}
        
# loads a saved mesh...
class JK_OT_Load_Mesh(bpy.types.Operator):
    """Loads the selected mesh from current stash"""
    bl_idname = "jk.l_mesh"
    bl_label = "Load Mesh"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        MMT.MMT_last_active = context.object.name
        unit_scale = scene.unit_settings.scale_length
        #name_start = (15 if "MANNEQUIN" in filename else 9)
        #obj_name = os.path.basename(MMT.L_meshes)[(15 if "MANNEQUIN" in MMT.L_meshes else 9):-6]
        obj_name = bpy.path.display_name_from_filepath(MMT.L_meshes)[(15 if "MANNEQUIN" in MMT.L_meshes else 9):]
        with bpy.data.libraries.load(MMT.L_meshes, link=False, relative=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name == obj_name]
            data_to.texts = [name for name in data_from.texts if name == obj_name + ".py"]

        for obj in data_to.objects:
            if obj is not None:
                # link the object to the current collection...
                bpy.context.collection.objects.link(obj)
                bpy.context.view_layer.objects.active = obj
                # reversed scaling: obj.scale = [obj.scale[0] * unit_scale, obj.scale[1] * unit_scale, obj.scale[2] * unit_scale]
                obj.scale = [obj.scale[0] * (1 / unit_scale), obj.scale[1] * (1 / unit_scale), obj.scale[2] * (1 / unit_scale)]
                if MMT.L_apply_scale_meshes:
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        for ref_text in data_to.texts:
            if ref_text is not None:
                # run and unlink the appended text...
                copy_text = bpy.context.copy()
                copy_text['edit_text'] = ref_text
                bpy.ops.text.run_script(copy_text)
                bpy.ops.text.unlink(copy_text)
        
        if bpy.data.is_saved:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
        else:
            Base_Functions.Show_Message(message = "Unable to save unsaved .blend, some data blocks with 0 users might not of been removed", title = "Save Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, some data blocks with 0 users might not of been removed")
        MMT.MMT_last_active = ""
        return {'FINISHED'}

# adds selected meshes to saved files...    
class JK_OT_Add_Mesh(bpy.types.Operator):
    """Adds viewport selected meshes to current stash if they have an armature modifier set to the active rig"""
    bl_idname = "jk.a_mesh"
    bl_label = "Stash Meshes"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        active = context.object
        MMT.MMT_last_active = active.name 
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                if any(mod.type == 'ARMATURE' and mod.object == active for mod in obj.modifiers):
                    importlib.reload(Object_Functions_Stash)
                    Object_Functions_Stash.Stash_Mesh(MMT, obj)
                else:
                    Base_Functions.Show_Message(message = obj.name + " does not have the correct armature modifier! (armature modifier must be targeting the active rig)", title = "Stash Error", icon = 'ERROR')
                    print(obj.name + " does not have the correct armature modifier! (armature modifier must be targeting the active rig)")
        MMT.MMT_last_active = "" 
        return {'FINISHED'}

# removes selected mesh from saved files...   
class JK_OT_Remove_Mesh(bpy.types.Operator):
    """Removes the selected mesh from current stash. Will not delete default meshes"""
    bl_idname = "jk.r_mesh"
    bl_label = "Remove Mesh"
        
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        if MMT.MMT_path not in MMT.L_meshes: 
            os.remove(MMT.L_meshes)
        return {'FINISHED'}

# loads a saved material...
class JK_OT_Load_Material(bpy.types.Operator):
    """Loads the selected material from current stash. Sets use_fake_user to stop it getting deleted during mesh loading"""
    bl_idname = "jk.l_material"
    bl_label = "Load Material"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        #mat_name = os.path.basename(MMT.L_materials)[9:-6]
        mat_name = bpy.path.display_name_from_filepath(MMT.L_materials)[9:]
        if mat_name not in bpy.data.materials:
            with bpy.data.libraries.load(MMT.L_materials, link=False, relative=False) as (data_from, data_to):
                data_to.materials = [name for name in data_from.materials if name == mat_name]
                data_to.texts = [name for name in data_from.texts if name == mat_name + ".py"]
            
            for material in data_to.materials:
                if material is not None:
                    # if loading a material set it to "use fake user" so it doesn't get deleted when next saving...
                    material.use_fake_user = True
            
            for ref_text in data_to.texts:
                if ref_text is not None:
                    # run and unlink the appended text...
                    copy_text = bpy.context.copy()
                    copy_text['edit_text'] = ref_text
                    bpy.ops.text.run_script(copy_text)
                    bpy.ops.text.unlink(copy_text)
            # dont really need to save the blend for material loading at the moment, i'm pretty sure all references are under control in the loading script...
            #if bpy.data.is_saved:
                #bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
                #bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
            #else:
                #print("Unable to save unsaved .blend, anything with 0 users has not been removed")
        else:
            Base_Functions.Show_Message(message = mat_name + " is already in bpy.data.materials, rename it then try again", title = "Stash Error", icon = 'ERROR')
            print(mat_name + " is already in bpy.data.materials, rename it then try again")
        return {'FINISHED'}    

# adds active materials to saved files...    
class JK_OT_Add_Material(bpy.types.Operator):
    """Adds active material on each viewport selected mesh to current stash"""
    bl_idname = "jk.a_material"
    bl_label = "Stash Materials"
    bl_options = {'PRESET'}
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                bpy.context.view_layer.objects.active = obj
                importlib.reload(Object_Functions_Stash)              
                Object_Functions_Stash.Stash_Material(MMT, obj.active_material)
        return {'FINISHED'}

# removes selected material from saved files...   
class JK_OT_Remove_Material(bpy.types.Operator):
    """Removes the selected material from current stash. Will not delete default materials"""
    bl_idname = "jk.r_material"
    bl_label = "Remove Material"
        
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        if MMT.MMT_path not in MMT.L_materials:
            os.remove(MMT.L_materials)
        return {'FINISHED'}

# loads a saved armature...        
class JK_OT_Load_Rig(bpy.types.Operator):
    """Loads the selected armature from default stash"""
    bl_idname = "jk.l_rig"
    bl_label = "Load Rig"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        unit_scale = scene.unit_settings.scale_length
        #rig_name = os.path.basename(MMT.L_rigs)[9:-6] - causing utf-8 errors on some systems??
        rig_name = bpy.path.display_name_from_filepath(MMT.L_rigs)[9:] # does the same thing but should be utf-8 compatible...
        with bpy.data.libraries.load(MMT.L_rigs, link=False, relative=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name == rig_name]
            data_to.texts = [name for name in data_from.texts if name == rig_name + ".py"]
        
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
                bpy.context.view_layer.objects.active = obj
                #obj.scale = [obj.scale[0] * unit_scale, obj.scale[1] * unit_scale, obj.scale[2] * unit_scale] - reversed scaling for saving?
                obj.scale = [obj.scale[0] * (1 / unit_scale), obj.scale[1] * (1 / unit_scale), obj.scale[2] * (1 / unit_scale)]
                if MMT.L_apply_scale_armatures:
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                
        for ref_text in data_to.texts:
            if ref_text is not None:
                # run and unlink the appended text...
                copy_text = bpy.context.copy()
                copy_text['edit_text'] = ref_text
                bpy.ops.text.run_script(copy_text)
                bpy.ops.text.unlink(copy_text)
        
        if bpy.data.is_saved:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
        else:
            Base_Functions.Show_Message(message = "Unable to save unsaved .blend, some data blocks with 0 users might not of been removed", title = "Save Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, some data blocks with 0 users might not of been removed")
        return {'FINISHED'}