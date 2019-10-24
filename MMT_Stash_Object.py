import bpy
import os
import importlib
from . import MMT_Stash_Material

#---------- NOTES -----------------------------------------------------------------------------

# This script is a work in progress! currently only works on meshes and does not consider object textures as references...

# Alrighty... so when we import/export objects to and from library .blends everything they reference gets exported/imported as well...
# so i'm gathering all the references on export and saving them as a text in the .blend with the exported object...
# this text also has reconstruction logic that fixes up the references on import if they already exist and then deletes any excess data...
# currently shape key data does not count as a reference and will be duplicated, their drivers should still be collected and cleaned up though...
# particle data still needs some work, currently it counts as a reference so a particle system of the same name will be used instead of whats in the library .blend...
# materials are handled seperately...

#---------- FUNCTIONS -------------------------------------------------------------------------

# gathers any driver references...            
def Get_Driver_References(drivers, obj_refs, obj):
    for drv in drivers:
        var_dict = {}
        for var in drv.driver.variables:
            if var.targets[0] != obj and var.targets[0] != None:
                var_dict[var.name] = var.targets[0].id.name
                # i dont think driver variables can have more than one target so i'm just using .targets[0]...
        if len(driver_dict) > 0:
            obj_refs['Drivers'][drv.data_path] = var_dict

