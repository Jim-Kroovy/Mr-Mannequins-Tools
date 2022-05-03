import bpy
import os
from bpy.props import (FloatVectorProperty, StringProperty, BoolProperty, EnumProperty, IntProperty)
from . import _functions_, _properties_

class JK_OT_MMT_Add_FBX_Settings(bpy.types.Operator):
    """Add/Overwrite custom export/import settings"""
    bl_idname = "jk.add_fbx_settings"
    bl_label = "Add Custom"
    
    name: StringProperty(name="Name", description="The name of the settings",
        default="", maxlen=1024, options=set(), subtype='NONE') 
        
    is_export: BoolProperty(name="Bool", description="If we are operating on export or import settings",
        default=False, options=set())
    
    def execute(self, context):
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        props = prefs.export_props if self.is_export else prefs.import_props
        # if the fresh default settings haven't been saved yet...
        if len(props) == 0:
            default_props = props.add()
            default_props.name = 'Default'
        if prefs.export_active in props:
            current_props = props[prefs.export_active]
        else:
            current_props = props['Default']
        # if there aren't already settings saved with this name...
        if self.name not in props:
            new_props = props.add()
            new_props.name = self.name
            # for each of the properties in the settings...
            for prop in new_props.bl_rna.properties:
                # if it's the FBX properties...
                if prop.identifier == "fbx_props":
                    # for each of the FBX properties...
                    for fbx_prop in new_props.fbx_props.bl_rna.properties:
                        # if it isn't the property RNA or name...
                        if fbx_prop.identifier not in ["rna_type", "name"]:
                            # set the new property to the current property...
                            #setattr() 
                            exec("new_props.fbx_props." + fbx_prop.identifier + " = current_props.fbx_props." + fbx_prop.identifier)
                # else if it isn't the property RNA or name...    
                elif prop.identifier not in ["rna_type", "name"]:
                    # set the new property to the current property...
                    exec("new_props." + prop.identifier + " = current_props." + prop.identifier)
        else:
            print(self.name, "is already being used to label settings!")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")

class JK_OT_MMT_Remove_FBX_Settings(bpy.types.Operator):
    """Remove custom settings"""
    bl_idname = "jk.remove_fbx_settings"
    bl_label = "Remove Custom"

    name: StringProperty(name="Name", description="The name of the settings",
        default="", maxlen=1024, options=set(), subtype='NONE') 
        
    is_export: BoolProperty(name="Bool", description="If we are operating on export or import settings",
        default=False, options=set())
    
    def execute(self, context):
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        if self.is_export:
            prefs.export_props.remove(prefs.export_props.find(self.name))
        else:
            prefs.import_props.remove(prefs.import_props.find(self.name))
        prefs.Export_active = "Default"
        return {'FINISHED'}

