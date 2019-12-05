# Contributor(s): James Goldsworthy (Jim Kroovy)

# Support: https://twitter.com/JimKroovy
#          https://www.facebook.com/JimKroovy
#          http://youtube.com/c/JimKroovy

# This code is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Currently all the default meshes, textures, materials and armatures provided
# with the add-on in the "MMT_Stash" folder are property of Epic Games and should
# come under the UE4 EULA <https://www.unrealengine.com/en-US/eula>.

bl_info = {
    "name": "Mr Mannequins Tools",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 2),
    "blender": (2, 81, 0),
    "location": "3D View > Tools",
    "description": "Loads, saves, imports and exports UE4 Mannequin compatible armatures and meshes",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Characters",
}

import bpy
import sys
import os
import importlib # i dont think executing importlib.reload(script) on scripts is needed as they all run from scene property values but doing it anyway just to be on the safe side...
from . import (MMT_Export_FBX, MMT_Import_FBX, MMT_Options_Retarget, MMT_Options_Rig, MMT_Stash_Object, MMT_Stash_Material, MMT_Update)

from bpy.props import (StringProperty, BoolProperty, BoolVectorProperty, IntProperty, IntVectorProperty, FloatProperty, EnumProperty, PointerProperty, CollectionProperty)
                       
from bpy.types import (Panel, Menu, WorkSpaceTool, Operator, PropertyGroup, AddonPreferences)

from bpy.utils import (register_class, unregister_class)

from mathutils import Matrix, Vector

from bpy.app.handlers import persistent

#---------- NOTES ------------------------------------------------------------------------------

# This is still a work in progress! I'm still not all that happy with the UI...
# and there are a whole bunch of options and functionality to create and finalize...
# i've got the main pieces of logic sussed out for this initial release and they should not need to change much...

# i suppose if you are reading this then you're probably trying to figure out how it all works...
# there are two parts to this add-on, the main and most useful part is the UE4 export FBX logic... (see MMT_Export_FBX.py for more info)
# which exports a UE4 mannequin compatible .FBX, no more retargeting needed! Woop!

# Then there is the stashing logic which enables the user to save their meshes/materials and reload them in other blend files...
# First the user creates a stash folder somewhere, then they are able write, load and remove library .blends to and from this location...
# the selection of library .blends is through drop down enum menus that display whats in the currently selected stash...
# users can have multiple stashes and the current stash can also be changed through a drop down enum menu...

# When a mesh/material is added to a stash a reference clean up text is written and stored with it...
# then when a mesh/material is loaded that clean up text is executed in order to set those references relative to what is in the current .blend...
# if a saved reference is not in the current .blend then it is linked to the scene... (see MMT_Stash_Object.py and MMT_Stash_Material.py for more info)

# I did want to make the rig properties specific to armatures but doing that makes them a pain to animate so they are attached to objects instead...
# which isn't all bad as that also means that in the future i can easily drive character mesh shape keys and options from the armature within the same actions...

# MMT stands for Mr Mannequins Tools, E stands for export, I stands for import, S stands for Stash, L stands for Load, A stands for Add, O stands for option, U stands for update, C stands for custom...
# and JK/Jk/jk stands for Jim Kroovy and is the creator prefix i use for anything that might be used elsewhere... (makes for easier searching in most editing programs)

# Dynamically generated EnumProperty items must be referenced from Python!!!
# You must maintain a reference to dynamically generated EnumProperty items from Python or else Blender
# will not behave properly (symptomps are garbage strings, utf-8 decode errors, and crashes). For more information, see:
#    https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
#    https://developer.blender.org/T50426

#---------- FUNCTIONS --------------------------------------------------------------------------

# one little message box function... (just in case)
def ShowMessage(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# get stashed items from default and custom stashes...
def Get_Stashed_MMT(MMT_path, armature, S_path, type):
    default_dir = os.path.join(MMT_path, "MMT_Stash")
    custom_dir = S_path
    items = []
    # gather items from default stash by type...
    for filename in os.listdir(default_dir):
        if type in filename:
            if type == 'MESH':
                if armature.JK_MMT.Rig_type in filename:
                    name_start = (15 if "MANNEQUIN" in filename else 9)
                    items.append((os.path.join(default_dir, filename), filename[name_start:-6], os.path.join(default_dir, filename)))
            else:
                items.append((os.path.join(default_dir, filename), filename[9:-6], os.path.join(default_dir, filename)))
    # gather items from custom stash by type...                
    if os.path.exists(custom_dir) and custom_dir != default_dir:
        for filename in os.listdir(custom_dir):
            if type in filename:
                if type == 'MESH':
                    if armature.JK_MMT.Rig_type in filename:
                        name_start = (15 if "MANNEQUIN" in filename else 9)
                        items.append((os.path.join(custom_dir, filename), filename[name_start:-6], os.path.join(custom_dir, filename)))
                else:
                    items.append((os.path.join(custom_dir, filename), filename[9:-6], os.path.join(custom_dir, filename)))
    if len(items) > 0:
        return items
    else:
        return [('None', "None", 'None')]

# gets all the saved stash paths from add-on preferences...

Get_Stashes_Result_Reference=[]

def Get_Stashes(self, context):
    stashes = []
    prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
    if len(prefs.S_paths) > 0:
        for stash in prefs.S_paths:
            if os.path.exists(stash[0]):
                stashes.append(stash)
            else:
                prefs.S_paths.remove(stash)

    # There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
    # https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
    global Get_Stashes_Result_Reference
    Get_Stashes_Result_Reference=stashes

    if len(stashes) > 0:
        return stashes
    else:
        return [('None', "None", 'None')]
    
# gets all .FBXs in the given folder location...
def Get_Imports_FBX(self, context, i_path):
    items = []
    if os.path.exists(bpy.path.abspath(i_path)):
        for filename in os.listdir(bpy.path.abspath(i_path)):
            if filename.upper().endswith(".FBX"):
                items.append((os.path.join(i_path, filename), filename[:-4], os.path.join(i_path, filename)))
    return items            

Get_Characters_Result_Reference=[]

# return the possible character meshes a rig can be set to...
def Get_Character_Meshes(self, context):
    items = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if obj.data.JK_MMT.Character_type == self.Rig_type and self.Rig_type != 'NONE':
                if not any(item[1] == obj.data.JK_MMT.Character_name for item in items):
                    items.append((obj.name, obj.data.JK_MMT.Character_name, obj.data.JK_MMT.Character_name))
                #if any(modifier.type == 'ARMATURE' for modifier in obj.modifiers
    
    # There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
    # https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
    global Get_Characters_Result_Reference
    Get_Characters_Result_Reference=items
    
    if len(items) > 0:
        return items
    else:
        return [('None', "None", 'None')]            

# gets the local matrix of a pose bone after constraints and drivers have been applied...
def Get_Local_Bone_Matrix(p_bone):
    matrix = p_bone.matrix
    rest = p_bone.bone.matrix_local.copy()
    rest_inv = rest.inverted()
    if p_bone.parent:
        parent_matrix = p_bone.parent.matrix.copy()
        parent_inv = parent_matrix.inverted()
        parent_rest = p_bone.parent.bone.matrix_local.copy()
    else:
        parent_matrix = Matrix()
        parent_inv = Matrix()
        parent_rest = Matrix()
    
    local_matrix = rest_inv @ (parent_rest @ (parent_inv @ matrix))

    # Compensate for non-local location - causes errors might try to fix in the future?
    #if not pose_bone.bone.use_local_location:
        #location = local_matrix.to_translation() * (parent_rest.inverted() @ rest).to_quaternion()
        #local_matrix.translation = location
    return local_matrix 

def Set_Rotation_Limits(p_bone, constraint, zero_overide):
    if zero_overide:
        constraint.use_limit_x, constraint.min_x, constraint.max_x = True, 0, 0
        constraint.use_limit_y, constraint.min_y, constraint.max_y = True, 0, 0
        constraint.use_limit_z, constraint.min_z, constraint.max_z = True, 0, 0
    else:
        constraint.use_limit_x, constraint.min_x, constraint.max_x = p_bone.use_ik_limit_x, p_bone.ik_min_x, p_bone.ik_max_x
        constraint.use_limit_y, constraint.min_y, constraint.max_y = p_bone.use_ik_limit_y, p_bone.ik_min_y, p_bone.ik_max_y
        constraint.use_limit_z, constraint.min_z, constraint.max_z = p_bone.use_ik_limit_z, p_bone.ik_min_z, p_bone.ik_max_z
                
# switch handler used to work around update functions not firing on keyframe change... (try not to add very much here as it could kill performance)
@persistent
def Post_Frame_Handler(dummy):
    # for each object...
    for obj in bpy.data.objects:
        # if its an armature...
        if obj.type == 'ARMATURE':
            # and it's a mannequin armature...
            if obj.JK_MMT.Rig_type == 'MANNEQUIN':
                # aaaand it's using switchable IK vs FK or IK parenting...
                if obj.JK_MMT.IK_parenting == '2' or obj.JK_MMT.IKvsFK_limbs == '2':
                    # iterate through all the pose bones... (this should be improved by saving references to all the IK targets and iterating through them instead)
                    #for p_bone in obj.pose.bones:
                    for data in obj.JK_MMT.IK_chain_data:
                        # check/set each switch in order to fire update functions during play back...
                        if obj.JK_MMT.IKvsFK_limbs == '2':
                            if data.Chain_use_fk != data.Current_switches[1]:
                                data.Chain_use_fk = data.Chain_use_fk
                            # always set the ik rotation overide bool so the update gets fired and keeps rotation limits equal to ik limits...   
                            data.Chain_ik_rotation_overide = data.Chain_ik_rotation_overide
                        if obj.JK_MMT.IK_parenting == '2':
                            if data.Chain_use_parent != data.Current_switches[0] and not data.Chain_use_fk:
                                data.Chain_use_parent = data.Chain_use_parent
                        # always set the IK inlfuence so the update gets fired and keeps the constraints influence equal to the saved influence
                        data.Chain_ik_influence = data.Chain_ik_influence
# should i append/remove handlers on register/unregister?                                           
bpy.app.handlers.frame_change_post.append(Post_Frame_Handler)

#---------- CLASSES ----------------------------------------------------------------------------
# add-on preferences... not much here for now but it stores all the stash file paths between .blends...    
class JK_MMT_Prefs(AddonPreferences):
    bl_idname = "MrMannequinsTools"
    # stores file string sets for stash enum...
    S_paths = []
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="See tool panel for options")

