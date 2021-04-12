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

# Included with this add-on(s) in the "_resources_" folder are the 
# "Mannequin.blend" and the "Gun.blend" and the meshes and textures
# contained/used by them are property of Epic Games and should come
# under the UE4 EULA <https://www.unrealengine.com/en-US/eula>.
#
# I have not included this license as a .txt as you should already
# have a copy of it and will of agreed to it when downloading UE4.

# Any .blend files included with this add-on(s) in the "_resources_" folder
# and any armatures, meshes, materials and textures contained within them that
# do not fall under the UE4 EULA (see above for specific files)
# are licensed under a Creative Commons Attribution 4.0 International License.
#
# You should have received a copy of the license along with this
# work. If not, see <http://creativecommons.org/licenses/by/4.0/>.

#### NOTES ####

bl_info = {
    "name": "Mr Mannequins Tools",
    "author": "James Goldsworthy (Jim Kroovy)",
    "version": (1, 4, 0),
    "blender": (2, 91, 0),
    "location": "3D View > Object > Add | File > Import/Export",
    "description": "One UE4 Mannequin (with material) ready for animation and export and a bunch of other mannequin themed mesh and armature templates",
    "warning": "",
    "wiki_url": "https://www.youtube.com/c/JimKroovy",
    "category": "Characters",
    }

import bpy
import addon_utils
import os
from bpy.utils import (register_class, unregister_class)
#from bpy.app.handlers import persistent
from . import (_properties_, _operators_, _interface_, _functions_)

JK_MMT_classes = (
    _properties_.JK_PG_MMT_FBX,
    _properties_.JK_PG_MMT_Export,
    _properties_.JK_PG_MMT_Import,
    
    _operators_.JK_OT_MMT_Add_FBX_Settings,
    _operators_.JK_OT_MMT_Remove_FBX_Settings,
    _operators_.JK_OT_MMT_Reopen_Op,
    _operators_.JK_OT_MMT_Export_FBX,
    _operators_.JK_OT_MMT_Import_FBX,
    _operators_.JK_OT_MMT_Load_Templates,
    
    _interface_.JK_MMT_Addon_Prefs)

def jk_mmt_enable_addons():
    # get our resources folder and all add-ons and if they are enabled/loaded into a dictionary...
    prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
    resources = prefs.resources
    addons = {mod_name : addon_utils.check(mod_name) for path in addon_utils.paths() for mod_name, _ in bpy.path.module_names(path)}
    # if control bones is already installed...
    if 'BLEND-ArmatureDeformControls' in addons:
        # if it's disabled, enable it...
        if not addons['BLEND-ArmatureDeformControls'][0]:
            bpy.ops.preferences.addon_enable(module='BLEND-ArmatureDeformControls')
    else:
        # otherwise it needs to be installed and enabled...
        print("Installing: BLEND-ArmatureDeformControls")
        bpy.ops.preferences.addon_install(filepath=os.path.join(resources, 'BLEND-ArmatureDeformControls.zip'))
        bpy.ops.preferences.addon_enable(module='BLEND-ArmatureDeformControls')
    # if rigging library is already installed...
    if 'BLEND-ArmatureRiggingLibrary' in addons:
        # if it's disabled, enable it...
        if not addons['BLEND-ArmatureRiggingLibrary'][0]:
            bpy.ops.preferences.addon_enable(module='BLEND-ArmatureRiggingLibrary')
    else:
        # otherwise it needs to be installed and enabled...
        print("Installing: BLEND-ArmatureRiggingLibrary")
        bpy.ops.preferences.addon_install(filepath=os.path.join(resources, 'BLEND-ArmatureRiggingLibrary.zip'))
        bpy.ops.preferences.addon_enable(module='BLEND-ArmatureRiggingLibrary')

    # check version of rigging add-ons at some point...
    #versions = {addon.bl_info['name'] : addon.bl_info.get('version') for addon in addon_utils.modules() 
        #if addon.bl_info['name'] in ['BLEND-ArmatureDeformControls', 'BLEND-ArmatureRiggingLibrary']}
    #print(versions)
    
    # we'll need to update all driver dependencies... (why doesn't blender have an operator for this?)
    for armature in [ob for ob in bpy.data.objects if ob.type == 'ARMATURE' and ob.animation_data]:
        # so for every driver in every armature...
        for drv in armature.animation_data.drivers:
            # just set the expression to itself...
            drv.driver.expression = drv.driver.expression
    return None

def register():
    print("REGISTER: ['Mr Mannequins Tools']")
    for cls in JK_MMT_classes:
        register_class(cls)
    print("Classes registered...")

    #bpy.types.Scene.jk_mmt = bpy.props.PointerProperty(type=_properties_.JK_PG_MMT_Scene, options=set())
    #bpy.types.Object.jk_mmt = bpy.props.PointerProperty(type=_properties_.JK_PG_MMT_Object, options=set())
    #print("Properties assigned...")
    
    bpy.types.TOPBAR_MT_file_export.append(_functions_.add_export_to_menu)
    bpy.types.TOPBAR_MT_file_import.append(_functions_.add_import_to_menu)
    bpy.types.VIEW3D_MT_add.append(_functions_.add_load_to_menu)
    print("Operators appended to menus...")

    # enable the add-ons Mr Mannequins rigging depends on...
    bpy.app.timers.register(jk_mmt_enable_addons, first_interval=3)
    print("Checking dependencies in 3 seconds...")

def unregister():
    print("UNREGISTER: ['Mr Mannequins Tools']")
    bpy.types.VIEW3D_MT_add.remove(_functions_.add_load_to_menu)
    bpy.types.TOPBAR_MT_file_export.remove(_functions_.add_import_to_menu)
    bpy.types.TOPBAR_MT_file_export.remove(_functions_.add_export_to_menu)
    print("Operators removed from menus...")
    
    #del bpy.types.Object.jk_mmt
    #del bpy.types.Scene.jk_mmt
    #print("Properties deleted...")
    
    for cls in reversed(JK_MMT_classes):
        unregister_class(cls)
    print("Classes unregistered...")

    