# Contributor(s): James Goldsworthy (Jim Kroovy)

# Support: https://twitter.com/JimKroovy
#          https://www.facebook.com/JimKroovy
#          http://youtube.com/c/JimKroovy
#          https://www.patreon.com/JimKroovy

# This code is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Currently all the default meshes, textures, materials and armatures provided
# with the add-on in the "MMT_Stash" folder are property of Epic Games and should
# come under the UE4 EULA <https://www.unrealengine.com/en-US/eula>.

# Any file(s) (eg: meshes, materials, armatures, textures etc) that DO NOT come under the afore mentioned licenses
# have a CC-BY (Creative Commons - Attribution) license <https://creativecommons.org/use-remix/cc-licenses/#by>
#
# "This license lets others distribute, remix, tweak, and build upon your work, even commercially, 
# as long as they credit you for the original creation."
#    
# To give credit you must visibly state that the specific file(s) were created by Jim Kroovy and/or Mr Mannequins Tools 
# and (if possible) provide links to my Patreon and/or YouTube channel (see above links)

# By downloading these files you agree to the above licenses where they are applicable.

bl_info = {
    "name": "Mr Mannequins Tools",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 3),
    "blender": (2, 82, 0),
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
from . import (Base_Properties,
    Object_Properties_Socket,
    Pose_Properties_Character,
    Pose_Properties_Mapping, 
    Pose_Properties_Retarget, 
    Pose_Properties_Rigging,

    Base_Operators,
    Object_Operators_Export, 
    Object_Operators_Import, 
    Object_Operators_Stash,
    Pose_Operators_Mapping,     
    Pose_Operators_Retarget,
    Pose_Operators_Rigging,  
    
    Base_Interface,
    Object_Interface_Export, 
    Object_Interface_Import, 
    Object_Interface_Socket, 
    Object_Interface_Stash,
    Pose_Interface_Retarget, 
    Pose_Interface_Rigging,
    )

from bpy.utils import (register_class, unregister_class)

from bpy.app.handlers import persistent

#---------- NOTES ------------------------------------------------------------------------------

# This is still a work in progress! I'm still not all that happy with the UI...
# and there are a whole bunch of options and functionality to create and finalize...

# i suppose if you are reading this then you're probably trying to figure out how it all works...
# there are several parts to this add-on, the main and most useful part is the UE4 export FBX logic...
# which exports a UE4 mannequin compatible .FBX, no more retargeting needed! Woop!

# Then there is the stashing logic which enables the user to save their meshes/materials and reload them in other blend files...
# First the user creates a stash folder somewhere, then they are able write, load and remove library .blends to and from this location...
# the selection of library .blends is through drop down enum menus that display whats in the currently selected stash...
# users can have multiple stashes and the current stash can also be changed through a drop down enum menu...

# When a mesh/material is added to a stash a reference clean up text is written and stored with it...
# then when a mesh/material is loaded that clean up text is executed in order to set those references relative to what is in the current .blend...
# if a saved reference is not in the current .blend then it is linked to the scene...

# I did want to make the rig properties specific to armatures but doing that makes them a pain to animate so they are attached to objects instead...
# which isn't all bad as that also means that in the future i can easily drive character mesh shape keys and options from the armature within the same actions...

# MMT stands for Mr Mannequins Tools, E stands for export, I stands for import, S stands for Stash, L stands for Load, A stands for Add, O stands for option, U stands for update, C stands for custom...
# and JK/Jk/jk stands for Jim Kroovy and is the creator prefix i use for anything that might be used elsewhere... (makes for easier searching in most editing programs)

# Dynamically generated EnumProperty items must be referenced from Python!!!
# You must maintain a reference to dynamically generated EnumProperty items from Python or else Blender
# will not behave properly (symptomps are garbage strings, utf-8 decode errors, and crashes). For more information, see:
#    https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
#    https://developer.blender.org/T50426