# There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
# https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
Get_Stashed_Armatures_Results_Reference = []
Get_Stashed_Meshes_Results_Reference = []
Get_Stashed_Materials_Results_Reference = []
Get_Import_Animations_Results_Reference = []
Get_Import_Meshes_Results_Reference = []

# all the main add-on options...
class JK_MMT_Props(PropertyGroup):

    def Get_Stashed_Armatures(self, context):
        result = Get_Stashed_MMT(self.MMT_path, bpy.context.object, self.S_path, 'ARMATURE')
        global Get_Stashed_Armatures_Results_Reference
        Get_Stashed_Armatures_Results_Reference = result
        return result

    def Get_Stashed_Meshes(self, context):
        result = Get_Stashed_MMT(self.MMT_path, bpy.context.object, self.S_path, 'MESH')
        global Get_Stashed_Meshes_Results_Reference
        Get_Stashed_Meshes_Results_Reference = result
        return result

    def Get_Stashed_Materials(self, context):
        result = Get_Stashed_MMT(self.MMT_path, bpy.context.object, self.S_path, 'MATERIAL')
        global Get_Stashed_Materials_Results_Reference
        Get_Stashed_Materials_Results_Reference = result
        return result

    def Get_Import_Animations(self, context):
        result = Get_Imports_FBX(self, context, self.I_path_animations)   
        global Get_Import_Animations_Results_Reference
        Get_Import_Animations_Results_Reference = result
        return result
    
    def Get_Import_Meshes(self, context):
        result = Get_Imports_FBX(self, context, self.I_path_meshes)   
        global Get_Import_Meshes_Results_Reference
        Get_Import_Meshes_Results_Reference = result
        return result    
  
    MMT_path: StringProperty(
        name="",
        description="Where the addon scripts are",
        default=os.path.dirname(os.path.realpath(__file__)),
        maxlen=1024,
        )
    
    MMT_last_active: StringProperty(
        name="",
        description="Last active armature name",
        default="",
        maxlen=1024,
        )
        
    S_path: EnumProperty(
        name="Stash",
        description="Where you want to save and load mesh/materials to and from",
        items=Get_Stashes,
        default=None
        )
    
    S_path_add: StringProperty(
        name="",
        description="Directory to create stash folder in. Must have write permissions",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )
    
    S_path_folder: StringProperty(
        name="Folder",
        description="The name used for a new stash folder. If folder already exists it gets added to stashes",
        default="UE4",
        maxlen=1024,
        )
    
    L_apply_scale_armatures: BoolProperty(
        name="Apply Scale",
        description="Automatically apply scaling given for the current scenes unit scale",
        default = True
        )
    
    A_overwrite_existing_meshes: BoolProperty(
        name="Overwrite Meshes",
        description="Overwrite existing meshes when saving them. Default mannequin meshes cannot be overwritten",
        default = False
        )
    
    L_apply_scale_meshes: BoolProperty(
        name="Apply Scale",
        description="Automatically apply scaling given for the current scenes unit scale",
        default = True
        )
     
    L_autoload_materials: BoolProperty(
        name="Auto-Load Materials",
        description="Automatically load any new materials when loading a mesh",
        default = True
        )
        
    L_active_parent: BoolProperty(
        name="Parent to active",
        description="Parent loaded mesh to active armature",
        default = True
        )
    
    A_autosave_materials: BoolProperty(
        name="Auto-Save Materials",
        description="Automatically save all materials used by selected meshes",
        default = True
        )
    
    A_overwrite_existing_materials: BoolProperty(
        name="Overwrite Materials",
        description="Overwrite existing materials when saving them. Default mannequin materials cannot be overwritten",
        default = False
        )
        
    A_pack_images: BoolProperty(
        name="Pack Images",
        description="Pack images into material files when saving them. If false any images use original filepaths",
        default = True
        )
    
    L_rigs: EnumProperty(
        name="Rig",
        description="Armature to load",
        items=Get_Stashed_Armatures,
        default=None
        )
        
    L_meshes: EnumProperty(
        name="Mesh",
        description="Mesh to load/remove",
        items=Get_Stashed_Meshes,
        default=None
        )
        
    L_materials: EnumProperty(
        name="Material",
        description="Material to load/remove",
        items=Get_Stashed_Materials,
        default=None
        )
        
    E_meshes: BoolProperty(
        name="Export Meshes",
        description="Export selected meshes that have an armature modifier to the active rig",
        default = False
        )
        
    E_batch_meshes: BoolProperty(
        name="Batch Export Meshes",
        description="Export each selected mesh to its own FBX. If false all selected meshes gets exported into one FBX",
        default = False
        )

    E_animations: BoolProperty(
        name="Export Animations",
        description="Export the current action used by the active rig",
        default = False
        )
                
    E_batch_animations: BoolProperty(
        name="Batch Export Animations",
        description="Export all actions the rig can use to their own FBXs. If false only export active action",
        default = False
        )
        
    E_apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifers on export (except armature ones). If true prevents exporting shape keys",
        default = False
        )
        
    E_startend_keys: BoolProperty(
        name="Start/End Keyframes",
        description="Force start and end keyframes on export",
        default = False
        )
    
    E_anim_step: FloatProperty(
        name="Sample Rate", 
        description="How often to evaluate animated values (in frames)", 
        default=1.0
        )
        
    E_simplify_factor: FloatProperty(
        name="Simplify", 
        description="How much to simplify baked values (0.0 to disable, the higher the more simplified)", 
        default=1.0
        )
                
    E_path_meshes: StringProperty(
        name="Mesh Export Folder",
        description="Export meshes to this folder",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )
    
    E_path_animations: StringProperty(
        name="Animation Export Folder",
        description="Export animations to this folder",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )
        
    I_animations: BoolProperty(
        name="Import Animations",
        description="Import Animations",
        default = False
        )
        
    I_meshes: BoolProperty(
        name="Import Meshes",
        description="Import Meshes",
        default = False
        )
    
    I_animation_fbxs: EnumProperty(
        name="FBX",
        description="Animation to import and convert",
        items=Get_Import_Animations,
        default=None
        )
    
    I_mesh_fbxs: EnumProperty(
        name="FBX",
        description="Animation to import and convert",
        items=Get_Import_Meshes,
        default=None
        )
    
    I_batch_animations: BoolProperty(
        name="Batch Import Animations",
        description="Import all animations from animation import folder",
        default = True
        )
        
    I_batch_meshes: BoolProperty(
        name="Batch Import Meshes",
        description="Import all meshes from animation import folder",
        default = True
        )
    
    I_pre_scale_keyframes: BoolProperty(
        name="Pre Scale Keyframes",
        description="Scale animation length before converting to Mr Mannequin. If false scales animation length after conversion which seems to stops extra keyframes being generated but may impact accuracy",
        default = True
        )
    
    I_root_motion: BoolProperty(
        name="Convert Root Motion",
        description="Convert root motion from imported armature to targets root bone. If false no root motion will be used",
        default = True
        )
    
    I_key_controls: BoolProperty(
        name="Key Controls",
        description="Keyframe 'Mute Default Constraints' off on the first frame of the imported animation. Also keyframes the IK targets 'Use FK'/'Use Parent' properties if applicable. These controls always get switched off for accurate importation",
        default = True
        )
        
    I_key_location: BoolProperty(
        name="Key Location",
        description="Keyframe locations from the imported animation. If false only keyframes rotations. WARNING: Work in progress, currently kills root and pelvis location keyframes!",
        default = True
        )
            
    I_rig_to_active: BoolProperty(
        name="Rig to Active",
        description="Whether we try to assign mesh armature modifiers to the active armature or just import the mesh with its imported armature. Only use this on imported mesh/armatures that very closely resemble the active armature and have the same bone names",
        default = False
        )
        
    I_import_to_retarget: BoolProperty(
        name="Import to Retarget",
        description="Jump straight into armature retargeting after import. Currently we only have a Mr Mannequin template to retarget with",
        default = False
        )
            
    I_user_props: BoolProperty(
        name="Import User Properties",
        description="Import user properties as custom properties. WARNING! Setting True might cause import errors with some properties found in .FBXs",
        default = False
        )
            
    I_frame_offset: IntProperty(
        name="Frame Offset",
        description="Offset imported actions keyframes to start from this frame",
        default = 1
        )
            
    I_path_animations: StringProperty(
        name="Animation Import Folder",
        description="Directory to import animations from",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )
    
    I_path_meshes: StringProperty(
        name="Mesh Import Folder",
        description="Directory to import meshes from",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )

# mesh specific options...        
class JK_MMT_Character_Props(PropertyGroup):
    
    Character_type: StringProperty(
        name="Type",
        description="The rig type used by the character mesh",
        default="None",
        maxlen=1024,
        )
    
    Character_name: StringProperty(
        name="Name",
        description="The name used for the character",
        default="None",
        maxlen=1024,
        )
    
    Is_default: BoolProperty(
        name="Is MMT Default",
        description="Is this a default mesh that i've provided",
        default=False
        )
        
    Is_female: BoolProperty(
        name="Is Female",
        description="Does this mesh need female bones. Sometimes male and female meshes might use the same points of rotation so this setting is relevant",
        default=False
        )
    # not currently in use...
    LOD_count: IntProperty(
        name="LOD Count",
        description="Number of different levels of detail. Not including the base mesh (LOD0)",
        default = 0
        )
    
    # think i'll be putting a collection or two here for morphable characters in the future...    
    #Morph_data:

# There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
# https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
Get_Socket_Targets_Results_Reference = []
Get_Socket_Subtargets_Results_Reference = []

# socket properties...
class JK_MMT_Socket_Props(PropertyGroup):
    
    def Get_Targets(self, context):
        items = [('None', "None", 'None')]
        if len(bpy.data.objects) > 0:
            items = items + [(obj.name, obj.name, obj.type) for obj in bpy.data.objects]
        # There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
        # https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
        global Get_Socket_Targets_Results_Reference
        Get_Socket_Targets_Results_Reference=items
        return items
    
    def Get_Subtargets(self, context):
        items = [('None', "None", 'None')]
        if self.Socket_target != 'None':
            target = bpy.data.objects[self.Socket_target]
            if target.type == 'ARMATURE':
                items = items + [(bone.name, bone.name, "Attach to " + bone.name) for bone in target.pose.bones]
            elif target.type == 'MESH':
                items = items + [(group.name, group.name, "Attach to " + group.name) for group in target.vertex_groups]
        # There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
        # https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
        global Get_Socket_Subtargets_Results_Reference
        Get_Socket_Subtargets_Results_Reference=items
        return items
    
    def Update_Subtarget(self, context):
        if self.Is_attached:
            if self.Socket_subtarget != 'None':
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].subtarget = self.Socket_subtarget
            else:
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].subtarget = ""
    
    def Update_Target(self, context):
        if self.Is_attached:
            if self.Socket_target != 'None':
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].target = bpy.data.objects[self.Socket_target]
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].subtarget = ""
            else:
                self.Is_attached = False
                    
    def Update_Attach(self, context):
        if self.Is_attached:          
            constraint = self.id_data.constraints.new('COPY_TRANSFORMS')
            constraint.name = "MMT SOCKET - " + constraint.name
            if self.Socket_target != 'None':
                constraint.target = bpy.data.objects[self.Socket_target]
            if self.Socket_subtarget != 'None':
                constraint.subtarget = self.Socket_subtarget
        else:       
            for constraint in self.id_data.constraints:
                if constraint.name.startswith("MMT SOCKET - "):
                    self.id_data.constraints.remove(constraint)
                                               
    Socket_target: EnumProperty(
        name="Target",
        description="The object to attach mesh/armature to",
        items=Get_Targets,
        default=None,
        update=Update_Target
        )
    
    Socket_subtarget: EnumProperty(
        name="Sub Target",
        description="The bone/vertex group to attach mesh/armature to (if required)",
        items=Get_Subtargets,
        default=None,
        update=Update_Subtarget
        )        
    
    Is_attached: BoolProperty(
        name="Is Attached",
        description="Is this mesh/armature currently attached to the target",
        default=False,
        update=Update_Attach
        )

