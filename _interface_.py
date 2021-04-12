import bpy
import os
from bpy.props import PointerProperty, StringProperty, CollectionProperty, BoolProperty
from . import (_properties_, _functions_)

class JK_MMT_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "MrMannequinsTools"

    resources: StringProperty(name="Resources", description="Where the templates are",
        default=os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), maxlen=1024, options=set(), subtype='DIR_PATH')

    export_active: StringProperty(name="Export Settings", description="The current export settings",
        default="", maxlen=1024, options=set(), subtype='NONE')
    
    export_default: PointerProperty(type=_properties_.JK_PG_MMT_Export, options=set())
    
    export_props: CollectionProperty(type=_properties_.JK_PG_MMT_Export, options=set())
    
    import_active: StringProperty(name="Import Settings", description="The current export settings", 
        default="", maxlen=1024, options=set(), subtype='NONE')

    import_default: PointerProperty(type=_properties_.JK_PG_MMT_Import, options=set())

    import_props: CollectionProperty(type=_properties_.JK_PG_MMT_Import, options=set())

    show_default_export: BoolProperty(name="Default Export Settings", description="Show the default export settings for editing",
        default=False)

    show_default_import: BoolProperty(name="Default Import Settings", description="Show the default export settings for editing",
        default=False)

    def draw(self, context):
        layout = self.layout
        eport, iport = self.export_default, self.import_default
        row = layout.row()
        row.label(text="Default Export Settings")
        row.prop(self, "show_default_export", text="", icon="TRIA_UP" if self.show_default_export else "TRIA_DOWN", toggle=False)
        if self.show_default_export:
            _functions_.show_export_meshes(self, eport)
            _functions_.show_export_actions(self, eport)
            _functions_.show_export_advanced(self, eport)
        
        row = layout.row()
        row.label(text="Default Import Settings")
        row.prop(self, "show_default_import", text="", icon="TRIA_UP" if self.show_default_import else "TRIA_DOWN", toggle=False)
        if self.show_default_import:
            _functions_.show_import_meshes(self, iport)
            _functions_.show_import_actions(self, iport)
            _functions_.show_import_advanced(self, iport)
