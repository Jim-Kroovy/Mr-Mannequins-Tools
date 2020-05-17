import bpy

from bpy.props import (BoolProperty, StringProperty)

# socket properties...
class JK_MMT_Socket_Props(bpy.types.PropertyGroup):
       
    def Update_Subtarget(self, context):
        if self.Is_attached:
            if self.Socket_subtarget != 'None':
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].subtarget = self.Socket_subtarget
            else:
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].subtarget = ""
    
    def Update_Target(self, context):
        if self.Is_attached:
            if self.Socket_target != 'None':
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].target = bpy.data.objects[self.Socket_target]
                self.id_data.constraints["MMT SOCKET - Copy Transforms"].subtarget = ""
            else:
                self.Is_attached = False
                    
    def Update_Attach(self, context):
        if self.Is_attached:          
            constraint = self.id_data.constraints.new('COPY_TRANSFORMS')
            constraint.name = "MMT SOCKET - " + constraint.name
            constraint.show_expanded = False
            if self.Socket_target != "":
                constraint.target = bpy.data.objects[self.Socket_target]
            if self.Socket_subtarget != "":
                constraint.subtarget = self.Socket_subtarget
        else:       
            for constraint in self.id_data.constraints:
                if constraint.name.startswith("MMT SOCKET - "):
                    self.id_data.constraints.remove(constraint)
                                               
    Socket_target: StringProperty(
        name="Target",
        description="The object to attach mesh/armature to",
        default="",
        update=Update_Target
        )
    
    Socket_subtarget: StringProperty(
        name="Sub Target",
        description="The bone/vertex group to attach mesh/armature to (if required)",
        default="",
        update=Update_Subtarget
        )        
    
    Is_attached: BoolProperty(
        name="Is Attached",
        description="Is this mesh/armature currently attached to the target",
        default=False,
        update=Update_Attach
        )