class JK_OT_MMT_Reopen_Op(bpy.types.Operator):
    """Re-opens the import/export operators after file selection"""
    bl_idname = "jk.reopen_op"
    bl_label = "Mr Mannequins FBX"
    bl_options = {'REGISTER', 'UNDO'}

    is_export: BoolProperty(name="Is Export", description="Which operator we are re-opening?",
        default=True, options=set())

    was_browsing: BoolProperty(name="Was Browsing", description="Did we have a browse?",
        default=False, options=set())

    mouse_x : IntProperty(default=0)
    mouse_y : IntProperty(default=0)
    
    _iter = 0

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            # get all the temporary file browser windows... (there can only be one)
            temp_screens = [sc for sc in bpy.data.screens if sc.name.startswith("temp") and any(area.type == 'FILE_BROWSER' for area in sc.areas)]
            # if we have a temporary file browsing screen...
            if len(temp_screens) > 0:
                # set the was browsing boolean True if it was false...
                if not self.was_browsing:
                    self.was_browsing = True
            # if we are not browsing files or we have finished browsing files...
            if len(temp_screens) == 0:
                # increment the iter...
                self._iter = self._iter + 1
                # if we never browsed after several checks then we cancel... (the temp screen doesn't pop straight away)
                if self._iter > 5 and not self.was_browsing:
                    self.cancel(context)
                    return {'CANCELLED'}
                # otherwise if we were browsing and have stopped...
                elif self.was_browsing and len(temp_screens) == 0:
                    # set the cursor back to where it was when this operator was called...
                    context.window.cursor_warp(self.mouse_x, self.mouse_y)
                    # re-open the relevent operator and cancel the modal timer...
                    if self.is_export:
                        bpy.ops.jk.export_fbx('INVOKE_DEFAULT')
                    else:
                        bpy.ops.jk.import_fbx('INVOKE_DEFAULT')
                    self.was_browsing = False
                    self.cancel(context)
                    return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        # get mouse x and y on invoke...
        self.mouse_x, self.mouse_y = event.mouse_x, event.mouse_y
        # and kick off the modal operator...
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class JK_OT_MMT_Export_FBX(bpy.types.Operator):
    """Exports FBXs... Mr Mannequin Style!"""
    bl_idname = "jk.export_fbx"
    bl_label = "Mr Mannequins FBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # get everything we need to reference...
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        eport = prefs.export_props[prefs.export_active] if prefs.export_active in prefs.export_props else prefs.export_default
        # if we are redirecting to send to unreal...
        if eport.send_to_unreal:
            # fire this function that can optionally bypass the collections...
            _functions_.export_s2u(eport.from_selection)
        else:
            # if auto keying is enabled...
            auto_key = bpy.context.scene.tool_settings.use_keyframe_insert_auto
            if auto_key:
                # turn it off before exporting...
                bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            _functions_.run_export(eport)
            # push the export process into the undo steps...
            bpy.ops.ed.undo_push()
            # and undo it to return everything back to the way it was...
            bpy.ops.ed.undo()
        return {'FINISHED'}

    def cancel(self, context):
        # such a hacky workaround to the operator cancelling when browsing files... (i should probably use a file browsing operator?)
        bpy.ops.jk.reopen_op('INVOKE_DEFAULT', is_export=True)
        
    def invoke(self, context, event):
        bpy.ops.object.mode_set(mode='OBJECT')
        unexportables = [ob for ob in bpy.context.selected_objects if ob.type not in ['ARMATURE', 'MESH']]
        for unexportable in unexportables:
            unexportable.select_set(False)
        # need to make sure we have the right armatures selected...
        armatures = [ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE']
        for armature in armatures:
            adc = armature.data.jk_adc
            # if the armature is a deformer and it's not combined...
            if adc.is_deformer and not adc.use_combined:
                # make sure we only have the controller selected...
                armature.select_set(False)
                adc.get_controller().select_set(True)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 20
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        row = layout.row()
        row.prop_search(prefs, "export_active", prefs, "export_props", text="")
        row.operator("jk.add_fbx_settings", text="", icon='COLLECTION_NEW').is_export = True
        # export settings set to default settings if the active string isn't in the saved export settings...
        eport = prefs.export_props[prefs.export_active] if prefs.export_active in prefs.export_props else prefs.export_default
        if prefs.export_active != 'Default':
            op = row.operator("jk.remove_fbx_settings", text="", icon='TRASH')
            op.name = prefs.export_active
            op.is_export = True
        
        _functions_.show_export_meshes(self, eport)
        _functions_.show_export_actions(self, eport)
        _functions_.show_export_advanced(self, eport)

class JK_OT_MMT_Import_FBX(bpy.types.Operator):
    """Adds an action slot"""
    bl_idname = "jk.import_fbx"
    bl_label = "Mr Mannequins FBX"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # get everything we need to reference...
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        iport = prefs.import_props[prefs.import_active] if prefs.import_active in prefs.import_props else prefs.import_default
        _functions_.run_import(iport)
        return {'FINISHED'} # {'CANCELLED'}
        # bpy.ops.ed.undo()

    def cancel(self, context):
        # such a hacky workaround to the operator cancelling when browsing files...
        bpy.ops.jk.reopen_op('INVOKE_DEFAULT', is_export=False)
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 20
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        row = layout.row()
        row.prop_search(prefs, "import_active", prefs, "import_props", text="")
        row.operator("jk.add_fbx_settings", text="", icon='COLLECTION_NEW').is_export = False
        # export settings set to default settings if the active string isn't in the saved export settings...
        iport = prefs.import_props[prefs.import_active] if prefs.import_active in prefs.import_props else prefs.import_default
        if prefs.import_active != 'Default':
            op = row.operator("jk.remove_fbx_settings", text="", icon='TRASH')
            op.name = prefs.import_active
            op.is_export = False

        _functions_.show_import_meshes(self, iport)
        _functions_.show_import_actions(self, iport)
        _functions_.show_import_advanced(self, iport)

class JK_OT_MMT_Load_Templates(bpy.types.Operator):
    """Loads Mr Mannequins template armatures, materials and meshes"""
    bl_idname = "jk.load_templates"
    bl_label = "Mr Mannequins Templates"
    bl_options = {'REGISTER', 'UNDO'}

    def update_rigging(self, context):
        if self.rigging:
            self.controls = True

    def update_controls(self, context):
        if not self.controls:
            self.rigging = False

    flavour: EnumProperty(name="Type", description="The type of template to load",
        items=[('BIPED', 'Biped', "The Mannequin, Femmequin and any other bipeds i create"),
            #('QUADRUPED', 'Quadruped', "The Equinequin and any other quadrupeds i create"),
            ('EQUIPMENT', 'Equipment', "The First Person Gun, Bow and Arrow and any other weapons/armour i create")],
        default='BIPED', options=set())
    
    bipeds: EnumProperty(name="Biped", description="The template to load",
        items=[('Mannequin', 'Mannequin (Epic)', "The mannequin in UE4s Third Person template"),
            ('Femmequin', 'Femmequin (Kroovy)', "The female mannequin Jim created from the the mannequin in UE4s Third Person template, has breast bones but needs an update"),
            ('Mannequin_Female', 'Mannequin Female (Epic)', "The female mannequin Epic created for the Third Person template in engine version 4.26, has broken wrist meshes (not my fault, it's what's in the engine)")],
        default='Mannequin', options=set())

    quadrupeds: EnumProperty(name="Quadruped", description="The template to load",
        items=[('Equinequin', 'Equinequin', "The horse Jim created from the mannequin in UE4s Third Person template")],
        default='Equinequin', options=set())

    equipment: EnumProperty(name="Equipment", description="The template to load",
        items=[('Gun', 'First Person Gun', "The gun in UE4s First Person template"),
            ('Bow', 'Bow and Arrow', "The bow and arrow Jim created from the gun in UE4s First Person template"),
            ('Sword_1H', 'One Handed Sword', "The one handed sword Jim created from the gun in UE4s First Person template"),
            ('Shield', 'Shield', "The shield Jim created from the gun in UE4s First Person template")],
        default='Gun', options=set())

    armatures: BoolProperty(name="Armatures", description="Load any armatures associated with this template",
        default=True, options=set())

    controls: BoolProperty(name="Use Controls", description="Load armatures with control bones",
        default=True, options=set(), update=update_controls)

    rigging: BoolProperty(name="Use Rigging", description="Load armatures with control bones and rigging",
        default=True, options=set(), update=update_rigging)
    
    meshes: BoolProperty(name="Meshes", description="Load any meshes associated with this template",
        default=True, options=set())
    
    materials: BoolProperty(name="Materials", description="Load any materials associated with this template",
        default=True, options=set())

    actions: BoolProperty(name="Actions", description="(Coming Soon!) Load any default actions associated with this template",
        default=False, options=set())

    rescale: BoolProperty(name="Use Scene Scale", description="Scale the template to match the current scenes unit scale",
        default=True, options=set())

    lods: BoolProperty(name="Load LODs", description="Load any level of detail meshes associated with this template",
        default=False, options=set())

    link: BoolProperty(name="Linked", description="Link the template and its data. (limits editing but reduces file size)",
        default=False, options=set())

    instance: BoolProperty(name="Instance Meshes", description="Instance meshes from existing ones. (if there are existing ones)",
        default=False, options=set())

    remap: BoolProperty(name="Remap Materials", description="Remap the loaded materials and images to use existing ones. (if there are existing ones)",
        default=False, options=set())

    #existing: BoolProperty(name="Existing Actions", description="Use existing actions of the same names. (if there are existing ones)",
        #default=False, options=set())

    def execute(self, context):
        
        # dictionary of the contents of the resources folder...
        templates = {
            # Default UE4 templates...
            'Mannequin' : {
                'armatures' : {"UE4_Mannequin_Skeleton" : ["UE4_Mannequin_Skeleton", "UE4_Mannequin_Skeleton_Controls", "UE4_Mannequin_Skeleton_Rigging"]},
                'meshes' : {"SK_Mannequin" : ["SK_Mannequin_LOD0", "SK_Mannequin_LOD1", "SK_Mannequin_LOD2", "SK_Mannequin_LOD3"]},
                'materials' : {"M_Male_Body" : 0, "M_UE4Man_ChestLogo" : 1},
                'actions' : {"" : []}
            },
            
            'Mannequin_Female' : {
                'armatures' : {"UE4_Mannequin_Skeleton_Female" : ["UE4_Mannequin_Female_Skeleton", "UE4_Mannequin_Female_Skeleton_Controls", "UE4_Mannequin_Female_Skeleton_Rigging"]},
                'meshes' : {"SK_Mannequin_Female" : ["SK_Mannequin_Female_LOD0"]},
                'materials' : {"MI_Female_Body" : 0, "M_UE4Man_ChestLogo" : 1},
                'actions' : {"" : []}
            },
            
            'Gun' : {
                'armatures' : {"UE4_FPGun_Skeleton" : ["UE4_FPGun_Skeleton", "UE4_FPGun_Skeleton_Controls", "UE4_FPGun_Skeleton_Rigging"]},
                'meshes' : {"SK_FPGun" : ["SK_FPGun_LOD0", "SK_FPGun_LOD1", "SK_FPGun_LOD2", "SK_FPGun_LOD3"]},
                'materials' : {"M_FPGun" : 0},
                'actions' : {"" : []}
            },
            
            # My custom templates...
            'Femmequin' : {
                'armatures' : {"UE4_Femmequin_Skeleton" : ["UE4_Femmequin_Skeleton", "UE4_Femmequin_Skeleton_Controls", "UE4_Femmequin_Skeleton_Rigging"]},
                'meshes' : {"SK_Femmequin" : ["SK_Femmequin_LOD0"]},
                'materials' : {"M_Male_Body" : 0, "M_UE4Man_ChestLogo" : 1},
                'actions' : {"" : []}
            },
            
            'Bow' : {
                'armatures' : {"UE4_FPBow_Skeleton" : ["UE4_FPBow_Skeleton", "UE4_FPBow_Skeleton_Controls", "UE4_FPBow_Skeleton_Rigging"]},
                'meshes' : {"SK_FPBow" : ["SK_FPBow_LOD0", "SK_FPArrow_LOD0"]},
                'materials' : {"M_FPGun" : 0},
                'actions' : {"" : []}
            },
            
            'Sword_1H' : {
                'armatures' : {},
                'meshes' : {"ST_Sword_1H" : ["ST_Sword_1H_LOD0"]},
                'materials' : {"M_FPGun" : 0},
                'actions' : {"" : []}
            },
                
            'Shield' : {
                'armatures' : {},
                'meshes' : {"ST_Shield" : ["ST_Shield_LOD0"]},
                'materials' : {"M_FPGun" : 0},
                'actions' : {"" : []}
            },
            
        }
        
        _functions_.load_template(self, templates)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        template = self.bipeds if self.flavour == 'BIPED' else self.quadrupeds if self.flavour == 'QUADRUPED' else self.equipment
        
        template_uses_armatures = {'Gun' : True, 'Bow' : True, 'Sword_1H' : False, 'Shield' : False, 
            'Mannequin' : True, 'Femmequin' : True, 'Mannequin_Female' : True}
        template_uses_actions = {'Gun' : False, 'Bow' : False, 'Sword_1H' : False, 'Shield' : False, 
            'Mannequin' : False, 'Femmequin' : False, 'Mannequin_Female' : False}
        
        layout = self.layout
        row = layout.row()
        row.prop(self, "flavour", text="")
        row.prop(self, "rescale")
        row = layout.row()
        if self.flavour == 'BIPED':
            row.prop(self, "bipeds", text="")
        elif self.flavour == 'QUADRUPED':
            row.prop(self, "quadrupeds", text="")
        elif self.flavour == 'EQUIPMENT':
            row.prop(self, "equipment", text="")

        row = layout.row(align=False)
        arm_col = row.column(align=True)
        arm_row = arm_col.row(align=True)
        arm_row.prop(self, "armatures", toggle=True)
        arm_row.prop(self, "controls", toggle=True, text="", icon='BONE_DATA')
        arm_row.prop(self, "rigging", toggle=True, text="", icon='CONSTRAINT_BONE')
        arm_col.enabled = template_uses_armatures[template]
        split = row.split()
        act_col = split.column(align=True)
        act_row = act_col.row(align=True)
        act_row.prop(self, "actions", toggle=True)
        act_row.prop(self, "actions", toggle=True, text="", icon='CON_ACTION')
        act_col.enabled = template_uses_actions[template]

        row = layout.row(align=False)
        me_col = row.column(align=True)
        me_row = me_col.row(align=True)
        me_row.prop(self, "meshes", toggle=True)
        me_row.prop(self, "instance", toggle=True, text="", icon='MOD_DATA_TRANSFER')
        me_row.prop(self, "lods", toggle=True, text="", icon='MOD_DECIM')
        split = row.split()
        ma_col = split.column(align=True)
        ma_row = ma_col.row(align=True)
        ma_row.prop(self, "materials", toggle=True)
        ma_row.prop(self, "remap", toggle=True, text="", icon='IMAGE_REFERENCE')
        
        
        
        """col = row.column(align=True)
        arma_row = col.row(align=True)
        arma_row.prop(self, "armatures", toggle=True)
        arma_row.prop(self, "controls", toggle=True, text="", icon='BONE_DATA')
        arma_row.prop(self, "rigging", toggle=True, text="", icon='CONSTRAINT_BONE')
        row.prop(self, "meshes", toggle=True)
        row.prop(self, "materials", toggle=True)
        row.prop(self, "actions", toggle=True)
        row = layout.row()
        row.prop(self, "rescale")
        row.prop(self, "lods")
        row.prop(self, "instance")
        row.prop(self, "remap")"""
        

        