# writes and returns reference clean up script...
def Write_References(item, obj_refs):        
    text_name = item.name + ".py"
    text = bpy.data.texts.new(text_name)
    text.write(f"""import bpy
import os
# object references...    
obj_refs = {obj_refs}

# link to options property group...
MMT = bpy.context.scene.JK_MMT    

# gather all objects that are currently linked to collections...
linked_objs = [obj.name for obj in bpy.data.objects if len(obj.users_collection) > 0]

missing_refs = {{}}
removal_refs = {{}}

obj = bpy.context.object

def Get_CleanUp(current_ref, saved_ref, removals, missing, linked, type):
    if current_ref != saved_ref:
        removals[current_ref] = type
    if not saved_ref in linked:
        missing[saved_ref] = type

def Set_Driver_References(drivers, obj_refs, obj):
    for drv in drivers:
        if drv.data_path in obj_refs['Drivers']:
            for var in drv.driver.variables:
                if var.targets[0].id != obj:
                    Get_CleanUp(var.targets[0].id.name, obj_refs['Drivers'][drv.data_path][var.name], removal_refs, missing_refs, linked_objs, 'OBJECT')
                    var.targets[0].id = bpy.data.objects[obj_refs['Drivers'][drv.data_path][var.name]]

def AutoLoad_Material(mat_path, mat_name):
    # remove any images that came with the material from the mesh library...
    if bpy.data.materials[mat_name].use_nodes:
        for node in bpy.data.materials[mat_name].node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image != None:
                bpy.data.images.remove(bpy.data.images[node.image.name], do_unlink=True)
    # remove the material that came from the mesh library...
    bpy.data.materials.remove(bpy.data.materials[mat_name], do_unlink=True)
    # load the material from stash...
    mat_filepath = os.path.join(mat_path, "MATERIAL_" + mat_name + ".blend")    
    with bpy.data.libraries.load(mat_filepath, link=False, relative=False) as (data_from, data_to):
        data_to.materials = [name for name in data_from.materials if name == mat_name]
        data_to.texts = [name for name in data_from.texts if name == mat_name + ".py"]
            
    for ref_text in data_to.texts:
        if ref_text is not None:
            # run and unlink the appended text...
            copy_text = bpy.context.copy()
            copy_text['edit_text'] = ref_text
            bpy.ops.text.run_script(copy_text)
            bpy.ops.text.unlink(copy_text)

if MMT.L_active_parent:
    if obj.parent != None:
        #print("obj parent", obj.parent.name)
        Get_CleanUp(obj.parent.name, MMT.MMT_last_active, removal_refs, missing_refs, linked_objs, 'OBJECT')
    obj.parent = bpy.data.objects[MMT.MMT_last_active]
elif obj.parent != None:
    if obj_refs['Parent'] in bpy.data.objects:
        Get_CleanUp(obj.parent.name, obj_refs['Parent'], removal_refs, missing_refs, linked_objs, 'OBJECT')
        obj.parent = bpy.data.objects[obj_refs['Parent']]

if len(obj_refs['Modifiers']) > 0:
    for mo in obj.modifiers:
        if mo.name in obj_refs['Modifiers']:
            for key, value in obj_refs['Modifiers'][mo.name].items():
                # armature modifiers always targeting last active armature...
                if key == 'object' and mo.type == 'ARMATURE':
                    mo.object = bpy.data.objects[MMT.MMT_last_active]
                if value != None:
                    if key == 'projectors':
                        for i, name in enumerate(value):
                            if name != None:
                                Get_CleanUp(mo.projectors[i].name, value[i], removal_refs, missing_refs, linked_objs, 'OBJECT')
                                mo.projectors[i] = bpy.data.objects[value[i]]
                    elif key == 'action':        
                        Get_CleanUp(mo.action.name, value, removal_refs, missing_refs, linked_objs, 'ACTION')
                        mo.action = bpy.data.actions[value]
                    else:
                        exec("Get_CleanUp(mo." + key + ".name, value, removal_refs, missing_refs, linked_objs, 'OBJECT')")
                        exec("mo." + key + " = bpy.data.objects[value]")
                        
if len(obj_refs['Constraints']) > 0:
    for co in obj.constraints:
        if co.name in obj_refs['Constraints']:
            for key, value in obj_refs['Constraints'][co.name].items():
                if value != None:
                    exec("Get_CleanUp(co." + key + ".name, value, removal_refs, missing_refs, linked_objs, 'OBJECT')")
                    exec("co." + key + " = bpy.data.objects[value]")

if len(obj.particle_systems) > 0:
    for particle in obj.particle_systems:
        Get_CleanUp(obj.particle_systems[particle.name].settings.name, obj_refs['Particles'][particle.name][0], removal_refs, missing_refs, linked_objs, 'PARTICLE')
        obj.particle_systems[particle.name].settings = bpy.data.particles[obj_refs['Particles'][particle.name][0]]
        if obj_refs['Particles'][particle.name][1] != None:
            Get_CleanUp(obj.particle_systems[particle.name].parent.name, obj_refs['Particles'][particle.name][1], removal_refs, missing_refs, linked_objs, 'OBJECT')
            obj.particle_systems[particle.name].parent = bpy.data.objects[obj_refs['Particles'][particle.name][1]]

if len(obj_refs['Physics']) > 0:
    for mo in obj.modifiers:
        if mo.name in obj_refs['Physics']:
            # if it's a smoke modifier...
            if mo.type == 'SMOKE':
                # if its type is domain we need to set these references...
                if mo.smoke_type == 'DOMAIN':
                    if mo.domain_settings.fluid_collection != None:
                        Get_CleanUp(mo.domain_settings.fluid_collection.name, obj_refs['Physics'][mo.name]['FLUID'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                        mo.domain_settings.fluid_collection = bpy.data.collections[obj_refs['Physics'][mo.name]['FLUID']]
                    if mo.domain_settings.collision_collection != None:
                        Get_CleanUp(mo.domain_settings.collision_collection.name, obj_refs['Physics'][mo.name]['COLLISION'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                        mo.domain_settings.collision_collection = bpy.data.collections[obj_refs['Physics'][mo.name]['COLLISION']]
                    if mo.domain_settings.effector_weights.collection != None:
                        Get_CleanUp(mo.domain_settings.effector_weights.collection.name, obj_refs['Physics'][mo.name]['EFFECTOR'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                        mo.domain_settings.effector_weights.collection = bpy.data.collections[obj_refs['Physics'][mo.name]['EFFECTOR']]
                # and if its type is flow we need this reference...
                elif mo.smoke_type == 'FLOW':
                    if mo.flow_settings.noise_texture != None:
                        Get_CleanUp(mo.flow_settings.noise_texture.name, obj_refs['Physics'][mo.name], removal_refs, missing_refs, linked_objs, 'TEXTURE')
                        mo.flow_settings.noise_texture = bpy.data.textures[obj_refs['Physics'][mo.name]]
            # soft body references...
            if mo.type == 'SOFT_BODY':
                if mo.settings.collision_collection != None:
                    Get_CleanUp(mo.settings.collision_collection.name, obj_refs['Physics'][mo.name]['COLLISION'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                    mo.settings.collision_collection = bpy.data.collections[obj_refs['Physics'][mo.name]['COLLISION']]
                if mo.settings.effector_weights.collection != None:
                    Get_CleanUp(mo.settings.effector_weights.collection.name, obj_refs['Physics'][mo.name]['EFFECTOR'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                    mo.settings.effector_weights.collection = bpy.data.collections[obj_refs['Physics'][mo.name]['EFFECTOR']]
            # cloth references...
            if mo.type == 'CLOTH':
                if mo.collision_settings.collection != None:
                    Get_CleanUp(mo.collision_settings.collection.name, obj_refs['Physics'][mo.name]['COLLISION'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                    mo.collision_settings.collection = bpy.data.collections[obj_refs['Physics'][mo.name]['COLLISION']]
                if mo.settings.effector_weights.collection != None:
                    Get_CleanUp(mo.settings.effector_weights.collection.name, obj_refs['Physics'][mo.name]['EFFECTOR'], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                    mo.settings.effector_weights.collection = bpy.data.collections[obj_refs['Physics'][mo.name]['EFFECTOR']]
            # dynamic paint references...
            if mo.type == 'DYNAMIC_PAINT':
                if any(su.brush_collection != None for su in mo.canvas_settings.canvas_surfaces):
                    for i, su in enumerate(mo.canvas_settings.canvas_surfaces):
                        if su.brush_collection != None:
                            Get_CleanUp(su.brush_collection.name, obj_refs['Physics'][mo.name][i], removal_refs, missing_refs, linked_objs, 'COLLECTION')
                            su.brush_collection = bpy.data.collections[obj_refs['Physics'][mo.name][i]]
    # rigid body constraint references...
    if obj.rigid_body_constraint:
        if obj.rigid_body_constraint.object1 != None:
            Get_CleanUp(obj.rigid_body_constraint.object1.name, obj_refs['Physics']['Rigid Body Constraint']['OBJECT1'], removal_refs, missing_refs, linked_objs, 'OBJECT')
            obj.rigid_body_constraint.object1 = bpy.data.objects[obj_refs['Physics']['Rigid Body Constraint']['OBJECT1']]
        if obj.rigid_body_constraint.object2 != None:
            Get_CleanUp(obj.rigid_body_constraint.object2.name, obj_refs['Physics']['Rigid Body Constraint']['OBJECT2'], removal_refs, missing_refs, linked_objs, 'OBJECT')
            obj.rigid_body_constraint.object2 = bpy.data.objects[obj_refs['Physics']['Rigid Body Constraint']['OBJECT2']]
    # force field references...
    if obj.field:
        if obj.field.source_object != None:
            Get_CleanUp(obj.field.source_object.name, obj_refs['Physics']['Force Field']['OBJECT'], removal_refs, missing_refs, linked_objs, 'OBJECT')
            obj.field.source_object = bpy.data.objects[obj_refs['Physics']['Force Field']['OBJECT']]
        if obj.field.texture != None:
            Get_CleanUp(obj.field.texture.name, obj_refs['Physics']['Force Field']['TEXTURE'], removal_refs, missing_refs, linked_objs, 'TEXTURE')
            obj.field.texture = bpy.data.textures[obj_refs['Physics']['Force Field']['TEXTURE']]

if len(obj.material_slots) > 0:
    for i, ma in enumerate(obj.material_slots):
        if ma.material != None:
            Get_CleanUp(ma.material.name, obj_refs['Materials'][i], removal_refs, missing_refs, linked_objs, 'MATERIAL')
            if ma.material.name != obj_refs['Materials'][i]:    
                ma.material = bpy.data.materials[obj_refs['Materials'][i]]
            # always auto load material if we are loading a default mesh...
            elif os.path.join(MMT.MMT_path, "MMT_Stash") in MMT.L_meshes:
                #print("DEFAULT")
                AutoLoad_Material(os.path.join(MMT.MMT_path, "MMT_Stash"), obj_refs['Materials'][i])
                ma.material = bpy.data.materials[obj_refs['Materials'][i]]
            elif MMT.L_autoload_materials:
                #print("AUTO")
                if MMT.S_path != 'None':
                    if "MATERIAL_" + obj_refs['Materials'][i] + ".blend" in os.listdir(MMT.S_path):
                        AutoLoad_Material(MMT.S_path, obj_refs['Materials'][i])
                        ma.material = bpy.data.materials[obj_refs['Materials'][i]]
                    elif "MATERIAL_" + obj_refs['Materials'][i] + ".blend" in os.listdir(os.path.join(MMT.MMT_path, "MMT_Stash")):
                        AutoLoad_Material(os.path.join(MMT.MMT_path, "MMT_Stash"), obj_refs['Materials'][i])
                        ma.material = bpy.data.materials[obj_refs['Materials'][i]]
                    elif obj_refs['Materials'][i] in bpy.data.materials:
                        ma.material = bpy.data.materials[obj_refs['Materials'][i]]
                        print(obj_refs['Materials'][i] + " was not in " + MMT.S_path + " or the default stash, if the material was not already present in the current blend then it has been loaded from the mesh file, you might need to clean up image references manually")
                else:
                    print(ma.material.name + " has been loaded from the mesh library, you might need to clean up image references manually")
            else:
                print(ma.material.name + " has been loaded from the mesh library, you might need to clean up image references manually")
                 
if len(obj_refs['Drivers']) > 0:
    if obj.animation_data:                
        if len(obj.animation_data.drivers) > 0:
            Set_Driver_References(obj.animation_data.drivers, obj_refs, obj)
    if obj.data.shape_keys.animation_data:
        if len(obj.data.shape_keys.animation_data.drivers) > 0:        
            Set_Driver_References(obj.data.shape_keys.animation_data.drivers, obj_refs, obj)

for key in removal_refs:
    #print(key)
    if removal_refs[key] == 'OBJECT':
        bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
    elif removal_refs[key] == 'MATERIAL':
        bpy.data.materials.remove(bpy.data.materials[key], do_unlink=True)
    elif removal_refs[key] == 'TEXTURE':
        bpy.data.textures.remove(bpy.data.textures[key], do_unlink=True)
    elif removal_refs[key] == 'COLLECTION':
        bpy.data.collections.remove(bpy.data.collections[key], do_unlink=True)
    elif removal_refs[key] == 'PARTICLE':
        bpy.data.particles.remove(bpy.data.particles[key], do_unlink=True)
        
for key in missing_refs:
    if missing_refs[key] == 'OBJECT':
        bpy.context.collection.objects.link(bpy.data.objects[key])

""")
    return text    

