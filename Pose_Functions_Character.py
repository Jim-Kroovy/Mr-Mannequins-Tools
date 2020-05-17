import bpy

# return the possible character meshes a rig can be set to...
Get_Characters_Result_Reference=[]
def Get_Character_Meshes(self, context):
    items = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if obj.data.JK_MMT.Character_type == self.Rig_type and self.Rig_type != 'NONE':
                if not any(item[1] == obj.data.JK_MMT.Character_name for item in items):
                    items.append((obj.name, obj.data.JK_MMT.Character_name, obj.data.JK_MMT.Character_name))
                #if any(modifier.type == 'ARMATURE' for modifier in obj.modifiers
    
    # There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
    # https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
    global Get_Characters_Result_Reference
    Get_Characters_Result_Reference=items
    
    if len(items) > 0:
        return items
    else:
        return [('None', "None", 'None')]  