# switch handler used to work around update functions not firing on keyframe change... (try not to add very much here as it could kill performance)
@persistent
def Post_Frame_Handler(dummy):
    # for each object...
    for obj in bpy.data.objects:
        # if its an armature...
        if obj.type == 'ARMATURE':
            MMT = obj.JK_MMT
            # and it's a mannequin armature with IK chains...
            if (MMT.Rig_type == 'MANNEQUIN' or MMT.Rig_type == 'CUSTOM') and len(MMT.IK_chain_data) > 0:
                # iterate through all the IK data...
                for data in obj.JK_MMT.IK_chain_data:
                    # aaaand if it's using switchable IK vs FK or IK parenting...
                    if data.IK_parenting == 'SWITCHABLE' or data.IKvsFK_limbs == 'SWITCHABLE':
                        # check/set each switch in order to fire update functions during play back...
                        if data.IKvsFK_limbs == 'SWITCHABLE':
                            if data.Chain_use_fk != data.Current_switches[1]:
                                data.Chain_use_fk = data.Chain_use_fk
                        if data.IK_parenting == 'SWITCHABLE':
                            if data.Chain_use_parent != data.Current_switches[0] and not data.Chain_use_fk:
                                data.Chain_use_parent = data.Chain_use_parent
                        # always set the IK influence so the update gets fired and keeps the constraints influence equal to the saved influence
                        data.Chain_ik_influence = data.Chain_ik_influence
# should i append/remove handlers on register/unregister?                                           
bpy.app.handlers.frame_change_post.append(Post_Frame_Handler)

# handler on depsgraph update... (currently only used to work around being unable to load in defaults to collection properties on register)
@persistent
def deps_update_handler(dummy):
    # iterate through scenes...
    for scene in bpy.data.scenes:
        # if they don't have any export properties...
        if len(scene.JK_MMT.Export_props) == 0:
            print("Props Handler")
            # add in the defaults...
            e_props = scene.JK_MMT.Export_props.add()
            e_props.name = 'Default'
            scene.JK_MMT.Export_active = 'Default'
        # if they don't have any import properties...
        if len(scene.JK_MMT.Import_props) == 0:
            print("Props Handler")
            # add in the defaults...
            i_props = scene.JK_MMT.Import_props.add()
            i_props.name = 'Default'
            scene.JK_MMT.Import_active = 'Default'

bpy.app.handlers.depsgraph_update_post.append(deps_update_handler)

#---------- REGISTRATION -----------------------------------------------------------------------    

