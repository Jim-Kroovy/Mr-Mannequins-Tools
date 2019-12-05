import bpy
import os

#---------- NOTES -----------------------------------------------------------------------------

# RIGHT! I've been working with blender, UE4 and Mr Mannequin since 2015!
# And only recently figured out this magic for exporting perfectly from blender to the UE4 Mannequin without retargeting! :D

# Animation location keyframes must have a scale of 100 in default blender units... 
# this can be achieved by either creating rigs and meshes at a 100 blender units scale...
# or setting the scenes "Unit Scale" to 0.01... OR using this export logic...

# If you try importing the mannequin FBX from UE4, you'll notice the empty parent has a scale of 0.01...
# then try applying that scale to the armature and see if you can export an animation onto the mannequin rig without any errors :P

# Now we could just leave the scale alone once it's been imported and export happily on to the UE4 mannequin BUT...

# The problem with setting the scene units to 0.01 or building rigs and meshes to a scale of 100
# is that it can cause all sorts of troubles in blender... for example if you want to animate anything using blenders physics :p

# So to keep everything happy in blender as well as UE4 i found this python method...
# of setting scale before exporting, then exporting using the FBX ALL scale option

# Rotation doesnt need to be scaled because it is relative (eg. -180 to 180)
# the same goes for scale as once it has been applied to the armature it's still keyframed at a value of 0 - inf

# So that was a bunch waffle that i might of talked about in a video already... but it has a place here :p

# A stands for Animation, O stands for Object, E stands for Export

#---------- FUNCTIONS -------------------------------------------------------------------------