def Get_References(obj, MMT):
    obj_refs = {}
    # properties of constraints and modifiers that cause object dependencies...
    named_refs = ['object', 'mirror_object', 'target', 'object_from', 'object_to', 'offset_object', 'start_cap', 'end_cap', 'origin', 'start_position_object', 'camera', 'depth_object', 'action']
    physics_mods = ['SOFT_BODY', 'FLUID_SIMULATION', 'SMOKE', 'COLLISION', 'CLOTH', 'DYNAMIC_PAINT']#, 'PARTICLE_SYSTEM']
    # if there is a parent it's a object reference...
    if obj.parent != None:
        obj_refs['Parent'] = obj.parent.name
    # collect any references from modifiers...    
    obj_refs['Modifiers'] = {}
    for mo in obj.modifiers:
        if not mo.type in physics_mods:
            # if it's an armature modifier we do not want to save it's target object as a reference...
            if mo.type == 'ARMATURE':
                mo_object = mo.object    
                mo.object = None 
            if any(prop.identifier in named_refs for prop in mo.bl_rna.properties):
                obj_refs['Modifiers'][mo.name] = {}
                for prop in mo.bl_rna.properties:
                    if prop.identifier in named_refs:
                        exec("obj_refs['Modifiers'][mo.name][prop.identifier] = mo." + prop.identifier + ".name if mo." + prop.identifier + " != None else None")
                    elif prop.identifier == 'projectors':
                        obj_refs['Modifiers'][mo.name][prop.identifier] = [pr.object.name if pr.object != None else None for pr in mo.projectors]                          
            # set the target object back if it was removed...
            if mo.type == 'ARMATURE':
                mo.object = mo_object
    # collect any references from constraints...
    obj_refs['Constraints'] = {}
    for co in obj.constraints:
        if any(prop.identifier in named_refs for prop in co.bl_rna.properties):
            obj_refs['Constraints'][co.name] = {}
            for prop in co.bl_rna.properties:
                if prop.identifier in named_refs:
                    exec("obj_refs['Constraints'][co.name][prop.identifier] = co." + prop.identifier + ".name if co." + prop.identifier + " != None else None")
    # collect any references from particles...
    obj_refs['Particles'] = {}
    for particle in obj.particle_systems:
        obj_refs['Particles'][particle.name] = [particle.settings.name, (particle.parent.name if particle.parent != None else None), [tex.name for tex in particle.settings.texture_slots if tex != None]]
    # collect any references from physics...
    obj_refs['Physics'] = {}
    for mo in obj.modifiers:
        if mo.type in physics_mods:
            # if it's a smoke modifier...
            if mo.type == 'SMOKE':
                # if its type is domain we need to gather these references...
                if mo.smoke_type == 'DOMAIN':
                    smoke_dict = {}
                    if mo.domain_settings.fluid_collection != None:
                        smoke_dict['FLUID'] = mo.domain_settings.fluid_collection.name
                    if mo.domain_settings.collision_collection != None:
                        smoke_dict['COLLISION'] = mo.domain_settings.collision_collection.name
                    if mo.domain_settings.effector_weights.collection != None:
                        smoke_dict['EFFECTOR'] = mo.domain_settings.effector_weights.collection.name
                    if len(smoke_list) > 0:
                        obj_refs['Physics'][mo.name] = smoke_list    
                # and if its type is flow we need this reference...
                elif mo.smoke_type == 'FLOW':
                    if mo.flow_settings.noise_texture != None:
                        obj_refs['Physics'][mo.name] = mo.flow_settings.noise_texture.name
            # if its a soft body modifier we need these references...
            if mo.type == 'SOFT_BODY':
                soft_dict = {}
                if mo.collision_collection != None:
                    soft_dict['COLLISION'] = mo.collision_collection.name
                if mo.settings.effector_weights.collection != None:
                    soft_dict['EFFECTOR'] = mo.settings.effector_weights.collection.name
                if len(soft_dict) > 0:
                    obj_refs['Physics'][mo.name] = soft_dict
            # if its a cloth modifier we need these references...
            if mo.type == 'CLOTH':
                cloth_dict = {}
                if mo.collision_settings.collection != None:
                    cloth_dict['COLLISION'] = mo.collision_settings.collection.name
                if mo.settings.effector_weights.collection != None:
                    cloth_dict['EFFECTOR'] = mo.settings.effector_weights.collection.name
                if len(cloth_dict) > 0:
                    obj_refs['Physics'][mo.name] = cloth_dict
            # if its a dynamic paint modifier we need these references...
            if mo.type == 'DYNAMIC_PAINT':
                if any(su.brush_collection != None for su in mo.canvas_settings.canvas_surfaces):
                    obj_refs['Physics'][mo.name] = [su.brush_collection.name if su.brush_collection != None else None for su in mo.canvas_settings.canvas_surfaces]
    # references in rigid body constraints...
    if obj.rigid_body_constraint:
        rigid_dict = {}
        if obj.rigid_body_constraint.object1 != None:
            rigid_dict['OBJECT1'] = obj.rigid_body_constraint.object1.name
        if obj.rigid_body_constraint.object1 != None:
            rigid_dict['OBJECT2'] = obj.rigid_body_constraint.object2.name
        if len(rigid_dict) > 0:
            obj_refs['Physics']['Rigid Body Constraint'] = rigid_dict
        # references in force fields...
    if obj.field:
        force_dict = {}
        if obj.field.source_object != None:
            force_dict['OBJECT'] = obj.field.source_object.name
        if obj.field.texture != None:
            force_dict['TEXTURE'] = obj.field.texture.name
        if len(force_dict) > 0:
            obj_refs['Physics']['Force Field'] = force_dict
    # collect any references to materials...
    obj_refs['Materials'] = [ma.material.name if ma.material != None else None for ma in obj.material_slots]
    if MMT.A_autosave_materials:
        for ma in obj_refs['Materials']:
            if ma != None:
                importlib.reload(MMT_Stash_Material)
                MMT_Stash_Material.Stash(MMT, bpy.data.materials[ma])
    # collect any references from drivers...
    obj_refs['Drivers'] = {}
    if obj.animation_data:                
        if len(obj.animation_data.drivers) > 0:
            Get_Driver_References(obj.animation_data.drivers, obj_refs, obj)
    # shape key drivers have their own animation data... (is this the same for other data blocks?)
    if obj.data.shape_keys:
        if obj.data.shape_keys.animation_data:
            if len(obj.data.shape_keys.animation_data.drivers) > 0:        
                Get_Driver_References(obj.data.shape_keys.animation_data.drivers, obj_refs, obj)
    return obj_refs

