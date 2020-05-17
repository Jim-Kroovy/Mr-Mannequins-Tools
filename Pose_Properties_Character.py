import bpy

from bpy.props import (StringProperty, BoolProperty, IntProperty)

# mesh specific options...        
class JK_MMT_Character_Props(bpy.types.PropertyGroup):
    
    Character_type: StringProperty(
        name="Type",
        description="The rig type used by the character mesh",
        default="None",
        maxlen=1024,
        )
    
    Character_name: StringProperty(
        name="Name",
        description="The name used for the character",
        default="None",
        maxlen=1024,
        )
    
    Is_default: BoolProperty(
        name="Is MMT Default",
        description="Is this a default mesh that i've provided",
        default=False
        )
        
    Is_female: BoolProperty(
        name="Is Female",
        description="Does this mesh need female bones. Sometimes male and female meshes might use the same points of rotation so this setting is relevant",
        default=False
        )
    # not currently in use...
    LOD_count: IntProperty(
        name="LOD Count",
        description="Number of different levels of detail. Not including the base mesh (LOD0)",
        default = 0
        )
    
    # think i'll be putting a collection or two here for morphable characters in the future...    
    #Morph_data: