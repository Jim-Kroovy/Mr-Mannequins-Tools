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
    "version": (1, 5, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Object > Add | File > Import/Export",
    "description": "One UE4 Mannequin (with material) ready for animation and export and a bunch of other mannequin themed mesh and armature templates",
    "warning": "",
    "wiki_url": "https://github.com/Jim-Kroovy/Mr-Mannequins-Tools/wiki",
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
    # then get the add-on versions... (if they are installed)
    versions = {addon.__name__ : addon.bl_info.get('version') for addon in addon_utils.modules()
        if addon.bl_info['name'] in ['B.L.E.N.D - Armature Deform Controls', 'B.L.E.N.D - Armature Rigging Modules']}
    # and declare the dependencies...
    dependencies = [{'name' : "BLEND-ArmatureDeformControls", 'version' : (1, 1, 1)},
        {'name' : "BLEND-ArmatureRiggingModules", 'version' : (1, 1, 2)}]
    # as Mr Mannequins depends on and ships with some of my other blender add-ons...
    for dependency in dependencies:
        name, version = dependency['name'], dependency['version']
        # if the add-on is installed...
        if name in versions:
            # if the right version is not installed...
            if version != versions[name]:
                zip_file = name + "-" + str(version[0]) + "." + str(version[1]) + ".zip"
                # remove and reinstall from the version that shipped with Mr Mannequins...
                override = bpy.context.copy()
                override['area'] = bpy.context.window_manager.windows[0].screen.areas[0]
                # remove operator needs an area to tag for redraw... (seems to work without but spits error and stops iteration)
                bpy.ops.preferences.addon_remove(override, module=name)
                bpy.ops.preferences.addon_install(filepath=os.path.join(resources, zip_file))
            # check if the add-on is enabled, if not then enable it... # addon_utils.check(mod_name) 
            if name not in bpy.context.preferences.addons:
                bpy.ops.preferences.addon_enable(module=name)
        else:
            # otherwise it wasn't installed, so install and enable it...
            zip_file = name + "-" + str(version[0]) + "." + str(version[1]) + ".zip"
            bpy.ops.preferences.addon_install(filepath=os.path.join(resources, zip_file))
            bpy.ops.preferences.addon_enable(module=name)
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

    bpy.types.TOPBAR_MT_file_export.append(_functions_.add_export_to_menu)
    bpy.types.TOPBAR_MT_file_import.append(_functions_.add_import_to_menu)
    bpy.types.VIEW3D_MT_add.append(_functions_.add_load_to_menu)
    print("Operators appended to menus...")

    # enable the add-ons Mr Mannequins rigging depends on...
    bpy.app.timers.register(jk_mmt_enable_addons, first_interval=0.5)
    print("Checking dependencies...")

def unregister():
    print("UNREGISTER: ['Mr Mannequins Tools']")
    bpy.types.VIEW3D_MT_add.remove(_functions_.add_load_to_menu)
    bpy.types.TOPBAR_MT_file_import.remove(_functions_.add_import_to_menu)
    bpy.types.TOPBAR_MT_file_export.remove(_functions_.add_export_to_menu)
    print("Operators removed from menus...")
    
    for cls in reversed(JK_MMT_classes):
        unregister_class(cls)
    print("Classes unregistered...")

    