import bpy

# import inteface panel...            
class JK_PT_MMT_Import(bpy.types.Panel):    
    bl_label = "Import"
    bl_idname = "JK_PT_MMT_Import"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'objectmode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.prop_search(scene.JK_MMT, "Import_active", scene.JK_MMT, "Import_props", text="")
        if scene.JK_MMT.Import_active in scene.JK_MMT.Import_props:
            MMT = scene.JK_MMT.Import_props[scene.JK_MMT.Import_active]
            row.operator("jk.import_add_settings", text="", icon='COLLECTION_NEW')
            if scene.JK_MMT.Import_active != 'Default':
                row.operator("jk.import_remove_settings", text="", icon='TRASH').Name = scene.JK_MMT.Import_active
            armature = context.object
            #if armature != None and len(bpy.context.selected_objects) > 0:
            box = layout.box()
            box.prop(MMT, "Meshes") 
            if MMT.Meshes:
                box.prop(MMT, "Path_meshes")
                box.prop(MMT, "Batch_meshes")
                if not MMT.Batch_meshes:
                    #box.prop_search()?
                    box.prop(MMT, "Mesh_fbxs")                                                                                               
            box = layout.box()
            box.prop(MMT, "Animations")                        
            if MMT.Animations:
                box.prop(MMT, "Path_animations")
                box.prop(MMT, "Batch_animations")
                if not MMT.Batch_animations:
                    #box.prop_search()?
                    box.prop(MMT, "Animation_fbxs")
                if armature != None and len(bpy.context.selected_objects) > 0:
                    if armature.type == 'ARMATURE':
                        if len(armature.JK_MMT.Retarget_data) > 0:
                            box.prop(MMT, "Anim_to_active")
                #box.prop(MMT, "I_anim_curves")    
                box.prop(MMT, "Scale_keyframes")                                                                  
                #box.prop(MMT, "Root_motion")
                #box.prop(MMT, "Key_controls")
                box.prop(MMT, "Frame_offset")
                if 'ue4curves' in bpy.context.preferences.addons.keys():
                    box.prop(MMT, "Use_most_host") 

            if MMT.Meshes or MMT.Animations:
                box = layout.box()
                box.prop(MMT, "Show_advanced", icon='DOWNARROW_HLT')
                if MMT.Show_advanced:
                    box.alignment = 'LEFT'
                    box.prop(MMT, "Add_root")
                    box.prop(MMT, "Clean_up")
                    box.prop(MMT, "User_props")
                    box.prop(MMT, "Leaf_bones")
                    box.prop(MMT, "Primary_bone_axis")
                    box.prop(MMT, "Secondary_bone_axis")
                    box.prop(MMT, "Manual_orient")
                    if MMT.Manual_orient:
                        box.prop(MMT, "Axis_forward")
                        box.prop(MMT, "Axis_up")
                layout.label(text="Apply Transforms:")
                row = layout.row()
                row.prop(MMT, "Apply_location")
                row.prop(MMT, "Apply_rotation")
                row.prop(MMT, "Apply_scale")
                layout.operator("jk.i_fbx")
        else:
            layout.label(text="No import options with this name!") 