# IK chain specific options...        
class JK_MMT_IK_Props(PropertyGroup):
    
    # don't need this function for now, might bring it back for more dynamic chains in future updates...
    #def Get_IK_Chain(self):    
        #p_bone = bpy.context.object.pose.bones[self.Owner_name]
        #constraint = p_bone.constraints["IK"]
        #chain_bones = [p_bone.name]
        #for i in range(1, constraint.chain_count):
            #p_bone = p_bone.parent
            #chain_bones.append(p_bone.name)
        #return chain_bones
                                
    def Update_Use_Parent(self, context):
        if self.Chain_use_parent != self.Current_switches[0]:
            armature = bpy.context.object
            ik_parent = self.Parent_name
            ik_pole = self.Pole_name                
            ik_parent_local = ik_parent[:2] + "_local" + ik_parent[2:]
            ik_pole_local = ik_parent[:2] + "_local" + ik_pole[2:]
            if self.Chain_use_parent and not self.Chain_use_fk:
                ik_bone_local = armature.pose.bones[ik_parent_local] 
                matrix = Get_Local_Bone_Matrix(ik_bone_local)
                ik_bone_local.location = matrix.to_translation()
                ik_bone_local.rotation_quaternion = matrix.to_quaternion()                
                ik_bone_local.constraints.remove(ik_bone_local.constraints["Use Parent - Copy Transforms"])
                
                pole_bone_local = armature.pose.bones[ik_pole_local] 
                matrix = Get_Local_Bone_Matrix(pole_bone_local)
                pole_bone_local.location = matrix.to_translation()
                pole_bone_local.rotation_quaternion = matrix.to_quaternion()                
                pole_bone_local.constraints.remove(pole_bone_local.constraints["Use Parent - Copy Transforms"])
                
                ik_bone = armature.pose.bones[ik_parent]
                constraint = ik_bone.constraints.new("COPY_TRANSFORMS")
                constraint.name = "Use Parent - Copy Transforms"
                constraint.target = armature
                constraint.subtarget = ik_parent_local
                
                pole_bone = armature.pose.bones[ik_pole]
                constraint = pole_bone.constraints.new("COPY_TRANSFORMS")
                constraint.name = "Use Parent - Copy Transforms"
                constraint.target = armature
                constraint.subtarget = ik_pole_local
                if ik_bone in bpy.context.selected_pose_bones:
                    if bpy.context.active_object.data.bones.active == ik_bone.bone:
                        bpy.context.active_object.data.bones.active = ik_bone_local.bone
                    ik_bone.bone.select = False
                    ik_bone_local.bone.select = True
                if pole_bone in bpy.context.selected_pose_bones:
                    if bpy.context.active_object.data.bones.active == pole_bone.bone:
                        bpy.context.active_object.data.bones.active = pole_bone_local.bone
                    pole_bone.bone.select = False
                    pole_bone_local.bone.select = True                 
            else:
                ik_bone = armature.pose.bones[ik_parent] 
                matrix = Get_Local_Bone_Matrix(ik_bone)
                ik_bone.location = matrix.to_translation()
                ik_bone.rotation_quaternion = matrix.to_quaternion()                
                ik_bone.constraints.remove(ik_bone.constraints["Use Parent - Copy Transforms"])
                
                pole_bone = armature.pose.bones[ik_pole] 
                matrix = Get_Local_Bone_Matrix(pole_bone)
                pole_bone.location = matrix.to_translation()
                pole_bone.rotation_quaternion = matrix.to_quaternion()                
                pole_bone.constraints.remove(pole_bone.constraints["Use Parent - Copy Transforms"])
                
                ik_bone_local = armature.pose.bones[ik_parent_local]
                constraint = ik_bone_local.constraints.new("COPY_TRANSFORMS")
                constraint.name = "Use Parent - Copy Transforms"
                constraint.target = armature
                constraint.subtarget = ik_parent
                
                pole_bone_local = armature.pose.bones[ik_pole_local]
                constraint = pole_bone_local.constraints.new("COPY_TRANSFORMS")
                constraint.name = "Use Parent - Copy Transforms"
                constraint.target = armature
                constraint.subtarget = ik_pole
                if ik_bone_local in bpy.context.selected_pose_bones:
                    if bpy.context.active_object.data.bones.active == ik_bone_local.bone:
                        bpy.context.active_object.data.bones.active = ik_bone.bone
                    ik_bone_local.bone.select = False
                    ik_bone.bone.select = True
                if pole_bone_local in bpy.context.selected_pose_bones:
                    if bpy.context.active_object.data.bones.active == pole_bone_local.bone:
                        bpy.context.active_object.data.bones.active = pole_bone.bone
                    pole_bone_local.bone.select = False
                    pole_bone.bone.select = True
            
            self.Current_switches[0] = self.Chain_use_parent
                                               
    def Update_Use_FK(self, context):
        if self.Chain_use_fk != self.Current_switches[1]:
            armature = bpy.context.object #self.id_data
            ik_owner = armature.pose.bones[self.Owner_name]
            ik_target = self.Target_name
            ik_parent = self.Parent_name
            ik_pole = self.Pole_name
            ik_chain = [self.Owner_name, armature.pose.bones[self.Owner_name].parent.name]  #self.Get_IK_Chain()
            ik_chain.append("GB_local" + ik_pole[2:])
            ik_chain.append("PB" + ik_parent[2:])
            ik_local = "GB_local" + ik_parent[2:]           
            if self.Chain_use_fk:
                if self.Chain_use_parent:
                    self.Current_switches[0] = False
                    self.Update_Use_Parent(context)
                for name in ik_chain:
                    p_bone = armature.pose.bones[name]
                    matrix = Get_Local_Bone_Matrix(p_bone)
                    p_bone.location = matrix.to_translation()
                    p_bone.rotation_quaternion = matrix.to_quaternion()                    
                    if "PB" in name:
                        p_bone.constraints.remove(p_bone.constraints["Copy Rotation"])
                    elif "GB_local" in name:
                        p_bone.constraints.remove(p_bone.constraints["Use FK - Copy Transforms"])
                    elif "CB" in name:
                        Set_Rotation_Limits(p_bone, p_bone.constraints["Use FK - Limit Rotation"], False)
                        if name == ik_owner.name:
                            p_bone.constraints.remove(p_bone.constraints["IK"])
                                                
                ik_bone = armature.pose.bones[ik_parent]
                constraint = ik_bone.constraints.new("COPY_TRANSFORMS")
                constraint.name = "Use FK - Copy Transforms"
                constraint.target = armature
                constraint.subtarget = ("GB_local" if ik_target != ik_parent else "PB") + ik_parent[2:]                
                
                pole_bone = armature.pose.bones[ik_pole]
                constraint = pole_bone.constraints.new("COPY_TRANSFORMS")
                constraint.name = "Use FK - Copy Transforms"
                constraint.target = armature
                constraint.subtarget = "GB_local" + ik_pole[2:]
                                
            else:
                if self.Chain_use_parent:
                    self.Current_switches[0] = False
                    self.Update_Use_Parent(context)
                ik_bone = armature.pose.bones[ik_parent]
                matrix = Get_Local_Bone_Matrix(ik_bone)
                ik_bone.location = matrix.to_translation()
                ik_bone.rotation_quaternion = matrix.to_quaternion()
                ik_bone.constraints.remove(ik_bone.constraints["Use FK - Copy Transforms"])                
                
                pole_bone = armature.pose.bones[ik_pole]
                matrix = Get_Local_Bone_Matrix(pole_bone)
                pole_bone.location = matrix.to_translation()
                pole_bone.rotation_quaternion = matrix.to_quaternion()               
                pole_bone.constraints.remove(pole_bone.constraints["Use FK - Copy Transforms"])
                
                for name in ik_chain:
                    p_bone = armature.pose.bones[name]
                    if "PB" in name:
                        constraint = p_bone.constraints.new("COPY_ROTATION")
                        constraint.name = "Copy Rotation"
                        constraint.target = armature
                        constraint.subtarget = ik_target
                    elif "GB_local" in name:
                        constraint = p_bone.constraints.new("COPY_TRANSFORMS")
                        constraint.name = "Use FK - Copy Transforms"
                        constraint.target = armature
                        constraint.subtarget = ik_pole
                    elif "CB" in name:
                        Set_Rotation_Limits(p_bone, p_bone.constraints["Use FK - Limit Rotation"], self.Chain_ik_rotation_overide)
                        if name == ik_owner.name:
                            constraint = p_bone.constraints.new("IK")
                            constraint.name = "IK"
                            constraint.target = armature
                            constraint.pole_target = armature
                            constraint.chain_count = 2
                            constraint.subtarget = ik_target
                            constraint.pole_subtarget = self.Pole_name
                            constraint.pole_angle = self.Pole_angle
                                                                                    
            self.Current_switches[1] = self.Chain_use_fk
    
    def Update_IK_Rotation_Overide(self, context):        
        if self.Chain_ik_rotation_overide != self.Current_switches[2]:
            armature = bpy.context.object
            ik_chain = [self.Owner_name, armature.pose.bones[self.Owner_name].parent.name] #self.Get_IK_Chain()
            for name in ik_chain:
                p_bone = armature.pose.bones[name]
                Set_Rotation_Limits(p_bone, p_bone.constraints["Use FK - Limit Rotation"], (self.Chain_ik_rotation_overide and not self.Chain_use_fk))
            self.Current_switches[2] = self.Chain_ik_rotation_overide                
    
    def Update_IK_Influence(self, context):
        o_bone = bpy.context.object.pose.bones[self.Owner_name]
        if "IK" in o_bone.constraints:
            o_bone.constraints["IK"].influence = self.Chain_ik_influence
    
    Owner_name: StringProperty(
        name="Owner Name",
        description="The name of the bone that has the IK constraint",
        default="",
        maxlen=1024,
        )
        
    Target_name: StringProperty(
        name="Target Name",
        description="The IK target bones name",
        default="",
        maxlen=1024,
        )
        
    Parent_name: StringProperty(
        name="Target Name",
        description="The IK parent bones name",
        default="",
        maxlen=1024,
        )
    
    Pole_name: StringProperty(
        name="Pole Name",
        description="The IK pole target bones name",
        default="",
        maxlen=1024,
        )
        
    Pole_angle: FloatProperty(
        name="Pole Angle", 
        description="The angle of the IK pole target", 
        default=0.0
        )
        
    Root_name: StringProperty(
        name="Root Name",
        description="The IK root bones name",
        default="",
        maxlen=1024,
        )
        
    Chain_name: StringProperty(
        name="Chain Name",
        description="The IK chains display name",
        default="",
        maxlen=1024,
        )
    
    Chain_use_parent: BoolProperty(
        name="Use Parent",
        description="Switch between Parented vs Independent targets for this IK chain",
        default=False,
        update=Update_Use_Parent
        )

    Chain_use_fk: BoolProperty(
        name="Use FK",
        description="Switch between IK vs FK for this IK chain",
        default=False,
        update=Update_Use_FK
        )
    
    Chain_ik_rotation_overide: BoolProperty(
        name="IK Rotation Overide",
        description="While using switchable IK vs FK this limits chain bones rotation to zero when controlling with IK. WARNING: Probably don't keyframe! I might make this option relative to each bone in the future",
        default=False,
        update=Update_IK_Rotation_Overide
        )
    
    Current_switches: BoolVectorProperty(
        name="Current Switches", 
        description="What the last booleans were. Set after firing option update functions", 
        default=(False, False, False),
        size=3
        )    
    
    Chain_ik_influence: FloatProperty(
        name="Chain - IK Influence", 
        description="While using switchable IK vs FK this maintains the ability to display and keyframe the influence of the IK constraint when it's not available", 
        default=1.0, 
        min=0.0, 
        max=1.0,
        subtype='FACTOR', 
        update=Update_IK_Influence
        )
     
