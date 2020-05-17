import bpy

# export/import inteface panel...            
class JK_PT_MMT_Export(bpy.types.Panel):    
    bl_label = "Export"
    bl_idname = "JK_PT_MMT_Export"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'objectmode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        MMT = scene.JK_MMT.Export_props
        armature = context.object
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE':
                row = layout.row()
                row.prop_search(scene.JK_MMT, "Export_active", scene.JK_MMT, "Export_props", text="")
                if scene.JK_MMT.Export_active in scene.JK_MMT.Export_props:
                    MMT = scene.JK_MMT.Export_props[scene.JK_MMT.Export_active]
                    row.operator("jk.export_add_settings", text="", icon='COLLECTION_NEW')
                    if scene.JK_MMT.Export_active != 'Default':
                        row.operator("jk.export_remove_settings", text="", icon='TRASH').Name = scene.JK_MMT.Export_active
                    box = layout.box()
                    box.prop(MMT, "Meshes")
                    if MMT.Meshes:          
                        box.prop(MMT, "Path_meshes")
                        box.prop(MMT, "Batch_meshes")
                        box.prop(MMT, "Apply_modifiers")
                    box = layout.box()
                    box.prop(MMT, "Animations")
                    if MMT.Animations:                   
                        box.prop(MMT, "Path_animations")
                        box.prop(MMT, "Batch_animations")
                        box.prop(MMT, "Startend_keys")
                        box.prop(MMT, "Anim_step")
                        box.prop(MMT, "Simplify_factor")
                        box.prop(MMT, "Bake_deforms")
                        if MMT.Bake_deforms:
                            box.prop(MMT, "Bake_step")
                        if 'ue4curves' in bpy.context.preferences.addons.keys():
                            box.prop(MMT, "Use_most_host") 
                    if MMT.Meshes or MMT.Animations:
                        box = layout.box()
                        box.prop(MMT, "Show_advanced", icon='DOWNARROW_HLT')
                        if MMT.Show_advanced:
                            box.alignment = 'LEFT'
                            box.prop(MMT, "Add_leaf_bones")
                            box.prop(MMT, "Primary_bone_axis")
                            box.prop(MMT, "Secondary_bone_axis")
                            box.prop(MMT, "Axis_forward")
                            box.prop(MMT, "Axis_up")
                        layout.operator("jk.e_fbx")               
                else:
                    layout.label(text="No export options with this name!") 
            else:
                layout.label(text="An armature must be active to export")
        else:
            layout.label(text="An armature must be active to export")