import bpy

# socket interface panel...       
class JK_PT_MMT_Socket(bpy.types.Panel):
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
            #layout.label(text="Active Object")
            layout.prop_search(obj.JK_MMT.Socket_props, "Socket_target", scene, "objects")
            if obj.JK_MMT.Socket_props.Socket_target != "":
                target = bpy.data.objects[obj.JK_MMT.Socket_props.Socket_target]
                if bpy.data.objects[obj.JK_MMT.Socket_props.Socket_target].type in ["ARMATURE", "MESH"]:
                    string = "bones" if obj.type == "ARMATURE" else "vertex_groups" if obj.type == "MESH" else ""
                    layout.prop_search(obj.JK_MMT.Socket_props, "Socket_subtarget", target.data, string)            
            layout.prop(obj.JK_MMT.Socket_props, "Is_attached")               
        else:
            layout.label(text="Please select an object for socket settings")