# one little message box function... (just in case)
def ShowMessage(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
            
# sets animation location scale to and from UE4... (this bit can take a few minutes if you have many keyframes or are batch exporting, it does a lot of work!)
def A_UE4_Scale(action, float, armature):
    bpy.ops.object.mode_set(mode='POSE')
    # iterate through the location curves...
    for curve in [fcurve for fcurve in action.fcurves if fcurve.data_path.endswith('location')]:
        # and iterate through the keyframe values... print(curve.data_path, curve.array_index)
        for key in curve.keyframe_points:
            # should probably find a better method of getting bone name from path but curve.data_path[12:-11] works for now... (curve.data_path = "pose.bones[bone.name].location")
            if curve.data_path[12:-11] in armature.pose.bones:
                # multiply keyframed location by either 100 or 0.01... (see above)
                key.co[1] = key.co[1] * float
                key.handle_left[1] = key.handle_left[1] * float 
                key.handle_right[1] = key.handle_right[1] * float
    # back to object mode...
    bpy.ops.object.mode_set(mode='OBJECT')    

# prepares animation for export by setting the start and end frame and clearing any left over pose data during batch exporting actions...
def A_Prep(action):
    #set the current frame to zero...(stops the current frame getting keyed as the rest pose on export)
    if (bpy.context.scene.frame_current > action.frame_range[0] and bpy.context.scene.frame_current < action.frame_range[1]) or (bpy.context.scene.frame_current == action.frame_range[0] or bpy.context.scene.frame_current == action.frame_range[1]):
        if action.frame_range[0] == 0:
            bpy.context.scene.frame_set(action.frame_range[1] + 1)
        else:
            bpy.context.scene.frame_set(action.frame_range[0] - 1)
    # set the start and end frames...
    bpy.context.scene.frame_start = action.frame_range[0]
    bpy.context.scene.frame_end = action.frame_range[1]
    # hop into pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    # to reveal any hidden bones before selecting everything and clearing all transforms...
    bpy.ops.pose.reveal(select=True)
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    # then back to object mode...
    bpy.ops.object.mode_set(mode='OBJECT')

# sets object scale to and from UE4... (see above)
def O_UE4_Scale(objects, float):
    active = bpy.context.view_layer.objects.active
    for obj in objects:
        # set the objects scale to either 100 or 0.01 if its parent is not selected... (see above)
        if not obj.parent in objects:
            obj.scale = [obj.scale[0] * float, obj.scale[1] * float, obj.scale[2] * float]
    # loop through and apply the given scale... (selected objects appear to always be arranged in order of hierarchy so this works)
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # return active object...
    bpy.context.view_layer.objects.active = active

# exports armature animation... (to seperate FBX's if desired)
def E_Animations(objects, MMT, scale):
    armature = bpy.context.view_layer.objects.active
    selected = objects
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
    # if we want to export each animation to its own FBX...
    if MMT.E_batch_animations:
        # get name references for the pose bones...
        bone_names = [bone.name for bone in armature.pose.bones]
        # check every action in the blend...
        for action in bpy.data.actions:
            # if the action could be used by any bones in the armature...
            if any(name in fcurve.data_path for fcurve in action.fcurves for name in bone_names):
                # set it as the active action...
                armature.animation_data.action = action
                # assemble the filepath/name...                    
                path = os.path.join(bpy.path.abspath(MMT.E_path_animations), A_name + "_" + action.name + ".FBX")
                # prepare the animation...
                A_Prep(action)
                # set the animations scale...
                A_UE4_Scale(action, scale, armature)
                # export...
                bpy.ops.export_scene.fbx(filepath=path, check_existing=True, filter_glob="*.fbx", use_selection=True, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=False, object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'}, use_mesh_modifiers=MMT.E_apply_modifiers, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', use_mesh_edges=False, use_tspace=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True, armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False, bake_anim_force_startend_keying=MMT.E_startend_keys, bake_anim_step=MMT.E_anim_step, bake_anim_simplify_factor=MMT.E_simplify_factor, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
    # if we only want to export the active action...
    else:
        try:
            # set only the active action...
            action = armature.animation_data.action
            # assemble the filepath/name...
            path = os.path.join(bpy.path.abspath(MMT.E_path_animations), A_name + "_" + action.name + ".FBX")
            # prepare the animation...
            A_Prep(action)
            # set the animations scale...
            A_UE4_Scale(action, scale, armature)
            # export...
            bpy.ops.export_scene.fbx(filepath=path, check_existing=True, filter_glob="*.fbx", use_selection=True, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=False, object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'}, use_mesh_modifiers=MMT.E_apply_modifiers, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', use_mesh_edges=False, use_tspace=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True, armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False, bake_anim_force_startend_keying=MMT.E_startend_keys, bake_anim_step=MMT.E_anim_step, bake_anim_simplify_factor=MMT.E_simplify_factor, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y') 
        except:
            ShowMessage(message = "No active action to export with the armature", title = "Export Error", icon = 'ERROR')
            print("No active action to export with the armature!")
    # after animation has been exported return armature name...
    armature.name = A_name                
    # and reselect the original selection...
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    armature.data.layers = layers

# exports selected objects... (to seperate FBX's if desired)
def E_Meshes(objects, MMT):
    active = bpy.context.view_layer.objects.active
    selected = objects
    for obj in selected:
        # only deselect if batch exporting meshes...
        if MMT.E_batch_meshes:
            # deselect everything each loop so everything stays seperate...
            bpy.ops.object.select_all(action='DESELECT')
            # select only the object...
            obj.select_set(True)
        # if an object has any armature modifiers...
        if any(mod.type == 'ARMATURE' and mod.object == active for mod in obj.modifiers) and obj.type == 'MESH':
            T = active
            # select the armature target so it gets exported with the object...           
            T.select_set(True)
            # save armatures name...
            T_name = T.name
            # if there is more than one armature modifier then only one will not generate an extra root bone...
            T.name = 'Armature'
            # set object to active... 
            bpy.context.view_layer.objects.active = obj #might not be necessery??
            if not active.JK_MMT.Character_props.Is_female:
                if "breast_l" in obj.vertex_groups: 
                    obj.vertex_groups.remove(obj.vertex_groups["breast_l"])
                if "breast_r" in obj.vertex_groups:
                    obj.vertex_groups.remove(obj.vertex_groups["breast_r"])
            # assemble the filepath/name...
            if MMT.E_batch_meshes:
                path = os.path.join(bpy.path.abspath(MMT.E_path_meshes), obj.name + ".FBX")
            else:
                path = os.path.join(bpy.path.abspath(MMT.E_path_meshes), T_name + "_" + str(len(selected) - 1) + ".FBX")
            # export without animation...
            bpy.ops.export_scene.fbx(filepath=path, check_existing=True, filter_glob="*.fbx", use_selection=True, use_active_collection=False, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=False, object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'}, use_mesh_modifiers=MMT.E_apply_modifiers, use_mesh_modifiers_render=True, mesh_smooth_type='FACE', use_mesh_edges=False, use_tspace=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True, armature_nodetype='NULL', bake_anim=False, bake_anim_use_all_bones=False, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False, bake_anim_force_startend_keying=False, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
            # after object has been exported return armature name...
            T.name = T_name
            # break if not batch exporting meshes...
            if not MMT.E_batch_meshes:
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

#---------- EXECUTION -------------------------------------------------------------------------

def Export(MMT):
    # hide deform bones so they dont get selected/processed...
    if not bpy.context.object.JK_MMT.Hide_deform_bones:
        bpy.context.object.JK_MMT.Hide_deform_bones = True
    # scale by 100 for UE4 from a default of 1... (so 100 multiplied by any custom unit scale should result in the correct size?)
    unit_scaling = 100 * bpy.context.scene.unit_settings.scale_length    
    # if an object named armature already exists change it's name...
    if "Armature" in bpy.data.objects:
        bpy.data.objects["Armature"].name = "RENAMED_FOR_UE4_EXPORT"
    # set scale for export...
    O_UE4_Scale(bpy.context.selected_objects, unit_scaling)
    # if we want to export animation...
    if MMT.E_animations:
        E_Animations(bpy.context.selected_objects, MMT, unit_scaling)
    # if we want to export meshes...
    if MMT.E_meshes:
        E_Meshes(bpy.context.selected_objects, MMT)
        
# used for testing...
#Export(bpy.context.scene.JK_MMT)