# armature specific options...        
class JK_MMT_Rig_Props(PropertyGroup):
    
    def Update_Head_Tracking(self, context):
        importlib.reload(MMT_Options_Rig)
        MMT_Options_Rig.Set_Head_Tracking()
        self.Current_options[0] = int(self.Head_tracking)
    
    def Update_IK_Parenting(self, context):
        importlib.reload(MMT_Options_Rig)
        MMT_Options_Rig.Set_IK_Parenting()
        self.Current_options[1] = int(self.IK_parenting)
        
    def Update_IKvsFK_Limbs(self, context):
        importlib.reload(MMT_Options_Rig)
        MMT_Options_Rig.Set_IKvsFK_Limbs()
        self.Current_options[2] = int(self.IKvsFK_limbs)
        
    def Update_IKvsFK_Digits(self, context):
        importlib.reload(MMT_Options_Rig)
        MMT_Options_Rig.Set_IKvsFK_Digits()
        self.Current_options[3] = int(self.IKvsFK_digits)
        
    def Update_Character_Mesh(self, context):
        for prop in bpy.data.objects[self.Character_meshes].data.JK_MMT.items():
            self.Character_props[prop[0]] = prop[1]
        
    Rig_type: EnumProperty(
        name="Rig Type",
        description="What type of rig the add-on registers the armature as",
        items=[('NONE', 'None', "Not a Mr Mannequin rig"),
        ('TEMPLATE', 'Template', "Retarget template rig"),
        ('MANNEQUIN', 'Mannequin', "Biped based rig"),
        ('GUN', 'Gun', "Weapon based rig"),
        ('CUSTOM', 'Custom', "User created rig")],
        default='NONE'
        )
    
    Mute_default_constraints: BoolProperty(
        name="Mute Default Constraints",
        description="Mute the default constraints. Useful when working with imported animations",
        default = False
        )
    
    Hide_deform_bones: BoolProperty(
        name="Hide Deform Bones",
        description="Hide the bones in the deform and mechanism bone groups while in pose mode. This probably does not need to be keyframed but it could be",
        default = True
        )
    
    Head_tracking: EnumProperty(
        name="Head Tracking",
        description="Which method of Head Tracking to use",
        items=[('0', 'None', "No head tracking"),
        ('1', 'Use Head Tracking', "Use head tracking")],
        #('2', 'Switchable', "Head tracking can be switched on and off while keyframing")] # not really needed as influences can be keyframed??
        default='0',
        update=Update_Head_Tracking
        )
    
    IK_parenting: EnumProperty(
        name="IK Parenting",
        description="Which method of IK parenting to use. Only affects limb IK targets",
        items=[('0', 'Independant', "IK targets have no parents"),
            ('1', 'Parented', "IK targets have root parents"),
            ('2', 'Switchable', "IK parenting can be switched while keyframing")],
        default='0',
        update=Update_IK_Parenting
        )
    
    IKvsFK_limbs: EnumProperty(
        name="IK vs FK - Limbs",
        description="Which method of IK vs FK to use",
        items=[('0', 'Use IK', "Only use IK"),
            ('1', 'Offset FK', "FK is offset from IK"),
            ('2', 'Switchable', "IK and FK can be switched between while keyframing")],
        default='0',
        update=Update_IKvsFK_Limbs
        )
    
    IKvsFK_digits: EnumProperty(
        name="IK vs FK - Digits",
        description="Which method of IK vs FK to use",
        items=[('0', 'Use FK', "Only use FK"),
            ('1', 'Offset FK', "FK is offset from IK")],
            #('2', 'Switchable', "IK and FK can be switched between while keyframing")] # coming in the future...
        default='0',
        update=Update_IKvsFK_Digits
        )
    
    Current_options: IntVectorProperty(
        name="Current Options", 
        description="What the last options were. Set after firing option update functions", 
        default=(0, 0, 0, 0),
        size=4
        )
        
    IK_chain_data: CollectionProperty(type=JK_MMT_IK_Props)
    
    Character_meshes: EnumProperty(
        name="Characters",
        description="Characters to set rig to",
        items=Get_Character_Meshes,
        default=None,
        update=Update_Character_Mesh
        )
    
    Character_props: PointerProperty(type=JK_MMT_Character_Props)
        
    Retarget_target: StringProperty(
        name="Target",
        description="Name of the armature we are retargeting too",
        default="None",
        maxlen=1024,
        )                 
    
    Force_template_rotations: BoolProperty(
        name="Force Template Rotations",
        description="Attempt to pose the mesh to fit the active templates default bone rotations and apply the deformation. WARNING! This is a work in progress",
        default = False
        )
        
    Force_template_locations: BoolProperty(
        name="Force Template Locations",
        description="Attempt to pose the mesh to fit the active templates default bone locations and apply the deformation. WARNING! This is a work in progress",
        default = False
        )
    
    Socket_props: PointerProperty(type=JK_MMT_Socket_Props)
    
