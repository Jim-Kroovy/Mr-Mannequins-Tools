import bpy
import math
import os

def add_export_to_menu(self, context):
    self.layout.operator("jk.export_fbx", icon='USER')

def add_import_to_menu(self, context):
    self.layout.operator("jk.import_fbx", icon='USER')

def add_load_to_menu(self, context):
    self.layout.operator("jk.load_templates", icon='USER')
    
# one little message box function... (just in case)
def show_message(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# not sure if this functions works, will come back to it at some point...
def clean_up_old_props():
    # i'm a dumbass and like to rename some of my add-ons, so they might need cleaning up...
    renamed = {"BLEND-ArmatureControlBones" : {'ARMATURE' : "jk_acb"}, "BLEND-ArmatureRiggingLibrary" : {'OBJECT' : "jk_arl"}}
    for remove, props in renamed.items():
        # if the old name exists in addons, remove the version with the old name...
        if remove in bpy.context.preferences.addons.keys():
            override = bpy.context.copy()
            override['area'] = bpy.context.window_manager.windows[0].screen.areas[0]
            # remove operator needs an area to tag for redraw... (seems to work without but spits error and stops iteration)
            bpy.ops.preferences.addon_remove(override, module=remove)
        # also clean up the old data if it exists... (removed add-on properties turn into custom properties after save/load?? how to handle this)
        for flavour, prop in props.items():
            if flavour == 'ARMATURE':
                for ar in bpy.data.armatures:
                    if prop in ar:
                        del ar[prop]
            elif flavour == 'OBJECT':
                for ob in bpy.data.objects:
                    if prop in ob:
                        del ob[prop]

# get distance between start and end...
def get_distance(start, end):
    x = end[0] - start[0]
    y = end[1] - start[1]
    z = end[2] - start[2]
    distance = math.sqrt((x)**2 + (y)**2 + (z)**2)
    return distance

def get_armature_uses_action(armature, action):
    return True if any(fc.data_path.partition('"')[2].split('"')[0] in armature.data.bones for fc in action.fcurves) else False

def get_armature_has_bones(armature, bones):
    return False if any(b.name not in armature.data.bones for b in bones) else True

def get_armature_has_proportions(armature, bones):
    return False if any(b.head_local != armature.data.bones[b.name].head_local for b in bones) else True

def get_armature_has_directions(armature, bones):
    return False if any(b.y_axis != armature.data.bones[b.name].y_axis for b in bones) else True

def get_action_bone_names(action, armature=None):
    return {fc.data_path.partition('"')[2].split('"')[0] : True if armature != None and fc.data_path.partition('"')[2].split('"')[0] in armature.pose.bones else False
        for fc in action.fcurves if fc.data_path.startswith("pose.bones")}

def scale_objects(unit_scaling, apply_loc, apply_rot):
    # clearing any transforms we don't want applied...
    if not apply_rot:
        bpy.ops.object.rotation_clear(clear_delta=False)
    if not apply_loc:
        bpy.ops.object.location_clear(clear_delta=False)
    # clear all parenting but keep transforms...
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    # iterate through all selected objects...
    for obj in bpy.context.selected_objects:
        # multiply objects scale and location by unit scaling
        obj.location = [obj.location.x * unit_scaling, obj.location.y * unit_scaling, obj.location.z * unit_scaling]
        obj.scale = [obj.scale.x * unit_scaling, obj.scale.y * unit_scaling, obj.scale.z * unit_scaling]
        # we don't want to actually apply the controller armatures transforms, so deselect them...
        if obj.type == 'ARMATURE' and obj.data.jk_adc.is_controller:
            obj.select_set(False)
    # before applying the transforms that we do want applied... (we always want to apply scale)
    bpy.ops.object.transform_apply(location=apply_loc, rotation=apply_rot, scale=True)
    # then iterate again on the armatures...
    armatures = [ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE']
    for arm in armatures:
        # refreshing the constraints for the control/deforms...
        if arm.data.jk_adc.is_deformer:
            arm.data.jk_adc.apply_transforms(arm.data.jk_adc.armature, use_identity=False)

def set_root(armature, length):
    # we want to be able to add a root bone regardless of current mode...
    last_mode = armature.mode
    if armature.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    # add the root bone with whatever length and the inverse matrix of the armatures parent...
    root_eb = armature.data.edit_bones.new(armature.name)
    root_eb.length, root_eb.matrix = length, armature.matrix_parent_inverse.copy()
    # and parent any parentless bones to it...
    for e_bone in [eb for eb in armature.data.edit_bones if eb.parent == None]:
        e_bone.parent = root_eb
    if armature.mode != last_mode:
        bpy.ops.object.mode_set(mode=last_mode)
    return armature.pose.bones.get(armature.name)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- TEMPLATE FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def load_armature(self, templates):
    # get the variables...
    prefs, unit_scale = bpy.context.preferences.addons["MrMannequinsTools"].preferences, bpy.context.scene.unit_settings.scale_length
    template = self.bipeds if self.flavour == 'BIPED' else self.quadrupeds if self.flavour == 'QUADRUPED' else self.equipment
    rigging = "_Rigging" if self.controls and self.rigging else "_Controls" if self.controls and not self.rigging else ""
    armature, sub_path = None, os.path.join(prefs.resources, "armatures")
    for library in templates[template]['armatures'].keys():
        # load the template things from their library .blend...
        with bpy.data.libraries.load(os.path.join(sub_path, library + ".blend"), link=False, relative=False) as (data_from, data_to):
            # the objects we want to pull through... (if we have rigging meshes/curves they should get pulled in as a dependency)
            data_to.objects = [o for o in data_from.objects if o.endswith("Skeleton" + rigging)]
        # there should only be one armature... (for now)
        armatures = [ob for ob in data_to.objects if ob is not None and ob.type == 'ARMATURE']
        
        if armatures:
            armature = armatures[0]
            armature.name, armature.data.name = library, library
            # if we are rescaling objects...
            if self.rescale:
                # scale the object xyz to fit the scene...
                unit_scaling = 1.0 / (100 * unit_scale)
                armature.scale = [armature.scale[0] * unit_scaling, armature.scale[1] * unit_scaling, armature.scale[2] * unit_scaling]
            # link the armatures to the scene...
            bpy.context.collection.objects.link(armature)
            armature.select_set(True)
            ob_chains = [rg for rg in armature.jk_arm.rigging if rg.flavour == 'SPLINE']
            for chain in ob_chains:
                spline = chain.spline
                # and link it to the scene... (but don't select it)
                bpy.context.collection.objects.link(spline.spline.curve)
            if armature.data.jk_adc.is_controller:
                armature.data.jk_adc.subscribe_mode(armature)

    # return the armature so we can assign meshes to it...
    return armature

def load_meshes(self, templates, armature):
    # get the variables...
    prefs, unit_scale = bpy.context.preferences.addons["MrMannequinsTools"].preferences, bpy.context.scene.unit_settings.scale_length
    template = self.bipeds if self.flavour == 'BIPED' else self.quadrupeds if self.flavour == 'QUADRUPED' else self.equipment
    meshes, sub_path = [], os.path.join(prefs.resources, "meshes")
    for library in templates[template]['meshes'].keys():
        # load the template things from their library .blend...
        with bpy.data.libraries.load(os.path.join(sub_path, library + ".blend"), link=False, relative=False) as (data_from, data_to):
            # the objects we want to pull through...
            data_to.objects = [o for o in data_from.objects] if self.lods else [o for o in data_from.objects if o.endswith("_LOD0")]
        # then we may need to scale/instance them...
        objects = [ob for ob in data_to.objects if ob is not None]
        for obj in objects:
            bpy.context.collection.objects.link(obj)
            # if we are rescaling objects...
            if self.rescale:
                # scale the object xyz to fit the scene...
                unit_scaling = 1.0 / (100 * unit_scale)
                obj.scale = [obj.scale[0] * unit_scaling, obj.scale[1] * unit_scaling, obj.scale[2] * unit_scaling]
            # maybe instance it from an existing mesh...
            mesh = obj.data
            if self.instance:
                existing = [me for me in bpy.data.meshes if me != mesh and mesh.name.startswith(me.name)]
                if existing:
                    obj.data = existing[0]
                    bpy.data.meshes.remove(mesh)
                else:
                    # we only want to select meshes to have their scale applied if they cannot be instanced...
                    obj.select_set(True)
            else:
                # else if we aren't trying to instance meshes then we always need to select them to apply scale...
                obj.select_set(True)
            meshes.append(obj)
            # if these meshes come with an armature...
            if armature:
                # give them and armature modifier to it...
                mod = obj.modifiers.new(type='ARMATURE', name="Armature")
                mod.name, mod.show_expanded = "Armature", False
                mod.object = armature
    # return the objects we loaded so we can assign materials to them...
    return meshes

def load_materials(self, templates, meshes):
    # get the variables...
    prefs, materials = bpy.context.preferences.addons["MrMannequinsTools"].preferences, []
    template = self.bipeds if self.flavour == 'BIPED' else self.quadrupeds if self.flavour == 'QUADRUPED' else self.equipment
    sub_path = os.path.join(prefs.resources, "materials")
    for library, slot in templates[template]['materials'].items():
        # load the template things from their library .blend...
        with bpy.data.libraries.load(os.path.join(sub_path, library + ".blend"), link=False, relative=False) as (data_from, data_to):
            # the objects we want to pull through...
            data_to.materials, data_to.images, data_to.node_groups = [m for m in data_from.materials], [i for i in data_from.images], [n for n in data_from.node_groups]
        # we might be remapping materials...
        material = data_to.materials[0]
        if self.remap:
            existing = [ma for ma in bpy.data.materials if ma != material and material.name.startswith(ma.name)]
            if existing:
                material.user_remap(existing[0])
                bpy.data.materials.remove(material)
                material = existing[0]
        # always remap to existing nodes... (0 user nodes don't get cleaned up)
        for nod in data_to.node_groups:
            if nod is not None:
                nodes = [no for no in bpy.data.node_groups if no != nod and nod.name.startswith(no.name)]
                if nodes:
                    nod.user_remap(nodes[0])
                    bpy.data.node_groups.remove(nod)
        # images are heavy on file size so always remap them if possible... (even if material isn't being remapped)
        for img in data_to.images:
            if img is not None:
                images = [im for im in bpy.data.images if im != img and img.filepath == im.filepath]
                if images:
                    img.user_remap(images[0])
                    bpy.data.images.remove(img)
                else:
                    # if we didn't already have the image sort out its file path and reload it...
                    img.filepath = os.path.join(prefs.resources, os.path.join("textures", img.name))
                    img.reload()
        # if there are meshes that should use this material...
        if meshes:
            # set it to their correct material slots...
            for mesh in meshes:
                mesh.material_slots[slot].material = material
        materials.append(material)
    # return materials for the sake of it lol...
    return materials

def load_actions(self, templates):
    # i'll come back and add root motion versions of all the TP animations at some point...
    pass

def load_template(self, templates):
    armature, meshes, materials = None, [], []
    # deselect everything....
    bpy.ops.object.select_all(action='DESELECT')
    # load/select the contents of the template...
    template = self.bipeds if self.flavour == 'BIPED' else self.quadrupeds if self.flavour == 'QUADRUPED' else self.equipment
    if self.armatures and templates[template]['armatures']:
        armature = load_armature(self, templates)
    if self.meshes:
        meshes = load_meshes(self, templates, armature)
    if self.materials:
        materials = load_materials(self, templates, meshes)
    # apply any scaling to selected objects...
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # if we have meshes with an armature...
    if meshes and armature:
        # parent them to it...
        for mesh in meshes:
            mesh.parent = armature
    # if we loaded an armature...
    if armature and self.rescale:
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)
        # if the armature was scaled with controls/rigging...
        if self.controls:
            # all the deform child of constraints need resetting... (all my templates are combined armatures)
            armature.data.jk_adc.apply_transforms(armature, use_identity=True)
        if self.rigging:
            # some of the rigging may need it's transforms applied...
            for ri, rigging in enumerate(armature.jk_arm.rigging):
                if rigging.flavour in ['SPLINE', 'OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE', 'TRACKING', 'TAIL_FOLLOW']:
                    armature.jk_arm.active = ri
                    chain = rigging.get_pointer()
                    chain.apply_transforms()
            rigging.get_sources()
        armature.jk_arm.subscribe_mode()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- EXPORT FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def export_fbx(path, props, is_action, types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'}):
    bpy.ops.export_scene.fbx(filepath=path,
        check_existing=True, filter_glob="*.fbx", use_selection=True, use_active_collection=False, global_scale=1.0, apply_unit_scale=False, 
        #---------------------------------------------------------------------------------#
        apply_scale_options='FBX_SCALE_ALL', bake_space_transform=False, object_types=types,
        #------------------------------------------------#
        use_mesh_modifiers=props.fbx_props.apply_modifiers,
        use_mesh_modifiers_render=True, mesh_smooth_type='FACE', use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_custom_props=False,
        #---------------------------------------------------------------------------------------------------------------------------------------------------------# 
        add_leaf_bones=props.fbx_props.add_leaf_bones, primary_bone_axis=props.fbx_props.primary_bone_axis, secondary_bone_axis=props.fbx_props.secondary_bone_axis,
        use_armature_deform_only=True, armature_nodetype='NULL',
        #---------------------------------------------# 
        bake_anim=props.actions if is_action else False,
        bake_anim_use_all_bones=True,
        #--------------------------------------------------------------------------------------------------------------------------------------------------------------------# 
        bake_anim_use_nla_strips=props.fbx_props.use_nla, bake_anim_use_all_actions=props.fbx_props.all_actions, bake_anim_force_startend_keying=props.fbx_props.startend_keys, 
        #-------------------------------------------------------------------------------------------------# 
        bake_anim_step=props.fbx_props.anim_step, bake_anim_simplify_factor=props.fbx_props.simplify_factor,
        path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True,
        #------------------------------------------------------------------------# 
        axis_forward=props.fbx_props.axis_forward, axis_up=props.fbx_props.axis_up)

def export_s2u(use_selection): # ONLY SUPPORTS MESHES AND ARMATURES COME BACK AND SORT OUT COLLISION AND EXTRAS!!!!
    if use_selection:
        # assign our selected objects to the collection names, and create a reference to collections that should be deleted...
        coll_objs = {'Mesh' : [me for me in bpy.context.selected_objects if me.type == 'MESH'], 'Rig' : [ar for ar in bpy.context.selected_objects if ar.type == 'ARMATURE']}#, 'Collision', 'Extras'}
        del_colls = []
        # then for each collection/object list...
        for name, objs in coll_objs:
            # if the collection exists get it...
            if name in bpy.context.scene.collection.children:
                coll = bpy.context.scene.collection.children[name]
                # and clear its current objects... (if any)
                coll_objs = [ob for ob in coll.objects]
                for coll_obj in coll_objs:
                    coll.objects.unlink(coll_obj)
            else:
                # else we need to create it and assign it for deletion...
                coll = bpy.data.collections.new(name=name)
                bpy.context.scene.collection.children.link(coll)
                del_colls.append(coll)
            # then link in our selected objects to the collection...
            for obj in objs:
                coll.objects.link(obj)
    # fire their send to unreal operator...
    bpy.ops.wm.send2ue()
    if use_selection:
        # then unlink all the selected objects from the send to unreal collections...
        for name, objs in coll_objs:
            for obj in objs:
                coll.objects.unlink(obj)
        # and if we have any collections to delete, unlink them...
        for del_coll in del_colls:
            bpy.context.scene.collection.children.unlink(del_coll)

def action_export(eport, ac_armatures):
    # for each action armature...
    for armature in ac_armatures:
        if not armature.animation_data:
            armature.animation_data_create()
        if not armature.data.jk_adc.armature.animation_data:
            armature.data.jk_adc.armature.animation_data_create()
        # if we should be muting NLA strips, mute them...
        if eport.mute_nla and not eport.fbx_props.use_nla:
            for track in armature.animation_data.nla_tracks:
                track.mute = True
        # get all the actions to export and iterate on them...
        only_active = not (eport.batch_actions or eport.fbx_props.all_actions or eport.fbx_props.use_nla)
        if eport.mute_nla:
            for track in armature.animation_data.nla_tracks:
                track.mute = True
        # if we are batch exporting actions or only exporting the active ones...
        if eport.batch_actions or only_active:
            actions, _ = armature.data.jk_adc.get_actions(armature, only_active)
            for action in actions.keys():
                # set the scenes frame start/end from the actions frame range...
                bpy.context.scene.frame_start, bpy.context.scene.frame_end = int(round(action.frame_range[0], 0)), int(round(action.frame_range[1], 0))
                # clear the controllers pose transforms...
                for pb in armature.pose.bones:
                    pb.location, pb.scale, pb.rotation_euler = [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]
                    pb.rotation_quaternion, pb.rotation_axis_angle = [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]
                # setting the action to be the active one...
                armature.animation_data.action = action
                # selecting and exporting only the deformer...
                bpy.ops.object.select_all(action='DESELECT')
                armature.data.jk_adc.armature.select_set(True)
                bpy.context.view_layer.objects.active = armature.data.jk_adc.armature
                path = os.path.join(bpy.path.abspath(eport.path_actions), eport.prefix_action + action.name + ".fbx")
                existing = bpy.data.objects.get("Armature")
                if existing:
                    existing.name = armature.name
                armature.name = "Armature"
                armature.data.pose_position = 'POSE'
                export_fbx(path, eport, True, types={'ARMATURE'})
        else:
            if not armature.data.jk_adc.armature.animation_data:
                armature.data.jk_adc.armature.animation_data_create()
            # bake all actions to the deform bones... (I'm not happy about this but it's a lot simpler than the alternatives)
            bpy.ops.jk.adc_bake_deforms('EXEC_DEFAULT', armature=armature.name, bake_step=1, only_active=False)
            # deselect everything and select the deforming armature...
            bpy.ops.object.select_all(action='DESELECT')
            armature.data.jk_adc.armature.select_set(True)
            # if the nla should influence export...
            if eport.fbx_props.use_nla or not eport.mute_nla:
                # select the controlling armature and link it's animation data to the deformer...
                armature.select_set(True)
                bpy.context.view_layer.objects.active = armature
                bpy.ops.object.make_links_data(type='ANIMATION')
                # then get all the actions again so we have the baked ones too...
                actions, _ = armature.data.jk_adc.get_actions(armature, only_active)
                for source, baked in actions.items():
                    # iterate through all the deformers NLA strips...
                    for track in armature.data.jk_adc.armature.animation_data.nla_tracks:
                        for strip in track.strips:
                            # replacing source actions with baked ones...
                            if strip.action == source:
                                strip.action = baked
                # then deselect the controlling armature...
                armature.select_set(False)
            # and export only the deformer...
            bpy.context.view_layer.objects.active = armature.data.jk_adc.armature
            path = os.path.join(bpy.path.abspath(eport.path_actions), eport.prefix_action + armature.name + ".fbx")
            existing = bpy.data.objects.get("Armature")
            if existing:
                existing.name = armature.data.jk_adc.armature.name
            armature.data.jk_adc.armature.name = "Armature"
            armature.data.pose_position = 'POSE'
            export_fbx(path, eport, True, types={'ARMATURE'})
            
def mesh_export(eport, sk_meshes, st_meshes):
    only_selected = True if len(sk_meshes) <= 1 and len(st_meshes) <= 1 else False
    if eport.batch_meshes or only_selected:
        # export each skeletal mesh with it's armature...
        for sk_mesh in sk_meshes:
            bpy.ops.object.select_all(action='DESELECT')
            sk_armature = sk_mesh.find_armature()
            sk_mesh.select_set(True)
            sk_armature.select_set(True)
            bpy.context.view_layer.objects.active = sk_armature
            path = os.path.join(bpy.path.abspath(eport.path_meshes), eport.prefix_skeletal + sk_mesh.name + ".fbx")
            existing = bpy.data.objects.get("Armature")
            if existing:
                existing.name = sk_armature.name
            sk_armature.name = "Armature"
            sk_armature.data.pose_position = 'REST'
            export_fbx(path, eport, False, types={'ARMATURE', 'MESH'}) 
        # and each static mesh by itself...  
        for st_mesh in st_meshes:
            bpy.ops.object.select_all(action='DESELECT')
            st_mesh.select_set(True)
            bpy.context.view_layer.objects.active = st_mesh
            path = os.path.join(bpy.path.abspath(eport.path_meshes), eport.prefix_static + st_mesh.name + ".fbx")
            export_fbx(path, eport, False, types={'MESH'})        
    else:
        # if we are cluster exporting meshes we need to gather the skeletal meshes by armature...
        if sk_meshes:
            sk_armature_meshes = {}
            for sk_mesh in sk_meshes:
                sk_armature = sk_mesh.find_armature()
                if sk_armature in sk_armature_meshes:
                    sk_armature_meshes[sk_armature].append(sk_mesh)
                else:
                    sk_armature_meshes[sk_armature] = [sk_mesh]
            # then we iterate through the armatures exporting all the meshes gathered with them...
            for sk_armature, sk_meshes in sk_armature_meshes.items():
                bpy.ops.object.select_all(action='DESELECT')
                sk_armature.select_set(True)
                bpy.context.view_layer.objects.active = sk_armature
                path = os.path.join(bpy.path.abspath(eport.path_meshes), eport.prefix_skeletal + sk_armature.name + ".fbx")
                existing = bpy.data.objects.get("Armature")
                if existing:
                    existing.name = sk_armature.name
                sk_armature.name = "Armature"
                sk_armature.data.pose_position = 'REST'
                for sk_mesh in sk_meshes:
                    sk_mesh.select_set(True)
                export_fbx(path, eport, False, types={'ARMATURE', 'MESH'})
        # and export all static meshes into an FBX together...
        bpy.ops.object.select_all(action='DESELECT')
        if st_meshes:
            for st_mesh in st_meshes:
                st_mesh.select_set(True)
                bpy.context.view_layer.objects.active = st_mesh
            path = os.path.join(bpy.path.abspath(eport.path_meshes), eport.prefix_static + st_meshes[0].name + ".fbx")
            export_fbx(path, eport, False, types={'MESH'})

def run_export(eport):
    unit_scaling = eport.export_scale * bpy.context.scene.unit_settings.scale_length
    # we don't want to be auto keyframing anything on export, so switch it off...
    is_auto_keying = bpy.context.scene.tool_settings.use_keyframe_insert_auto
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
    # get the meshes we want to export...
    st_meshes = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH' and not ob.find_armature()]
    sk_meshes = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH' and ob.find_armature()]
    # get the armatures we want to export...
    ac_armatures = [ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE']
    sk_armatures = [sk.find_armature().data.jk_adc.armature if sk.find_armature().data.jk_adc.is_deformer else sk.find_armature() for sk in sk_meshes]
    # sort out the armatures and their control/deforms...
    for armature in ac_armatures + sk_armatures:
        bpy.context.view_layer.objects.active = armature
        # if the armature doesn't have control/deform bones, give it some...
        if not armature.data.jk_adc.is_controller:
            bpy.ops.jk.adc_edit_controls('EXEC_DEFAULT', action='ADD', only_deforms=True)
        # if it's deforms are combined, un-combine them...
        if armature.data.jk_adc.use_combined:
            armature.data.jk_adc.use_combined = False
        # set it to use the deform bones...
        if not armature.data.jk_adc.use_deforms:
            armature.data.jk_adc.use_deforms = True  
        # and unhide the deforms if they are hidden...
        if armature.data.jk_adc.hide_deforms:
            armature.data.jk_adc.hide_deforms = False
        else:
            # if they weren't hiding we'll need to select the deform armature... (it got deselected on invoke)
            armature.data.jk_adc.armature.select_set(True)
        # and make sure we have the control armature selected also...
        armature.select_set(True)
    bpy.ops.object.mode_set(mode='OBJECT')
    # scale everything that needs scaling...
    scale_objects(unit_scaling, eport.apply_location, eport.apply_rotation)
    # if we are batch/cluster exporting actions, export them...
    if eport.actions:
        action_export(eport, ac_armatures)
    # if we are batch/cluster exporting meshes, export them...
    if eport.meshes:
        mesh_export(eport, sk_meshes, st_meshes)
    # set auto keying back to whatever it was...
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = is_auto_keying

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- EXPORT INTERFACE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def show_export_meshes(self, eport):
    is_only_active = not (eport.batch_actions or eport.fbx_props.all_actions or eport.fbx_props.use_nla)
    is_path_equal = True if eport.path_actions == eport.path_meshes and eport.prefix_skeletal == eport.prefix_action else False
    layout, is_conflict = self.layout, True if is_path_equal and not is_only_active else False
    box = layout.box()
    row = box.row()          
    row.prop(eport, "path_meshes", text="Mesh Folder")
    row = box.row()
    row.prop(eport, "meshes")
    col = row.column()
    col.enabled = eport.meshes
    col.prop(eport, "batch_meshes")
    col = row.column()
    col.enabled = eport.meshes
    col.prop(eport.fbx_props, "apply_modifiers")
    
    if is_conflict:
        row = box.row()
        row.label(text="Please use a prefix! Skeletal mesh and action FBXs using the same armature and folder may overwrite each other", icon='ERROR')
    
    row = box.row()
    row.prop(eport, "prefix_skeletal", text="Skeletal Prefix")
    row.enabled = eport.meshes
    
    row = box.row()
    row.prop(eport, "prefix_static", text="Static Prefix")
    row.enabled = eport.meshes
    
def show_export_actions(self, eport):
    is_only_active = not (eport.batch_actions or eport.fbx_props.all_actions or eport.fbx_props.use_nla)
    is_path_equal = True if eport.path_actions == eport.path_meshes and eport.prefix_skeletal == eport.prefix_action else False
    layout, is_conflict = self.layout, True if is_path_equal and not is_only_active else False
    box = layout.box()
    row = box.row()  
    row.prop(eport, "path_actions", text="Action Folder")
    row = box.row()
    row.prop(eport, "actions")
    col = row.column()
    col.enabled = eport.actions
    col.prop(eport, "batch_actions")
    col = row.column()
    col.enabled = eport.actions
    col.prop(eport.fbx_props, "startend_keys")

    row = box.row()
    col = row.column()
    # only enable all actions if not batch exporting...
    col.prop(eport.fbx_props, "all_actions")
    col.enabled = not eport.batch_actions
    # only enable muted nla if not using nla...
    col = row.column()
    col.prop(eport, "mute_nla")
    col.enabled = not eport.fbx_props.use_nla
    # disable use NLA if we are batch exporting...
    col = row.column()
    col.prop(eport.fbx_props, "use_nla")
    col.enabled = not eport.batch_actions
    row.enabled = eport.actions
    
    row = box.row()
    row.enabled = eport.actions
    row.prop(eport.fbx_props, "anim_step")
    row.prop(eport.fbx_props, "simplify_factor")
    row = box.row()
    row.enabled = eport.actions

    if is_conflict:
        row = box.row()
        row.label(text="Please use a prefix! Skeletal mesh and action FBXs using the same armature and folder may overwrite each other", icon='ERROR')
    
    row = box.row()
    row.prop(eport, "prefix_action", text="Action Prefix")
    row.enabled = eport.actions

def show_export_advanced(self, eport):
    layout = self.layout
    row = layout.row()
    row.prop(eport, "show_advanced")
    col = row.column()
    col.prop(eport, "send_to_unreal")
    col.enabled = False
    if eport.show_advanced:
        box = layout.box()
        row = box.row()
        row.label(text="Primary Bone Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(eport.fbx_props, "primary_bone_axis", text="")
        row.label(text="Object Forward Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(eport.fbx_props, "axis_forward", text="")
        
        row = box.row()
        row.label(text="Secondary Bone Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(eport.fbx_props, "secondary_bone_axis", text="")
        row.label(text="Object Up Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(eport.fbx_props, "axis_up", text="")
        
        row = box.row()
        row.prop(eport.fbx_props, "add_leaf_bones")
        row.prop(eport, 'apply_location')
        row.prop(eport, 'apply_rotation')
        
        row = box.row()
        row.prop(eport, "export_scale")   
        
        # alternative axis display...
        #row = box.row()
        #row.label(text="Primary Bone Axis:")
        #col = row.column()
        #col.ui_units_x = 25
        #row = col.row()
        #row.prop(eport.FBX_props, "Primary_bone_axis", expand=True)

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- IMPORT FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def import_fbx(path, props, is_action):
    bpy.ops.import_scene.fbx(filepath=path, directory="", filter_glob="*.fbx", ui_tab='MAIN', #files=None, 
        #--------------------------------------------------#
        use_manual_orientation=props.fbx_props.manual_orient,
        global_scale=1.0, bake_space_transform=False, use_custom_normals=True, use_image_search=False, use_alpha_decals=False, decal_offset=0.0, 
        #--------------------------------------------------------------#
        use_anim=props.actions if is_action else False, anim_offset=props.fbx_props.anim_offset, 
        use_subsurf=False, 
        #-----------------------------------------------------------------------------------------------------------------------------# 
        use_custom_props=props.fbx_props.user_props, use_custom_props_enum_as_string=True, ignore_leaf_bones=props.fbx_props.ignore_leaf_bones,
        force_connect_children=False, automatic_bone_orientation=False,
        #----------------------------------------------------------------------------------------------------------# 
        primary_bone_axis=props.fbx_props.primary_bone_axis, secondary_bone_axis=props.fbx_props.secondary_bone_axis,
        use_prepost_rot=True, 
        #------------------------------------------------------------------------#
        axis_forward=props.fbx_props.axis_forward, axis_up=props.fbx_props.axis_up)

def get_fbx_paths(iport):
    # figure out what we are importing from all the fbx paths...
    if iport.batch_actions:
        action_fbxs = [ac for ac in os.listdir(bpy.path.abspath(iport.path_actions)) if ac.upper().endswith(".FBX")]
    else:
        action_fbxs = [iport.action_fbx]
    if iport.batch_meshes:
        mesh_fbxs = [me for me in os.listdir(bpy.path.abspath(iport.path_meshes)) if me.upper().endswith(".FBX")]
    else:
        mesh_fbxs = [iport.mesh_fbx]
    # then organise them into a dictionary for easier iteration...
    fbx_paths = {}
    if iport.actions:
        for ac_fbx in action_fbxs:
            if iport.batch_actions:
                ac_path = os.path.join(bpy.path.abspath(iport.path_actions), ac_fbx)
            else:
                ac_path = bpy.path.abspath(ac_fbx)
            if ac_path in fbx_paths:
                fbx_paths[ac_path]['Actions'] = True
            else:
                fbx_paths[ac_path] = {'Actions' : True, 'Meshes' : False}

    if iport.meshes:
        for me_fbx in mesh_fbxs:
            if iport.batch_meshes:
                me_path = os.path.join(bpy.path.abspath(iport.path_meshes), me_fbx)
            else:
                me_path = bpy.path.abspath(me_fbx)
            if me_path in fbx_paths:
                fbx_paths[me_path]['Meshes'] = True
            else:
                fbx_paths[me_path] = {'Actions' : False, 'Meshes' : True}

    return fbx_paths

def import_armatures(iport, armatures, active):
    remove_armatures = []
    for armature, actions in armatures.items():
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        # get and deselect the pose bones...
        pbs, root_pb = armature.pose.bones, None
        for pb in pbs:
            pb.bone.select = False
        # if we are adding a root bone, add and select it...
        if iport.add_root and armature.name not in armature.data.bones:
            root_pb = set_root(armature, 0.25)
            root_pb.bone.select = True
        # if we have imported actions...
        if actions:
            # we should rename all imported actions to use the bake prefix of the control/deform actions... ?
            adc_prefs = bpy.context.preferences.addons["BLEND-ArmatureDeformControls"].preferences
            for action, fps_scale in actions.items():
                print("Mr Mannequin is now processing:", action.name)
                action.name = adc_prefs.deform_prefix + action.name
                # always set fake user so the action doesn't get deleted by mistake...
                action.use_fake_user = True
                # if we need to scale the action to the framerate, scale it...
                if iport.scale_keyframes and fps_scale != 1.0:
                    for fcurve in action.fcurves:
                        for key in fcurve.keyframe_points:
                            key.co[0] = (key.co[0] - iport.fbx_props.anim_offset) * fps_scale + iport.fbx_props.anim_offset
                            key.handle_left[0] = (key.handle_left[0] - iport.fbx_props.anim_offset) * fps_scale + iport.fbx_props.anim_offset
                            key.handle_right[0] = (key.handle_right[0] - iport.fbx_props.anim_offset) * fps_scale + iport.fbx_props.anim_offset
                # if we are going to apply the armatures scale...
                if iport.apply_scale:
                    # quick and dirty fix for retargeting translation...
                    use_trans, trans_names = iport.use_default_retargeting_translation, [root_pb.name if root_pb else 'root', 'pelvis', 'ik_hand_l', 'ik_hand_r', 'ik_foot_l', 'ik_foot_r', 'ik_foot_root', 'ik_hand_root']
                    # we need to apply its automatic scaling after import to the pose bone curves... (only scale fcurve locations that should be scaled)
                    loc_curves = [fc for fc in action.fcurves if (fc.data_path.endswith("location") and fc.data_path != 'location') and (fc.data_path.partition('"')[2].split('"')[0] in trans_names if use_trans else True)]
                    scale = armature.scale
                    for fcurve in loc_curves:
                        for key in fcurve.keyframe_points:
                            # multiply keyframed location by scale per channel...
                            key.co[1] = key.co[1] * scale[fcurve.array_index]
                            key.handle_left[1] = key.handle_left[1] * scale[fcurve.array_index] 
                            key.handle_right[1] = key.handle_right[1] * scale[fcurve.array_index]
                    # if using quick fix...
                    if use_trans:
                        # kill all location curves that didn't get scaled...
                        del_curves = [fc for fc in action.fcurves if (fc.data_path.endswith("location") and fc.data_path != 'location') and fc.data_path.partition('"')[2].split('"')[0] not in trans_names]
                        clear_pbs = {}
                        for del_curve in del_curves:
                            bone_name = del_curve.data_path.partition('"')[2].split('"')[0]
                            action.fcurves.remove(del_curve)
                            clear_pbs[bone_name] = armature.pose.bones.get(bone_name)
                        # and clear any leftover translations on the bones...
                        if clear_pbs:
                            for name, pb in clear_pbs.items():
                                if pb:
                                    pb.location = [0.0, 0.0, 0.0]
                # if we added a root...                
                if root_pb:
                    # and the action has object curves...
                    ob_curves = [fc for fc in action.fcurves if fc.data_path in ["location", "rotation_quaternion", "rotation_euler", "rotation_axis_angle", "scale"]]
                    #print(root_pb, ob_curves)
                    if ob_curves:
                        # make the action active...
                        armature.animation_data.action = action
                        # and iterate on the object fcurves...
                        for ob_curve in ob_curves:
                            # adding a root curve for each one... (ignoring scale)
                            if ob_curve.data_path != "scale":
                                root_path = 'pose.bones["' + root_pb.name + '"].' + ob_curve.data_path
                                root_curve = action.fcurves.new(root_path, index=ob_curve.array_index, action_group=root_pb.name)
                                # and adding root keys for each object key...
                                for ob_key in ob_curve.keyframe_points:
                                    # they should be the same as the created roots, orientation will be the same as the armature objects...
                                    root_curve.keyframe_points.insert(ob_key.co[0], ob_key.co[1], options=set(), keyframe_type='KEYFRAME')
                            # then getting rid of the object fcurve...
                            action.fcurves.remove(ob_curve)
                # if we are attempting to bake animation to active armatures controls...
                if iport.bake_to_active and active:
                    # make sure the active armature has it's control/deforms set up to recieve the animation...
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = active
                    active.select_set(True)
                    # if it's deforms are combined, un-combine them...
                    if active.data.jk_adc.use_combined:
                        active.data.jk_adc.use_combined = False  
                    # and unhide the deforms if they are hidden...
                    if active.data.jk_adc.hide_deforms:
                        active.data.jk_adc.hide_deforms = False
                    else:
                        # if they weren't hiding we'll need to select the deform armature...
                        active.data.jk_adc.armature.select_set(True)
                    # give the deform armature the action...
                    if not active.data.jk_adc.armature.animation_data:
                        active.data.jk_adc.armature.animation_data_create()
                    active.data.jk_adc.armature.animation_data.action = action
                    
                    if active.data.jk_adc.mute_deforms:
                        active.data.jk_adc.mute_deforms = False
                    # and bake to the controls...
                    if not active.data.jk_adc.reverse_deforms:
                        active.data.jk_adc.reverse_deforms = True
                    bpy.ops.jk.adc_bake_controls('EXEC_DEFAULT', armature=active.data.jk_adc.armature.name, bake_step=1, only_active=True)

        # if any meshes using this armature should be deformed to the active armature...
        meshes = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.find_armature() == armature]
        if iport.deform_to_active and meshes and active:
            # insert retargeting logic here, when it's sorted out...
            pass
        
        # we can append the armature to be removed if...
        if iport.clean_up:
            # there were no actions and we retargeted it's meshes...
            if (iport.deform_to_active and meshes and active) and not actions:
                remove_armatures.append(armature)
            # or there were no meshes and we retargeted it's actions...
            elif (iport.bake_to_active and actions and active) and not meshes:
                remove_armatures.append(armature)
            # or we retargeted both its actions and meshes...
            elif (iport.bake_to_active and actions and active) and (iport.deform_to_active and meshes and active):
                remove_armatures.append(armature)
    
    # remove any armatures that may want to be cleaned up...
    for remove_armature in remove_armatures:
        # by making sure they are removed from the armatures dictionary...
        del armatures[remove_armature]
        # then getting rid of both object and it's data...
        data = remove_armature.data
        bpy.data.objects.remove(remove_armature)
        bpy.data.armatures.remove(data)

def import_meshes(iport, sk_meshes, st_meshes, active):
    # remap any materials...
    for mesh in sk_meshes + st_meshes:
        for slot in mesh.material_slots:
            new_material = slot.material
            for material in bpy.data.materials:
                if material.name.startswith(new_material.name) and material != new_material:
                    slot.material = material
    # if we want to import the mesh to the active armature...
    if iport.deform_to_active:
        for sk_mesh in sk_meshes:
            # switch their armature modifiers to the assigned armature...
            for mod in [mo for mo in sk_mesh.modifiers if mo.type == 'ARMATURE']:
                mod.object = active
            sk_mesh.parent = active

def run_import(iport):
    # we don't want to be auto keyframing anything on import, so switch it off...
    is_auto_keying = bpy.context.scene.tool_settings.use_keyframe_insert_auto
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
    # get some references...
    active = bpy.context.view_layer.objects.active
    if active and active.type != 'ARMATURE':
        active = None
    existing_objects = {ob : ob.type for ob in bpy.data.objects}
    existing_actions = {ac : ac.frame_range for ac in bpy.data.actions}
    removal_objects = {}
    # get the paths for what needs importing...
    fbx_paths= get_fbx_paths(iport)
    armatures, sk_meshes, st_meshes = {}, [], []
    pre_fps = bpy.context.scene.render.fps
    # iterate on the fbx paths importing everything we want to import...          
    for path, bools in fbx_paths.items():
        # import the fbx... (only importing actions if we should)
        import_fbx(path, iport, bools['Actions'])
        post_fps = bpy.context.scene.render.fps
        # get all the new armatures with any actions that might of come with them...
        new_armatures = {ob : {ac : (pre_fps / post_fps) for ac in ob.data.jk_adc.get_actions(ob)[0].keys() if ac not in existing_actions} 
                for ob in bpy.data.objects if ob.type == 'ARMATURE' and ob not in existing_objects}
        # get all the new meshes with the armature they came in with... (if any)
        new_meshes = {ob : ob.find_armature() for ob in bpy.data.objects if ob.type == 'MESH' and ob not in existing_objects}
        # get all the objects that we don't want... (if any)
        new_removals = [ob for ob in bpy.data.objects if ob not in existing_objects and ob not in new_armatures and ob not in new_meshes]
        # we only need one of each armature...
        for new_armature, new_actions in new_armatures.items():
            armature = None
            new_bbs = new_armature.data.bones
            for arm in armatures.keys():
                bbs = arm.data.bones
                # if an existing armature has all the imported armatures bones and vice versa then likely we have a copy...
                if get_armature_has_bones(arm, new_bbs) and get_armature_has_bones(new_armature, bbs):
                    # then check if it has the same proportions just to be sure of compatibility...
                    if get_armature_has_proportions(arm, new_bbs):
                        armature = arm
                        break
            # if we have an armature to assign to...        
            if armature and armature != new_armature:
                # append the new armature to be removed...
                new_removals.append(new_armature)
                # then iterate on all the actions...
                for new_action, fps_scale in new_actions.items():
                    # adding them to the assigned armature with their fps scale...
                    armatures[armature][new_action] = fps_scale
                # then iterate on any new meshes that use the new armature...
                for new_mesh in [me for me, ar in new_meshes.items() if ar == new_armature]:
                    # switch their armature modifiers to the assigned armature...
                    for mod in [mo for mo in new_mesh.modifiers if mo.type == 'ARMATURE']:
                        mod.object = armature
                    # and if they are to be a child, make it so...
                    if new_mesh.parent == new_armature:
                        new_mesh.parent = armature
            else:
                # otherwise this is a new armature we'll want to process it...
                armatures[new_armature] = new_actions#new_armatures[new_armature]
        # if we are importing meshes from this fbx... 
        if bools['Meshes']:
            # we can just append the new meshes to their lists...
            for mesh, arma in new_meshes.items():
                if arma:
                    sk_meshes.append(mesh)
                else:
                    st_meshes.append(mesh)
        else:
            # otherwise append them for removal...
            for mesh in new_meshes.keys():
                new_removals.append(mesh)
        # and append all the new objects we don't want to the main removal list...
        for new_removal in new_removals:
            removal_objects[new_removal] = True

    # now that we have everything imported we can process it...
    bpy.ops.object.select_all(action='DESELECT')
    # get rid of all the empties and extra things now before we start processing though...
    for remove_object in removal_objects.keys():
        if remove_object in armatures:
            del armatures[remove_object]
        if remove_object:
            bpy.data.objects.remove(remove_object)
    # armatures might need to have action scaled and/or baked to the active one...
    import_armatures(iport, armatures, active)
    # meshes should have their materials remapped and/or armatures switched to the active...
    import_meshes(iport, sk_meshes, st_meshes, active)
    # don't forget to set our fps back to what it was incase we imported actions...
    bpy.context.scene.render.fps = pre_fps
    # if we are going to apply any transforms...
    if iport.apply_scale or iport.apply_location or iport.apply_rotation:
        parenting = {}
        for sk_mesh in sk_meshes:
            sk_mesh.select_set(True)
            parenting[sk_mesh] = sk_mesh.parent
        for st_mesh in st_meshes:
            st_mesh.select_set(True)
            parenting[st_mesh] = sk_mesh.parent
        for armature in armatures.keys():
            armature.select_set(True)
        # clear all parenting but keep transforms...   
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        # apply all the transforms we want to apply...
        bpy.ops.object.transform_apply(location=iport.apply_location, rotation=iport.apply_rotation, scale=iport.apply_scale)
        # then re-apply parenting...
        for child, parent in parenting.items():
            child.parent = parent
    # set auto keying back to whatever it was...
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = is_auto_keying

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- IMPORT INTERFACE FUNCTIONS ---------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def show_import_meshes(self, iport):
    active = bpy.context.view_layer.objects.active
    is_active_armature = True if active and active.type == 'ARMATURE' else False
    layout = self.layout
    box = layout.box()
    row = box.row()
    row.prop(iport, "path_meshes", text="Mesh Folder")
    row.enabled = iport.meshes and iport.batch_meshes
    row = box.row()
    row.prop(iport, "mesh_fbx", text="Mesh File")
    row.enabled = iport.meshes and not iport.batch_meshes 
    row = box.row()
    row.prop(iport, "meshes")
    col = row.column()
    col.prop(iport, "batch_meshes")
    col.enabled = iport.meshes
    col = row.column()
    col.prop(iport, "deform_to_active")
    col.enabled = False # iport.meshes and is_active_armature
    
def show_import_actions(self, iport):
    active = bpy.context.view_layer.objects.active
    is_active_armature = True if active and active.type == 'ARMATURE' else False
    layout = self.layout
    box = layout.box()
    row = box.row()          
    row.prop(iport, "path_actions", text="Action Folder")
    row.enabled = iport.actions and iport.batch_actions
    row = box.row()
    row.prop(iport, "action_fbx", text="Action File")
    row.enabled = iport.actions and not iport.batch_actions 
    row = box.row()
    row.prop(iport, "actions")
    col = row.column()
    col.enabled = iport.actions
    col.prop(iport, "batch_actions")
    # can only bake to controls if the active object is armature...
    col = row.column()
    col.prop(iport, "bake_to_active")
    col.enabled = iport.actions and is_active_armature
    row = box.row()
    row.prop(iport, "scale_keyframes")
    row.prop(bpy.context.scene.render, "fps", text="Framerate")
    row.prop(iport.fbx_props, "anim_offset")
    row.enabled = iport.actions
    row = box.row()
    row.prop(iport, "use_default_retargeting_translation", icon='ERROR')
    row.enabled = iport.actions

def show_import_advanced(self, iport):
    layout = self.layout
    row = layout.row()
    row.prop(iport, "show_advanced")
    if iport.show_advanced:
        box = layout.box()
        row = box.row()
        row.prop(iport.fbx_props, "ignore_leaf_bones")
        row.prop(iport, "add_root")
        row.prop(iport.fbx_props, "manual_orient")
        row = box.row()
        row.label(text="Primary Bone Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(iport.fbx_props, "primary_bone_axis", text="")
        row.label(text="Object Forward Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(iport.fbx_props, "axis_forward", text="")
        col.enabled = iport.fbx_props.manual_orient
        row = box.row()
        row.label(text="Secondary Bone Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(iport.fbx_props, "secondary_bone_axis", text="")
        row.label(text="Object Up Axis:")
        col = row.column()
        col.ui_units_x = 5
        col.prop(iport.fbx_props, "axis_up", text="")
        col.enabled = iport.fbx_props.manual_orient
        row = box.row()
        row.prop(iport, 'apply_location')
        row.prop(iport, 'apply_rotation')
        row.prop(iport, "apply_scale")