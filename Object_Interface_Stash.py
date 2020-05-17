import bpy
import os

# stash interface panel...       
class JK_PT_MMT_Stash(bpy.types.Panel):
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
                #if armature.get('MrMannequinRig') != None:
                    #layout.operator("jk.u_updaterig", text="Update Rig (1.1)")
                #elif armature.get("MMT Rig Version") == None and armature.JK_MMT.Rig_type != 'NONE':
                    #layout.operator("jk.u_updaterig", text="Update Rig (1.2)")