# adds selected meshes to saved files...    
class JK_OT_A_Stash(Operator):
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
                        ShowMessage(message = "Unable to create folder here, check your folder/drive permissions or try running blender as administrator", title = "Write Error", icon = 'ERROR')
                        print("Unable to create folder here, check your folder/drive permissions or try running blender as administrator")
                else:
                    if MMT.S_path_folder not in [stash[1] for stash in prefs.S_paths]:
                        prefs.S_paths.append((os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder), MMT.S_path_folder, os.path.join(bpy.path.abspath(MMT.S_path_add), MMT.S_path_folder)))
                    else:
                        ShowMessage(message = "Stash already exists", title = "Stash Error", icon = 'ERROR')
                        print("Stash already exists")
            else:
                ShowMessage(message = "Stash paths should not be in the add-ons folder! (updates could delete anything saved here)", title = "Stash Error", icon = 'ERROR')
                print("Stash paths should not be in the add-ons folder! (updates could delete anything saved here)")
        else:
            ShowMessage(message = "Path does not exist!", title = "Write Error", icon = 'ERROR')
            print("Path does not exist!")
    
        return {'FINISHED'}

#removes selected mesh from saved files... 
# not currently working properly... try/except still pulling os.remove permission error... 
class JK_OT_R_Stash(Operator):
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
                        ShowMessage(message = stash[1] + " has been removed from stashes but the folder and library .blends must be deleted manually", title = "Stash Info", icon = 'INFO')
                        print(stash[1] + " has been removed from stashes but the folder and library .blends must be deleted manually")
        return {'FINISHED'}
        
# loads a saved mesh...
class JK_OT_L_Mesh(Operator):
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
            ShowMessage(message = "Unable to save unsaved .blend, some data blocks with 0 users might not of been removed", title = "Save Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, some data blocks with 0 users might not of been removed")
        MMT.MMT_last_active = ""
        return {'FINISHED'}

# adds selected meshes to saved files...    
class JK_OT_A_Mesh(Operator):
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
                    importlib.reload(MMT_Stash_Object)
                    MMT_Stash_Object.Stash(MMT, obj)
                else:
                    ShowMessage(message = obj.name + " does not have the correct armature modifier! (armature modifier must be targeting the active rig)", title = "Stash Error", icon = 'ERROR')
                    print(obj.name + " does not have the correct armature modifier! (armature modifier must be targeting the active rig)")
        MMT.MMT_last_active = "" 
        return {'FINISHED'}

# removes selected mesh from saved files...   
class JK_OT_R_Mesh(Operator):
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
class JK_OT_L_Material(Operator):
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
            ShowMessage(message = mat_name + " is already in bpy.data.materials, rename it then try again", title = "Stash Error", icon = 'ERROR')
            print(mat_name + " is already in bpy.data.materials, rename it then try again")
        return {'FINISHED'}    

# adds active materials to saved files...    
class JK_OT_A_Material(Operator):
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
                importlib.reload(MMT_Stash_Material)              
                MMT_Stash_Material.Stash(MMT, obj.active_material)
        return {'FINISHED'}

# removes selected material from saved files...   
class JK_OT_R_Material(Operator):
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
class JK_OT_L_Rig(Operator):
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
            ShowMessage(message = "Unable to save unsaved .blend, some data blocks with 0 users might not of been removed", title = "Save Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, some data blocks with 0 users might not of been removed")
        return {'FINISHED'}

# FBX export operator...       
class JK_OT_E_FBX(Operator):
    """Exports Mr Mannequin FBX(s) that are directly compatible with the mannequin skeleton in UE4. No retargeting necessery! Will reveal any hidden pose bones"""
    bl_idname = "jk.e_fbx"
    bl_label = "Export FBX"
    
    def execute(self, context):
        if bpy.data.is_saved:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            if "Armature" in bpy.data.objects:
                bpy.data.objects["Armature"].name = bpy.context.active_object.name
            scene = context.scene
            MMT = scene.JK_MMT
            importlib.reload(MMT_Export_FBX)
            MMT_Export_FBX.Export(MMT)
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
        else:
            ShowMessage(message = "Unable to save unsaved .blend, export requires you to of saved at least once", title = "Export Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, export requires you to of saved at least once")
        return {'FINISHED'}

            
# FBX import operator...       
class JK_OT_I_FBX(Operator):
    """Imports and converts Mr Mannequin FBX(s) to be compatible with this rig in Blender. Currently only works on mannequin based animations. I'd like to work on making it more accurate"""
    bl_idname = "jk.i_fbx"
    bl_label = "Import FBX"
    
    def execute(self, context):
        if bpy.data.is_saved:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            scene = context.scene
            MMT = scene.JK_MMT
            importlib.reload(MMT_Import_FBX)
            MMT_Import_FBX.Import(MMT)
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        else:
            ShowMessage(message = "Unable to save unsaved .blend, import requires you to of saved at least once", title = "Import Error", icon = 'ERROR')
            print("Unable to save unsaved .blend, import requires you to of saved at least once")
        return {'FINISHED'}

class JK_OT_C_RetargetRig(Operator):
    """Work in progress! - Currently registers/unregisters a custom rig with the add-on and swaps/unswaps the X and Y axes on all deforming bones"""
    bl_idname = "jk.c_retargetrig"
    bl_label = "Export FBX"
    
    def execute(self, context):
        scene = context.scene
        MMT = scene.JK_MMT
        importlib.reload(MMT_Options_Retarget)
        obj = bpy.context.object
        if bpy.context.object.JK_MMT.Rig_type == 'TEMPLATE':
            MMT_Options_Retarget.Apply_Rig_Retargeting(bpy.data.objects[obj.JK_MMT.Retarget_target], obj, 'ARMATURE_UE4_Mannequin_Template')
        else:   
            MMT_Options_Retarget.Start_Rig_Retargeting(obj, 'ARMATURE_UE4_Mannequin_Template')
        return {'FINISHED'}
    
# updates rig to current version...    
class JK_OT_U_UpdateRig(Operator):
    """Update the currently selected Mr Mannequin armature from version 1.0 to 1.1"""
    bl_idname = "jk.u_updaterig"
    bl_label = "Update Rig"

    def execute(self, context):
        scene = context.scene
        armature = context.object
        MMT = scene.JK_MMT
        importlib.reload(MMT_Update)
        if armature.get('MrMannequinRig') != None:
            MMT_Update.Update_1_1(armature, MMT)
        elif armature.get("MMT Rig Version") == None and armature.JK_MMT.Rig_type != 'NONE':
            MMT_Update.Update_1_2(armature, MMT)      
        return {'FINISHED'}

# export/import inteface panel...            
class JK_PT_MMT_Export_FBX(Panel):    
    bl_label = "Export/Import"
    bl_idname = "JK_PT_MMT_Export_FBX"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'objectmode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        MMT = scene.JK_MMT
        armature = context.object
        layout.prop(scene.unit_settings, "scale_length")
        layout.prop(scene.render, "fps")
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE':
                #if armature.JK_MMT.Rig_type != 'NONE':
                layout.prop(MMT, "E_meshes")
                if MMT.E_meshes:
                    box = layout.box()
                    box.prop(MMT, "E_batch_meshes")
                    box.prop(MMT, "E_path_meshes")
                layout.prop(MMT, "E_animations")
                if MMT.E_animations:
                    box = layout.box()
                    box.prop(MMT, "E_batch_animations")
                    box.prop(MMT, "E_path_animations")
                if MMT.E_meshes or MMT.E_animations:
                    layout.prop(MMT, "E_apply_modifiers")
                    layout.prop(MMT, "E_startend_keys")
                    layout.prop(MMT, "E_anim_step")
                    layout.prop(MMT, "E_simplify_factor")
                    layout.operator("jk.e_fbx")
                    layout.separator()            
                layout.prop(MMT, "I_meshes") 
                if MMT.I_meshes:
                    box = layout.box()
                    box.prop(MMT, "I_batch_meshes")
                    if not MMT.I_batch_meshes:
                        box.prop(MMT, "I_mesh_fbxs")
                        if not MMT.I_rig_to_active:
                            box.prop(MMT, "I_import_to_retarget")                        
                    box.prop(MMT, "I_rig_to_active")                                                                        
                    box.prop(MMT, "I_path_meshes")
                layout.prop(MMT, "I_animations")                        
                if MMT.I_animations:
                    box = layout.box()
                    box.prop(MMT, "I_batch_animations")
                    if not MMT.I_batch_animations:
                        box.prop(MMT, "I_animation_fbxs")
                    box.prop(MMT, "I_pre_scale_keyframes")                                                                  
                    box.prop(MMT, "I_root_motion")
                    box.prop(MMT, "I_key_controls")
                    box.prop(MMT, "I_key_location")
                    box.prop(MMT, "I_frame_offset")
                    box.prop(MMT, "I_path_animations")                
                if MMT.I_meshes or MMT.I_animations:
                    layout.prop(MMT, "I_user_props")
                    layout.operator("jk.i_fbx")
                if armature.JK_MMT.Rig_type == 'NONE' or armature.JK_MMT.Rig_type == 'TEMPLATE':
                    layout.operator("jk.c_retargetrig", text=("Start Retargeting" if armature.JK_MMT.Rig_type == 'NONE' else "Apply Retargeting"))
            else:
                layout.label(text="Please select a Mr Mannequin rig")
        else:
            layout.label(text="Please select a Mr Mannequin rig")

