import bpy

from . import Pose_Functions_Mapping

class JK_PT_MMT_Retarget_Options(bpy.types.Panel):    
    bl_label = "Mapping"
    bl_idname = "JK_PT_MMT_Retarget_Options"
    bl_space_type = 'VIEW_3D'    
    bl_context = 'posemode'
    bl_region_type = 'UI'
    bl_category = "Mr Mannequins Tools"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = bpy.context.object
        prefs = bpy.context.preferences.addons["MrMannequinsTools"].preferences
        mapping = prefs.Mapping
        retargets = prefs.Retargets
        MMT = armature.JK_MMT
        if armature != None and len(bpy.context.selected_objects) > 0:
            if armature.type == 'ARMATURE':
                row = layout.row()
                if armature.JK_MMT.Rig_type in ['GUN', 'BOW']:
                    row.label(text="Sorry no mapping for weapons... yet!")
                if len(armature.JK_MMT.Retarget_data) > 0 and MMT.Rig_type != 'TEMPLATE':
                    layout.operator("jk.retarget_anim")
                    layout.operator("jk.save_retarget_data")
                    if len(mapping) > 0:
                        row.operator("jk.force_mapping_names", text="Set Control Names")
                
                if len(MMT.Retarget_data) > 0:
                    if len(retargets) > 0:
                        row.operator("jk.force_retarget_names", text="Set Deform Names")
                    for p_bone in bpy.context.selected_pose_bones:
                        for data in MMT.Retarget_data:
                            if p_bone.name == data.Control_name:
                                box = layout.box()
                                if len(mapping) > 0:
                                    mapping_name = Pose_Functions_Mapping.Get_Mapping_Name(data.Mapping_indices, mapping)
                                    if mapping_name != "":
                                        box.label(text=mapping_name)
                                row = box.row()
                                row.label(text=data.name + " - " + data.Control_name)
                                row = box.row()
                                row.prop(data, "Retarget_method", text="")
                                row.alignment = 'LEFT'
                                row.prop(data, "Mapping_indices", text="")
                else:
                    layout.label(text="No mapping information to display...")
            
                                  
                                