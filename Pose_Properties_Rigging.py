import bpy
import importlib

from bpy.props import (StringProperty, BoolProperty, BoolVectorProperty, IntProperty, IntVectorProperty, FloatProperty, FloatVectorProperty, EnumProperty, PointerProperty, CollectionProperty)

from . import (Pose_Functions_Rigging, Pose_Properties_Character, Pose_Functions_Character, Object_Properties_Socket, Pose_Properties_Retarget)

class JK_MMT_Head_Tracking_Props(bpy.types.PropertyGroup):
    # not currently used... (using update functions might not be the best way to do this)
    def Update_Head_Tracking(self, context):
        if self.id_data != None:
            bpy.ops.object.mode_set(mode='EDIT')
            axes = (True, False, False) if "X" in self.Axis else (False, True, False) if "Y" in self.Axis else (False, False, True)
            distance = (0 - self.Distance) if "NEGATIVE" in self.Axis else self.Distance
            vector = (distance, 0, 0 ) if "X" in self.Axis else (0, distance, 0) if "Y" in self.Axis else (0, 0, distance)
            h_bone = self.id_data.data.edit_bones[self.name]
            t_bone = self.id_data.data.edit_bones[self.Target]
            s_bone = self.id_data.data.edit_bones[self.Stretch]
            t_bone.head = h_bone.head
            t_bone.tail = h_bone.tail
            t_bone.roll = h_bone.roll
            bpy.ops.armature.select_all(action='DESELECT')
            t_bone.select_tail = True
            t_bone.select_head = True
            bpy.ops.transform.translate(value=vector, orient_type='NORMAL', constraint_axis=(axes[0], axes[1], axes[2]))
            t_bone.roll = 0
            s_bone.head = h_bone.head
            s_bone.tail = t_bone.head
            s_bone.roll = 0
            bpy.ops.object.mode_set(mode='POSE')

    Target: StringProperty(
        name="Target Name",
        description="The targets bones name",
        default="",
        maxlen=1024,
        )

    Stretch: StringProperty(
        name="Stretch Name",
        description="The stretch bones name",
        default="",
        maxlen=1024,
        )

    Neck: StringProperty(
        name="Neck Name",
        description="The neck bones name",
        default="",
        maxlen=1024,
        )

    Spine: StringProperty(
        name="Spine Name",
        description="The spine bones name",
        default="",
        maxlen=1024,
        )

    Axis:  EnumProperty(
        name="Forward Axis",
        description="The the local forward axis of the head bone",
        items=[('X', 'X', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_LOCLIKE", 1),
        ('Y', 'Y', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y', "", "CON_LOCLIKE", 3),
        ('Z', 'Z', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z', "", "CON_LOCLIKE", 5)],
        default='X',
        #update=Update_Head_Tracking
        )
        
    Distance: FloatProperty(
        name="Target Distance", 
        description="The distance the target is from the head. (in meters)", 
        default=0.25,
        #update=Update_Head_Tracking
        )

class JK_MMT_Twist_Bone_Props(bpy.types.PropertyGroup):
    
    Type: EnumProperty(
        name="Type",
        description="The type of twist bone to add",
        items=[('HEAD_HOLD', 'Head Hold', "Holds deformation at the head of the bone back by tracking to the target. (eg: Upper Arm Twist)"),
        ('TAIL_FOLLOW', 'Tail Follow', "Follows deformation at the tail of the bone by copying the Y rotation of the target. (eg: Lower Arm Twist)")],
        default='HEAD_HOLD'
        )

    Target: StringProperty(
        name="Target",
        description="The targets bones name",
        default="",
        maxlen=1024,
        )
    
    Parent: StringProperty(
        name="Parent",
        description="The original parent of the twist bone. (if any)",
        default="",
        maxlen=1024,
        )
    
    Float: FloatProperty(
        name="Float", 
        description="Either the head vs tail or influence depending on the twist type", 
        default=1.0, 
        min=0.0, 
        max=1.0,
        subtype='FACTOR',
        )

    Has_pivot: BoolProperty(
        name="Use Pivot",
        description="Does this twist bone have a pivot bone to define its limits?",
        default=False,
        )

    Limits_use: BoolVectorProperty(
        name="Use Limits",
        description="Which axes are limited",
        default=(False, False, False),
        size=3,
        subtype='EULER'
        )

    Limits_min: FloatVectorProperty(
        name="Limits Min",
        description="Min limits of rotation. (Degrees)",
        default=(0.0, 0.0, 0.0),
        size=3,
        subtype='EULER'
        )

    Limits_max: FloatVectorProperty(
        name="Limits Max",
        description="Max limits of rotation. (Degrees)",
        default=(0.0, 0.0, 0.0),
        size=3,
        subtype='EULER'
        )

class JK_MMT_Digit_Bone_Props(bpy.types.PropertyGroup):

    def Update_IKvsFK(self, context):
        if self.Last_IKvsFK == self.IKvsFK:
            print("Already using this method of digit control")
        else:
            if self.IKvsFK == 'NONE':
                Pose_Functions_Rigging.Set_IKvsFK_None_Digit(self)
            elif self.IKvsFK == 'OFFSET':
                Pose_Functions_Rigging.Set_IKvsFK_Offset_Digit(self)
        self.Last_IKvsFK = self.IKvsFK

    IKvsFK: EnumProperty(
        name="IK vs FK - Digits",
        description="Which method of IK vs FK to use",
        items=[('NONE', 'None', "Only use copy rotation controls"),
            ('OFFSET', 'Offset FK', "FK is offset from IK. (Scale control bone to curl finger)")],
            #('2', 'Switchable', "IK and FK can be switched between while keyframing")] # coming in the future...
        default='NONE',
        update=Update_IKvsFK
        )

    Last_IKvsFK: StringProperty(default='NONE')
    
    Main_axis:  EnumProperty(
        name="Main Axis",
        description="The main axis the digit curls around. (This should be the same for each bone in the digit)",
        items=[('X', 'X', "", "CON_ROTLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_ROTLIKE", 1),
        ('Z', 'Z', "", "CON_ROTLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_ROTLIKE", 3)],
        default='X'
        )
    
    Proximal: StringProperty(
        name="Proximal",
        description="Name of the first bone in the digit",
        default="",
        maxlen=1024,
        )

    Medial: StringProperty(
        name="Medial",
        description="Name of the second bone in the digit",
        default="",
        maxlen=1024,
        )

    Distal: StringProperty(
        name="Distal",
        description="Name of the third bone in the digit",
        default="",
        maxlen=1024,
        )

class JK_MMT_End_Bone_Props(bpy.types.PropertyGroup):
    
    Main_axis:  EnumProperty(
        name="Main Axis",
        description="The main axis the end bone rotates around. (The axis that rotates the deformation down)",
        items=[('X', 'X', "", "CON_ROTLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_ROTLIKE", 1),
        ('Z', 'Z', "", "CON_ROTLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_ROTLIKE", 3)],
        default='X'
        )
    
    Control: StringProperty(
        name="Control Name",
        description="Name of the bone that controls the end chain mechanism",
        default="",
        maxlen=1024,
        )

    Pivot: StringProperty(
        name="Pivot",
        description="Name of the bone used to pivot the end of chain. (eg: bone at the ball of the foot)",
        default="",
        maxlen=1024,
        )

    Pivot_axis:  EnumProperty(
        name="Pivot Axis",
        description="The main axis the pivot bone rotates around. (The axis that rotates the deformation down)",
        items=[('X', 'X', "", "CON_ROTLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_ROTLIKE", 1),
        ('Z', 'Z', "", "CON_ROTLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_ROTLIKE", 3)],
        default='X'
        )

class JK_MMT_Chain_Bone_Props(bpy.types.PropertyGroup):

    Target: StringProperty(
        name="Target",
        description="The IK target bone",
        default="",
        maxlen=1024,
        )

    Control: StringProperty(
        name="Control",
        description="The bone that controls the IK chain. (If there isn't one this will be equal to the target)",
        default="",
        maxlen=1024,
        )

    Control_local: StringProperty(
        name="Local Control",
        description="The local bone that controls the IK chain",
        default="",
        maxlen=1024,
        )
    
    Control_root: StringProperty(
        name="Root Control",
        description="The parented IK control target bones name",
        default="",
        maxlen=1024,
        )
  
    Parent: StringProperty(
        name="Parent",
        description="The bone at the beginning but not included in the chain. (if any)",
        default="",
        maxlen=1024,
        )
    
    Pole: StringProperty(
        name="Pole",
        description="The IK pole target bones name",
        default="",
        maxlen=1024,
        )
    
    Pole_local: StringProperty(
        name="Local Pole",
        description="The local IK pole target bones name",
        default="",
        maxlen=1024,
        )
    
    Pole_root: StringProperty(
        name="Root Pole",
        description="The parented IK pole target bones name",
        default="",
        maxlen=1024,
        )

    Root: StringProperty(
        name="IK Root",
        description="The IK root bone. (if any)",
        default="",
        maxlen=1024,
        )
    
    Pole_axis:  EnumProperty(
        name="Pole Axis",
        description="The local axis of the second bone that the pole target is created along. (pole angle might need to be adjusted)",
        items=[('X', 'X', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X', "", "CON_LOCLIKE", 1),
        ('Z', 'Z', "", "CON_LOCLIKE", 2),
        ('Z_NEGATIVE', '-Z', "", "CON_LOCLIKE", 3)],
        default='X'
        )
        
    Pole_distance: FloatProperty(
        name="Pole Distance", 
        description="The distance the pole target is from the IK parent. (meters)", 
        default=0.25
        )

    Has_pivots: BoolProperty(
        name="Use Pivots",
        description="Does this chain have a pivot bones to rotate targets around?",
        default=True,
        )

# IK chain specific options...        
class JK_MMT_IK_Props(bpy.types.PropertyGroup):

    Chain_side: EnumProperty(
        name="Side",
        description="The type of limb IK chain",
        items=[#('NONE', 'None', ""),
        ('LEFT', 'Left', ""),
        ('RIGHT', 'Right', "")],
        default='LEFT'
        )

    Chain_type: EnumProperty(
        name="Type",
        description="The type of limb IK chain",
        items=[('ARM', 'Arm', ""),
        ('LEG', 'Leg', "")],
        # Coming soon!
        #('WING', 'Wing', ""),
        #('TAIL', 'Tail', "")],
        default='ARM'
        )

    def Update_IK_Parenting(self, context):
        # don't do anything if we are already using the current option...
        if self.Last_parenting == self.IK_parenting:
            print("Already using this method of IK parenting")
        else:
            # if we aren't at the default setting return to it...
            if self.Last_parenting == 'ROOTED' or self.Last_parenting == 'SWITCHABLE':
                Pose_Functions_Rigging.Set_Parenting_None(self)
            # then set to whatever the new setting is... (default already set if that was chosen) 
            if self.IK_parenting == 'ROOTED':
                Pose_Functions_Rigging.Set_Parenting_Rooted(self)
            elif self.IK_parenting == 'SWITCHABLE':
                Pose_Functions_Rigging.Set_Parenting_Switchable(self)
        # and set the last option record for next time...
        self.Last_parenting = self.IK_parenting

    IK_parenting: EnumProperty(
        name="Parenting",
        description="Which method of IK parenting to use",
        items=[('NONE', 'None', "IK targets have no parents"),
            ('ROOTED', 'Parented', "IK targets are parented to their root"),
            ('SWITCHABLE', 'Switchable', "IK parenting can be switched and keyframed")],
        default='NONE',
        update=Update_IK_Parenting
        )
    
    Last_parenting: StringProperty(default='NONE')

    def Update_IKvsFK_Limbs(self, context):
        # don't do anything if we are already using the current option...
        if self.Last_IKvsFK == self.IKvsFK_limbs:
            print("Already using this method of IK vs FK")
        else:
            # if we aren't at the default setting return to it...
            if self.Last_IKvsFK == 'SWITCHABLE':
                Pose_Functions_Rigging.Set_IKvsFK_None(self)
            # then set to whatever the new setting is... (default already set if that was chosen) 
            elif self.IKvsFK_limbs == 'SWITCHABLE':
                Pose_Functions_Rigging.Set_IKvsFK_Switchable(self)
        # and set the last option record for next time...
        self.Last_IKvsFK = self.IKvsFK_limbs

    IKvsFK_limbs: EnumProperty(
        name="IK vs FK",
        description="Which method of IK vs FK to use",
        items=[('NONE', 'None', "Only use IK"),
            #('OFFSET', 'Offset FK', "FK is offset from IK"),
            ('SWITCHABLE', 'Switchable', "IK and FK can be switched between while keyframing")],
        default='NONE',
        update=Update_IKvsFK_Limbs
        )

    Last_IKvsFK: StringProperty(default='NONE')

    Current_switches: BoolVectorProperty(default=(False, False), size=2)   
    
    def Update_Parenting_Switch(self, context):
        if self.Chain_use_parent != self.Current_switches[0]:
            # if we are using the parent and not using FK...
            if self.Chain_use_parent and not self.Chain_use_fk:
                Pose_Functions_Rigging.Set_None_To_Rooted(self)                 
            # else we need to reverse the process...
            else:
                Pose_Functions_Rigging.Set_Rooted_To_None(self)
        self.Current_switches[0] = self.Chain_use_parent

    Chain_use_parent: BoolProperty(
        name="Use Parent",
        description="Switch between Parented vs Independent targets for this IK chain",
        default=False,
        update=Update_Parenting_Switch
        )            
    
    def Update_IKvsFK_Switch(self, context):
        if self.Chain_use_fk != self.Current_switches[1]:        
            if self.Chain_use_fk:
                if self.Chain_use_parent:
                    self.Current_switches[0] = False
                    self.Update_Parenting_Switch(context)
                Pose_Functions_Rigging.Set_IK_To_FK(self)               
            else:
                if self.Chain_use_parent:
                    self.Current_switches[0] = False
                    self.Update_Parenting_Switch(context)
                Pose_Functions_Rigging.Set_FK_To_IK(self)                                                            
        self.Current_switches[1] = self.Chain_use_fk  

    Chain_use_fk: BoolProperty(
        name="Use FK",
        description="Switch between IK vs FK for this IK chain",
        default=False,
        update=Update_IKvsFK_Switch
        )

    def Update_IK_Influence(self, context):
        if "GB" + self.name[2:] in bpy.context.object.pose.bones:
            o_bone = bpy.context.object.pose.bones["GB" + self.name[2:]]
            if "IK" in o_bone.constraints:
                o_bone.constraints["IK"].influence = self.Chain_ik_influence

    Chain_ik_influence: FloatProperty(
        name="Chain - IK Influence", 
        description="While using switchable IK vs FK this maintains the ability to display and keyframe the influence of the IK constraint when it's not available", 
        default=1.0, 
        min=0.0, 
        max=1.0,
        subtype='FACTOR', 
        update=Update_IK_Influence
        )

    def Update_Pole_angle(self, context):
        if "GB" + self.name[2:] in bpy.context.object.pose.bones:
            o_bone = bpy.context.object.pose.bones["GB" + self.name[2:]]
            if "IK" in o_bone.constraints:
                o_bone.constraints["IK"].pole_angle = self.Chain_pole_angle    
    
    Chain_pole_angle: FloatProperty(
        name="Pole Angle", 
        description="The angle of the IK pole target. (degrees)", 
        default=0.0,
        subtype='ANGLE',
        update=Update_Pole_angle
        )

    Chain_data: PointerProperty(type=JK_MMT_Chain_Bone_Props)

    End_data: PointerProperty(type=JK_MMT_End_Bone_Props)
    
# armature specific options...        
class JK_MMT_Rig_Props(bpy.types.PropertyGroup):
        
    def Update_Character_Mesh(self, context):
        for prop in bpy.data.objects[self.Character_meshes].data.JK_MMT.items():
            self.Character_props[prop[0]] = prop[1]

    def Update_Hide_Deform_Bones(self, context):
        armature = self.id_data
        deform_bones = [p_bone for p_bone in armature.pose.bones if p_bone.bone_group == armature.pose.bone_groups['Deform Bones']]
        mechanism_bones = [p_bone for p_bone in armature.pose.bones if p_bone.bone_group == armature.pose.bone_groups['Mechanism Bones']]
        for d_bone in deform_bones:
            d_bone.bone.hide = self.Hide_deform_bones
        for m_bone in mechanism_bones:
            m_bone.bone.hide = self.Hide_deform_bones

    def Update_Master_Mute(self, context):
        armature = self.id_data
        #deform_bones = [p_bone for p_bone in armature.pose.bones if p_bone.bone_group == armature.pose.bone_groups['Deform Bones']]
        #mechanism_bones = [p_bone for p_bone in armature.pose.bones if p_bone.bone_group == armature.pose.bone_groups['Mechanism Bones']]
        control_bones = [p_bone for p_bone in armature.pose.bones if p_bone.bone_group == armature.pose.bone_groups['Control Bones']]
        for bone in control_bones:
            for constraint in bone.constraints:
                constraint.mute = self.Mute_default_constraints

    Rig_type: EnumProperty(
        name="Rig Type",
        description="What type of rig the add-on registers the armature as",
        items=[('NONE', 'None', "Not a Mr Mannequin rig"),
        ('TEMPLATE', 'Template', "Retarget template rig"),
        ('MANNEQUIN', 'Mannequin', "Biped based rig"),
        ('GUN', 'Gun', "Gun based rig"),
        ('BOW', 'Bow', "Bow based rig"),
        ('CUSTOM', 'Custom', "User created rig")],
        default='NONE'
        )
    
    Mute_default_constraints: BoolProperty(
        name="Mute Constraints",
        description="Mute all control bone constraints. Useful when working with imported animations",
        default=False,
        update=Update_Master_Mute
        )
    
    Hide_deform_bones: BoolProperty(
        name="Hide Deform Bones",
        description="Hide the bones in the deform and mechanism bone groups while in pose mode",
        default=True,
        update=Update_Hide_Deform_Bones
        )
    
    IK_chain_data: CollectionProperty(type=JK_MMT_IK_Props)

    Head_tracking_data: CollectionProperty(type=JK_MMT_Head_Tracking_Props)

    Twist_bone_data: CollectionProperty(type=JK_MMT_Twist_Bone_Props)

    Digit_bone_data: CollectionProperty(type=JK_MMT_Digit_Bone_Props)
    
    Character_meshes: EnumProperty(
        name="Characters",
        description="Characters to set rig to",
        items=Pose_Functions_Character.Get_Character_Meshes,
        default=None,
        update=Update_Character_Mesh
        )
    
    Character_props: PointerProperty(type=Pose_Properties_Character.JK_MMT_Character_Props)
        
    Retarget_target: StringProperty(
        name="Target",
        description="Name of the armature we are retargeting too",
        default="None",
        maxlen=1024,
        )                 
    
    Force_template_rotations: BoolProperty(
        name="Force Template Rotations",
        description="Attempt to pose the mesh to fit the active templates default bone rotations and apply the deformation. WARNING! This is a work in progress",
        default = False
        )
        
    Force_template_locations: BoolProperty(
        name="Force Template Locations",
        description="Attempt to pose the mesh to fit the active templates default bone locations and apply the deformation. WARNING! This is a work in progress",
        default = False
        )
    
    Socket_props: PointerProperty(type=Object_Properties_Socket.JK_MMT_Socket_Props)
    
    Retarget_data: CollectionProperty(type=Pose_Properties_Retarget.JK_MMT_Retarget_Props)