# socket interface panel...       
class JK_PT_MMT_Socket(Panel):
    bl_label = "Socket"
    bl_idname = "JK_PT_MMT_Socket"
    bl_space_type = 'VIEW_3D'
    bl_context = 'objectmode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = bpy.context.object
        if obj != None and len(bpy.context.selected_objects) > 0:
            layout.label(text="Active Object")
            layout.prop(obj.JK_MMT.Socket_props, "Socket_target")
            layout.prop(obj.JK_MMT.Socket_props, "Socket_subtarget")
            layout.prop(obj.JK_MMT.Socket_props, "Is_attached")
            for socket in bpy.context.selected_objects:
                if socket != obj:
                    box = layout.box()
                    box.label(text=socket.name)
                    box.prop(socket.JK_MMT.Socket_props, "Socket_target")
                    box.prop(socket.JK_MMT.Socket_props, "Socket_subtarget")
                    box.prop(socket.JK_MMT.Socket_props, "Is_attached")               
        else:
            layout.label(text="Please select one or more objects")
                
# stash interface panel...       
class JK_PT_MMT_Stash(Panel):
    bl_label = "Stash"
    bl_idname = "JK_PT_MMT_Stash"
    bl_space_type = 'VIEW_3D'
    bl_context = 'objectmode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        MMT = scene.JK_MMT
        armature = context.object
        if MMT.S_path != 'None':
            layout.prop(MMT, "S_path")
        box = layout.box()
        box.prop(MMT, "S_path_folder")
        box.prop(MMT, "S_path_add")
        row = box.row()
        row.operator("jk.a_stash")
        row.operator("jk.r_stash")        
        layout.separator()
        layout.prop(MMT, "L_rigs")
        box = layout.box()
        box.prop(MMT, "L_apply_scale_armatures")        
        # add in any future rigging options here...
        box.operator("jk.l_rig")
        layout.separator()
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE':
                if armature.JK_MMT.Rig_type != 'NONE':
                    layout.prop(MMT, "L_materials")
                    box = layout.box()
                    row = box.row()
                    row.operator("jk.l_material")
                    row.operator("jk.r_material")
                    if os.path.exists(MMT.S_path) and any(obj.type != 'ARMATURE' and len(obj.data.materials) > 0 for obj in bpy.context.selected_objects):
                        box = layout.box()
                        box.prop(MMT, "A_overwrite_existing_materials")
                        box.prop(MMT, "A_pack_images")
                        box.operator("jk.a_material")             
                    layout.separator()
                    layout.prop(MMT, "L_meshes")
                    box = layout.box()
                    box.prop(MMT, "L_autoload_materials") 
                    box.prop(MMT, "L_active_parent")
                    box.prop(MMT, "L_apply_scale_meshes") 
                    row = box.row()
                    if os.path.exists(MMT.L_meshes):
                        row.operator("jk.l_mesh")
                        row.operator("jk.r_mesh")
                    if os.path.exists(MMT.S_path) and any(obj.type == 'MESH' for obj in bpy.context.selected_objects):
                        box = layout.box()
                        box.prop(MMT, "A_overwrite_existing_meshes")
                        box.prop(MMT, "A_autosave_materials")
                        box.operator("jk.a_mesh")
                if armature.get('MrMannequinRig') != None:
                    layout.operator("jk.u_updaterig", text="Update Rig (1.1)")
                elif armature.get("MMT Rig Version") == None and armature.JK_MMT.Rig_type != 'NONE':
                    layout.operator("jk.u_updaterig", text="Update Rig (1.2)")
                               
# rig options interace panel...            
class JK_PT_MMT_Pose_Options(Panel):    
    bl_label = "Rig Options"
    bl_idname = "JK_PT_MMT_Pose_Options"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'posemode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = bpy.context.object
        MMT = armature.JK_MMT
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE':
                # if it's a mannequin rig we know what options there should be...
                if armature.JK_MMT.Rig_type == 'MANNEQUIN':
                    layout.prop(MMT, "Character_meshes") 
                    
                    box = layout.box()
                    box.label(text="Head Tracking")
                    box.prop(MMT, "Head_tracking", text="")

                    box = layout.box()
                    box.label(text="IK Parenting")
                    box.prop(MMT, "IK_parenting", text="")

                    box = layout.box()
                    box.label(text="IK vs FK - Limbs")
                    box.prop(MMT, "IKvsFK_limbs", text="")

                    box = layout.box()
                    box.label(text="IK vs FK - Digits")
                    box.prop(MMT, "IKvsFK_digits", text="")
                # if it's a custom rig we will need to check if options can be used...
                elif armature.JK_MMT.Rig_type == 'CUSTOM':
                    # head tracking is not dynamic (yet) so all three bones must be present...
                    if "CB_head" in armature.pose.bones and "CB_neck_01" in armature.pose.bones and  "CB_spine_03" in armature.pose.bones:
                        box = layout.box()
                        box.label(text="Head Tracking")
                        box.prop(MMT, "Head_tracking", text="")
                    # ik parenting requires both the ik roots exist...
                    if "CB_ik_hand_root" in armature.pose.bones and "CB_ik_foot_root" in armature.pose.bones:
                        box = layout.box()
                        box.label(text="IK Parenting")
                        box.prop(MMT, "IK_parenting", text="")
                    # if there are any IK chains we can use the IK vs FK limb options....
                    if len(armature.JK_MMT.IK_chain_data) > 0:
                        box = layout.box()
                        box.label(text="IK vs FK - Limbs")
                        box.prop(MMT, "IKvsFK_limbs", text="")
                    # if there any digits we can use the digit IK vs FK options... i think??
                    if any(name + "_l" in armature.pose.bones or name + "_r" in armature.pose.bones for name in ["CB_thumb_03", "CB_index_03", "CB_middle_03", "CB_ring_03", "CB_pinky_03"]):
                        box = layout.box()
                        box.label(text="IK vs FK - Digits")
                        box.prop(MMT, "IKvsFK_digits", text="")                
                elif armature.JK_MMT.Rig_type == 'GUN':
                    layout.label(text="Sorry no gun options... yet!")
                elif armature.JK_MMT.Rig_type == 'TEMPLATE':
                    if MMT.Retarget_target != "None":
                        target = bpy.data.objects[MMT.Retarget_target]
                        layout.label(text="Target Display")
                        box = layout.box()
                        box.prop(target, "display_type", text="Armature")
                        box.prop(target.data, "display_type", text="Bones")
                    layout.label(text="Template Display")
                    box = layout.box()
                    box.prop(armature, "display_type", text="Armature")
                    box.prop(armature.data, "display_type", text="Bones")
                    box.prop(armature.data, "show_bone_custom_shapes", text="Shapes")
                    layout.prop(armature.JK_MMT, "Force_template_rotations")
                    layout.prop(armature.JK_MMT, "Force_template_locations")
                    layout.operator("jk.c_retargetrig", text=("Start Retargeting" if armature.JK_MMT.Rig_type == 'NONE' else "Apply Retargeting"))
                else:
                    layout.label(text="Please select a Mr Mannequin rig for options")
            else:
                layout.label(text="Please select a Mr Mannequin rig for options")
        else:
            layout.label(text="Please select a Mr Mannequin rig for options")
                