JK_MMT_classes = (
    # Properties...
    Base_Properties.JK_MMT_Import_Props,
    Base_Properties.JK_MMT_Export_Props,
    Base_Properties.JK_MMT_Base_Props,
    Object_Properties_Socket.JK_MMT_Socket_Props,
    Pose_Properties_Character.JK_MMT_Character_Props,
    Pose_Properties_Mapping.JK_MMT_Section_Mapping,
    Pose_Properties_Mapping.JK_MMT_Joint_Mapping,
    Pose_Properties_Mapping.JK_MMT_Part_Mapping,
    Pose_Properties_Retarget.JK_MMT_Retarget_Item,
    Pose_Properties_Retarget.JK_MMT_Retarget_Dictionary,
    Pose_Properties_Retarget.JK_MMT_Retarget_Props,
    Pose_Properties_Rigging.JK_MMT_Head_Tracking_Props,
    Pose_Properties_Rigging.JK_MMT_Twist_Bone_Props,
    Pose_Properties_Rigging.JK_MMT_Digit_Bone_Props,
    Pose_Properties_Rigging.JK_MMT_Chain_Bone_Props,
    Pose_Properties_Rigging.JK_MMT_End_Bone_Props,
    Pose_Properties_Rigging.JK_MMT_IK_Props,
    Pose_Properties_Rigging.JK_MMT_Rig_Props,
    # Operators...
    Base_Operators.JK_OT_Reset_Child_Ofs,
    Base_Operators.JK_OT_Prep_Anim,
    Base_Operators.JK_OT_Scale_Anim,
    Base_Operators.JK_OT_Scale_Selected,
    Base_Operators.JK_OT_Scale_Keyframes,
    Object_Operators_Export.JK_OT_Export_Add_Settings,
    Object_Operators_Export.JK_OT_Export_Remove_Settings,
    Object_Operators_Export.JK_OT_Export_Mesh_FBX,
    Object_Operators_Export.JK_OT_Export_Anim_FBX,
    Object_Operators_Export.JK_OT_Export_FBX,
    Object_Operators_Import.JK_OT_Import_Add_Settings,
    Object_Operators_Import.JK_OT_Import_Remove_Settings,
    Object_Operators_Import.JK_OT_Import_Mesh_FBX,
    Object_Operators_Import.JK_OT_Import_Anim_FBX,
    Object_Operators_Import.JK_OT_Import_FBX,
    Object_Operators_Stash.JK_OT_Add_Stash,
    Object_Operators_Stash.JK_OT_Remove_Stash,
    Object_Operators_Stash.JK_OT_Load_Mesh,
    Object_Operators_Stash.JK_OT_Add_Mesh,
    Object_Operators_Stash.JK_OT_Remove_Mesh,
    Object_Operators_Stash.JK_OT_Load_Material,
    Object_Operators_Stash.JK_OT_Add_Material,
    Object_Operators_Stash.JK_OT_Remove_Material,
    Object_Operators_Stash.JK_OT_Load_Rig,
    ## saved mapping operators...
    Pose_Operators_Mapping.JK_OT_Mapping_Force_Naming,
    Pose_Operators_Mapping.JK_OT_Mapping_Write,
    Pose_Operators_Mapping.JK_OT_Mapping_Reset,
    Pose_Operators_Mapping.JK_OT_Mapping_Clear,
    Pose_Operators_Mapping.JK_OT_Mapping_Add,
    Pose_Operators_Mapping.JK_OT_Mapping_Remove,
    ## saved retargets operators...
    Pose_Operators_Retarget.JK_OT_Retarget_Force_Naming,
    Pose_Operators_Retarget.JK_OT_Retargets_Write,
    Pose_Operators_Retarget.JK_OT_Retargets_Reset,
    Pose_Operators_Retarget.JK_OT_Retargets_Clear,
    Pose_Operators_Retarget.JK_OT_Retargets_Add,
    Pose_Operators_Retarget.JK_OT_Retargets_Remove,
    Pose_Operators_Retarget.JK_OT_Retarget_Save,
    Pose_Operators_Retarget.JK_OT_Retarget_Type,
    ## rigging operators...
    Pose_Operators_Rigging.JK_OT_Add_Head_Controls,
    Pose_Operators_Rigging.JK_OT_Remove_Head_Controls,
    Pose_Operators_Rigging.JK_OT_Add_Twist_Controls,
    Pose_Operators_Rigging.JK_OT_Remove_Twist_Controls,
    Pose_Operators_Rigging.JK_OT_Add_Digit_Controls,
    Pose_Operators_Rigging.JK_OT_Remove_Digit_Controls,
    Pose_Operators_Rigging.JK_OT_Add_Ankle_Controls,
    Pose_Operators_Rigging.JK_OT_Remove_Ankle_Controls,
    Pose_Operators_Rigging.JK_OT_Add_IK_Chain,
    Pose_Operators_Rigging.JK_OT_Remove_IK_Chain,
    ## retarget operators...
    Pose_Operators_Retarget.JK_OT_Retarget_Rig,
    Pose_Operators_Retarget.JK_OT_Retarget_Anim,
    # Interface...
    Base_Interface.JK_MMT_Addon_Prefs,
    Base_Interface.JK_PT_MMT_Object,
    Base_Interface.JK_PT_MMT_Pose,

    Object_Interface_Export.JK_PT_MMT_Export,
    Object_Interface_Import.JK_PT_MMT_Import, 
    Object_Interface_Socket.JK_PT_MMT_Socket, 
    Object_Interface_Stash.JK_PT_MMT_Stash,

    Pose_Interface_Rigging.JK_PT_MMT_Rig_Options,
    Pose_Interface_Rigging.JK_PT_MMT_Rig_Controls,
    Pose_Interface_Retarget.JK_PT_MMT_Retarget_Options,
    )

def register():
    for C in JK_MMT_classes:
        register_class(C) 
    # add-on options for import/export/stashing etc...
    bpy.types.Scene.JK_MMT = bpy.props.PointerProperty(type=Base_Properties.JK_MMT_Base_Props)
    # mesh data is each specific meshes data in relation to a rig types options...
    bpy.types.Mesh.JK_MMT = bpy.props.PointerProperty(type=Pose_Properties_Character.JK_MMT_Character_Props)
    # in order for rig properties to be keyframed in the same action as the bones they must be assigned to objects not armatures...
    bpy.types.Object.JK_MMT = bpy.props.PointerProperty(type=Pose_Properties_Rigging.JK_MMT_Rig_Props)
    
def unregister():
    for C in reversed(JK_MMT_classes):
        unregister_class(C)

    del bpy.types.Scene.JK_MMT
    del bpy.types.Mesh.JK_MMT
    del bpy.types.Object.JK_MMT

#if __name__ == "__main__":
    #register()
    