def Save_Object(obj, MMT):
    armature = bpy.data.objects[MMT.MMT_last_active]
    # gather references...
    obj_refs = Get_References(obj, MMT)
    # write the clean up script...
    ref_text = Write_References(obj, obj_refs) 
    # path to the created blend...
    obj_filepath = os.path.join(MMT.S_path, obj.type + "_" + armature.JK_MMT.Rig_type + "_" + obj.name + ".blend") #'MANNEQUIN' + "_" + obj.name + ".blend")
    # set the data to write before...
    data_blocks = set([obj, ref_text])
    # writing the data...
    bpy.data.libraries.write(obj_filepath, data_blocks)
    # unlink the written text...
    copy_text = bpy.context.copy()
    copy_text['edit_text'] = ref_text
    bpy.ops.text.unlink(copy_text)

#---------- EXECUTION -------------------------------------------------------------------------

def Stash(MMT, obj):     
    if obj.type + "_" + obj.name + ".blend" in os.listdir(MMT.S_path):
        if MMT.A_overwrite_existing_meshes:
            Save_Object(obj, MMT)
        else:
            print(obj.name + " already exists in " + os.path.basename(MMT.S_path) + " and was not overwritten")
    else:
        Save_Object(obj, MMT)

# function here for testing...         
#Stash(bpy.context.scene.JK_MMT, bpy.data.objects["SK_Mannequin_LOD0"])