# rig options interace panel...            
class JK_PT_MMT_Pose_Controls(Panel):    
    bl_label = "Rig Controls"
    bl_idname = "JK_PT_MMT_Pose_Controls"
    bl_space_type = 'VIEW_3D'    
    bl_context= 'posemode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = bpy.context.object
        MMT = armature.JK_MMT
        Spine = ["CB_pelvis", "CB_spine_01", "CB_spine_02", "CB_spine_03", "CB_neck_01", "CB_head", "HT_head", "HT_stretch"]
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE' and MMT.Rig_type != 'NONE':
                layout.prop(MMT, 'Hide_deform_bones')
                layout.prop(MMT, 'Mute_default_constraints')
                # if it's a mannequin or custom rig...
                if MMT.Rig_type == 'MANNEQUIN' or MMT.Rig_type == 'CUSTOM':                
                    if any(armature.pose.bones[name] in bpy.context.selected_pose_bones for name in Spine if name in armature.pose.bones):
                        layout.label(text="Torso")
                        layout.prop(armature.pose.bones["CB_pelvis"].bone, "use_inherit_rotation", text="Pelvis - Inherit Rotation")
                        layout.prop(armature.pose.bones["CB_spine_01"].bone, "use_inherit_rotation", text="Spine 01 - Inherit Rotation")
                        if "CB_spine_02" in armature.pose.bones:
                            if "Copy Rotation" in armature.pose.bones["CB_spine_02"].constraints:
                                layout.prop(armature.pose.bones["CB_spine_02"].constraints["Copy Rotation"], 'influence', text="Spine 02 - Copy Spine 01")
                        if "GB_head" in armature.pose.bones:
                            box = layout.box()
                            box.label(text="Head Tracking")
                            # might implement a driven master influence in the future... (does not do what i want atm)
                            #box.prop(armature.pose.bones["HT_stretch"].constraints["Head Tracking - IK"], 'influence', text="Master Influence")
                            for bone in ["CB_head", "CB_neck_01", "CB_spine_03"]:
                                box.prop(armature.pose.bones[bone].constraints["Head Tracking - IK"], 'influence', text=("Head" if bone == "CB_head" else "Neck" if bone == "CB_neck_01" else "Spine 03") + (" - X-Z Rotation" if bone != "CB_head" else " - X-Y-Z Rotation"))
                                if bone != "CB_head":
                                    box.prop(armature.pose.bones[bone].constraints["Head Tracking - Copy Rotation"], 'influence', text=("Neck" if bone == "CB_neck_01" else "Spine 03") + " - Y Rotation")
                    if len(MMT.IK_chain_data) > 0:
                        for data in MMT.IK_chain_data:
                            owner = armature.pose.bones[data.Owner_name]
                            selected_names = [child.name for child in owner.parent.children if "MB" not in child.name] + [child.name for child in owner.children if "MB" not in child.name] + [owner.parent.name, 
                                data.Parent_name, 
                                data.Pole_name, 
                                data.Parent_name[:2] + "_local" + data.Parent_name[2:], 
                                data.Pole_name[:2] + "_local" + data.Pole_name[2:],
                                "CB" + data.Parent_name[2:],
                                owner.parent.parent.name]
                            if any(armature.pose.bones[name] in bpy.context.selected_pose_bones for name in selected_names if name in armature.pose.bones):
                                layout.label(text=data.Chain_name)
                                layout.prop(data, "Chain_ik_influence")
                                for child in owner.children:
                                    if "twist" in child.name and "IK" in child.constraints:
                                        layout.prop(child.constraints["IK"], 'influence', text=("Wrist - Copy Hand Y" if "Arm" in data.Chain_name else "Ankle - Copy Foot Y"))
                                if MMT.IK_parenting == '2' or MMT.IKvsFK_limbs == '2':
                                    box = layout.box()
                                    if MMT.IK_parenting == '2':
                                        row = box.row()    
                                        row.prop(data, 'Chain_use_parent')
                                        row.enabled = not data.Chain_use_fk
                                    if MMT.IKvsFK_limbs == '2':
                                        box.prop(data, 'Chain_use_fk')
                                        box.prop(data, 'Chain_ik_rotation_overide')
                    else:
                        layout.label(text="No IK chains registered")
                # if it's a gun rig...
                elif MMT.Rig_type == 'GUN':
                    layout.prop(armature.pose.bones["CB_Trigger_Bone"].constraints["Limit Rotation"], 'influence', text="Trigger - Limit Rotation")
                    layout.prop(armature.pose.bones["CB_Slide_Bone"].constraints["Limit Location"], 'influence', text="Slide - Limit Location")
                    layout.prop(armature.pose.bones["CB_Ammo"].constraints["Limit Location"], 'influence', text="Ammo - Limit Location") 
                # if it's a template rig...
                elif MMT.Rig_type == 'TEMPLATE':
                    for bone in bpy.context.selected_pose_bones:    
                        box = layout.box()
                        box.label(text=bone.name)
                        box.prop(bone.bone, "use_inherit_rotation")
                        box.prop(bone.bone, "use_inherit_scale")
                        box.prop(bone, "custom_shape")
                        box.prop(bone, "custom_shape_scale")
                        if len(bone.constraints) > 0:
                            box_in = box.box()
                        for constraint in bone.constraints:
                            if constraint.type == 'COPY_LOCATION':
                                box_in.label(text="Point Of Rotation:") 
                            elif constraint.type == 'IK':
                                box_in.label(text="IK Stretch To:")
                            elif constraint.type == 'COPY_ROTATION':    
                                box_in.label(text="Copy Y Rotation Of:")                        
                            box_in.prop(constraint, "target")
                            box_in.prop(constraint, "subtarget")
                else:
                    layout.label(text="Please select a Mr Mannequin rig for controls")
            else:
                layout.label(text="Please select a Mr Mannequin rig for controls")
        else:
            layout.label(text="Please select a Mr Mannequin rig for controls")                
                                        
#---------- REGISTRATION -----------------------------------------------------------------------    

JK_MMT_classes = (
    JK_MMT_Prefs,
    JK_MMT_Props,
    JK_MMT_Socket_Props,
    JK_MMT_Character_Props,
    JK_MMT_IK_Props,
    JK_MMT_Rig_Props,
    JK_OT_A_Stash,
    JK_OT_R_Stash,
    JK_OT_E_FBX,
    JK_OT_I_FBX,
    JK_OT_L_Rig,
    JK_OT_L_Mesh,
    JK_OT_L_Material,
    JK_OT_A_Mesh,
    JK_OT_A_Material,
    JK_OT_R_Mesh,
    JK_OT_R_Material,
    JK_OT_C_RetargetRig,
    JK_OT_U_UpdateRig,
    JK_PT_MMT_Export_FBX,
    JK_PT_MMT_Socket,
    JK_PT_MMT_Stash,
    JK_PT_MMT_Pose_Options,
    JK_PT_MMT_Pose_Controls,
    )

def register():
    for C in JK_MMT_classes:
        register_class(C)
    # add-on options for import/export/stashing etc...
    bpy.types.Scene.JK_MMT = PointerProperty(type=JK_MMT_Props)
    # mesh data is each specific meshes data in relation to a rig types options...
    bpy.types.Mesh.JK_MMT = PointerProperty(type=JK_MMT_Character_Props)
    # in order for rig properties to be keyframed in the same action as the bones they must be assigned to objects not armatures...
    bpy.types.Object.JK_MMT = PointerProperty(type=JK_MMT_Rig_Props)
    
def unregister():
    for C in reversed(JK_MMT_classes):
        unregister_class(C)
    del bpy.types.Scene.JK_MMT
    del bpy.types.Mesh.JK_MMT
    del bpy.types.Object.JK_MMT

#if __name__ == "__main__":
    #register()      