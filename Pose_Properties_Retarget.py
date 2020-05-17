import bpy

from . import Pose_Functions_Retarget

from bpy.props import (StringProperty, IntVectorProperty, EnumProperty, CollectionProperty, BoolProperty)

# name of the bone and the mapping indices it retargets to...
class JK_MMT_Retarget_Item(bpy.types.PropertyGroup):
    
    Show_children: BoolProperty(
        name="Expand",
        description="Show the children of this bone",
        default=False
        ) 
    
    Indices: IntVectorProperty(
        name="Indices",
        description="Indices to map to the bones name",
        default=(-1, -1, -1),
        size=3,
        )

    Parent: StringProperty(
        name="Parent",
        description="Parent of this bone",
        default="",
        maxlen=1024,
        )

    Retarget: EnumProperty(
        name="Retargeting Translation",
        description="Set bone translation retargeting",
        items=[('SKELETON', 'Skeleton', "Use translation from skeleton"),
        ('ANIMATION', 'Animation', "Use translation from animation")],
        #('ANIMATION_SCALED', 'Animation Scaled', "Biped based rig"),
        #('ANIMATION_RELATIVE', 'Animation Relative', "Weapon based rig"),
        #('ORIENT_SCALE', 'Orient and Scale', "User created rig")],
        default='ANIMATION',
    	)

    Type: EnumProperty(
        name="Retarget Type",
        description="Set the retarget type. (only used while retargeting)", 
        items=[('NONE', 'Manual', "Manually assign rotation"),
        ('STRETCH', 'Stretch', "Stretches to target"),
        ('TWIST_HOLD', 'Twist Hold', "Holds back the Y rotation. (eg: Upper Arm Twist)"),
        ('TWIST_FOLLOW', 'Twist Follow', "Follows targets Y rotation. (eg: Lower Arm Twist)"),
        ('ROOT_COPY', 'Root Copy', "Copies world space rotation of it's parent"),
        ('IK_DEFAULT', 'IK Default', "An IK deform bone present in the default rig. (You will need to remove/set this bone up yourself)")],
        default='NONE',
        )
        
    Subtarget: StringProperty(
        name="Subtarget",
        description="Subtarget during retargeting (if any)",
        default="",
        maxlen=1024,
        )

# name of retargeting + collection of bone to indices mapping...
class JK_MMT_Retarget_Dictionary(bpy.types.PropertyGroup):
    
    Show_bones: BoolProperty(
        name="Expand",
        description="Show the bones of this retarget",
        default=False
        )
    
    Bones: CollectionProperty(type=JK_MMT_Retarget_Item)


class JK_MMT_Retarget_Props(bpy.types.PropertyGroup):
    
    Retarget_method: EnumProperty(
        name="Retargeting Translation",
        description="Set bone translation retargeting",
        items=[('SKELETON', 'Skeleton', "Use translation from skeleton"),
        ('ANIMATION', 'Animation', "Use translation from animation")],
        #('ANIMATION_SCALED', 'Animation Scaled', "Use translation and scale from animation"),
        #('ANIMATION_RELATIVE', 'Animation Relative', "Use translation and scale from animation"),
        #('ORIENT_SCALE', 'Orient and Scale', "Use translation and scale from animation")],
        default='SKELETON'
        )
    
    Retarget_type: EnumProperty(
        name="Retarget Type",
        description="Set the retarget type. (only used while retargeting)",
        items=[('NONE', 'Manual', "Manually assign rotation"),
        ('STRETCH', 'Stretch', "Stretches to target"),
        ('TWIST_HOLD', 'Twist Hold', "Holds back the Y rotation. (eg: Upper Arm Twist)"),
        ('TWIST_FOLLOW', 'Twist Follow', "Follows targets Y rotation. (eg: Lower Arm Twist)"),
        ('ROOT_COPY', 'Root Copy', "Copies world space rotation of it's parent"),
        ('IK_DEFAULT', 'IK Default', "Is an IK deform bone present in the default rig. (You will need to remove/set this bone up yourself)"),
        ('REMOVE', 'Remove', "Get rid of this bone when applying control bones")],
		default='NONE'
        )

    Subtarget: StringProperty(
        name="Subtarget",
        description="Subtarget during retargeting (if any)",
        default="",
        maxlen=1024,
        )
    
    Mapping_indices: IntVectorProperty(
        name="Mapping Indices",
        description="Indices used to map this bone between armatures",
        default=(-1, -1, -1),
        size=3,
        )
            
    Control_name: StringProperty(
        name="Control Name",
        description="Controlling bone",
        default="",
        maxlen=1024,
        )

Default_retargets = {
    "UE4" : {
	    "pelvis" : [(1, 0, 0), "root", "ANIMATION", "STRETCH", "spine_01"],
	    "spine_01" : [(1, 1, 0), "pelvis", "SKELETON", "STRETCH", "spine_02"],
	    "spine_02" : [(1, 1, 2), "spine_01", "SKELETON", "STRETCH", "spine_03"],
	    "spine_03" : [(1, 1, 3), "spine_02", "SKELETON", "STRETCH", "neck_01"],
	    "clavicle_l" : [(1, 4, 0), "spine_03", "SKELETON", "STRETCH", "upperarm_l"],
	    "upperarm_l" : [(3, 0, 0), "clavicle_l", "SKELETON", "STRETCH", "lowerarm_l"],
	    "lowerarm_l" : [(3, 1, 0), "upperarm_l", "SKELETON", "STRETCH", "hand_l"],
	    "hand_l" : [(3, 2, 1), "lowerarm_l", "SKELETON", "NONE", ""],
	    "index_01_l" : [(3, 4, 0), "hand_l", "SKELETON", "STRETCH", "index_02_l"],
	    "index_02_l" : [(3, 4, 1), "index_01_l", "SKELETON", "STRETCH", "index_03_l"],
	    "index_03_l" : [(3, 4, 2), "index_02_l", "SKELETON", "NONE", ""],
	    "middle_01_l" : [(3, 5, 0), "hand_l", "SKELETON", "STRETCH", "middle_02_l"],
	    "middle_02_l" : [(3, 5, 1), "middle_01_l", "SKELETON", "STRETCH", "middle_03_l"],
	    "middle_03_l" : [(3, 5, 2), "middle_02_l", "SKELETON", "NONE", ""],
	    "pinky_01_l" : [(3, 7, 0), "hand_l", "SKELETON", "STRETCH", "pinky_02_l"],
	    "pinky_02_l" : [(3, 7, 1), "pinky_01_l", "SKELETON", "STRETCH", "pinky_03_l"],
	    "pinky_03_l" : [(3, 7, 2), "pinky_02_l", "SKELETON", "NONE", ""],
	    "ring_01_l" : [(3, 6, 0), "hand_l", "SKELETON", "STRETCH", "ring_02_l"],
	    "ring_02_l" : [(3, 6, 1), "ring_01_l", "SKELETON", "STRETCH", "ring_03_l"],
	    "ring_03_l" : [(3, 6, 2), "ring_02_l", "SKELETON", "NONE", ""],
	    "thumb_01_l" : [(3, 2, 2), "hand_l", "SKELETON", "STRETCH", "thumb_02_l"],
	    "thumb_02_l" : [(3, 3, 0), "thumb_01_l", "SKELETON", "STRETCH", "thumb_03_l"],
	    "thumb_03_l" : [(3, 3, 1), "thumb_02_l", "SKELETON", "NONE", ""],
	    "lowerarm_twist_01_l" : [(3, 2, 0), "lowerarm_l", "SKELETON", "TWIST_FOLLOW", "hand_l"],
	    "upperarm_twist_01_l" : [(3, 0, 1), "upperarm_l", "SKELETON", "TWIST_HOLD", "upperarm_l"],
	    "clavicle_r" : [(1, 5, 0), "spine_03", "SKELETON", "STRETCH", "upperarm_r"],
	    "upperarm_r" : [(4, 0, 0), "clavicle_r", "SKELETON", "STRETCH", "lowerarm_r"],
	    "lowerarm_r" : [(4, 1, 0), "upperarm_r", "SKELETON", "STRETCH", "hand_r"],
	    "hand_r" : [(4, 2, 1), "lowerarm_r", "SKELETON", "NONE", "_r"],
	    "index_01_r" : [(4, 4, 0), "hand_r", "SKELETON", "STRETCH", "index_02_r"],
	    "index_02_r" : [(4, 4, 1), "index_01_r", "SKELETON", "STRETCH", "index_03_r"],
	    "index_03_r" : [(4, 4, 2), "index_02_r", "SKELETON", "NONE", "_r"],
	    "middle_01_r" : [(4, 5, 0), "hand_r", "SKELETON", "STRETCH", "middle_02_r"],
	    "middle_02_r" : [(4, 5, 1), "middle_01_r", "SKELETON", "STRETCH", "middle_03_r"],
	    "middle_03_r" : [(4, 5, 2), "middle_02_r", "SKELETON", "NONE", "_r"],
	    "pinky_01_r" : [(4, 7, 0), "hand_r", "SKELETON", "STRETCH", "pinky_02_r"],
	    "pinky_02_r" : [(4, 7, 1), "pinky_01_r", "SKELETON", "STRETCH", "pinky_03_r"],
	    "pinky_03_r" : [(4, 7, 2), "pinky_02_r", "SKELETON", "NONE", "_r"],
	    "ring_01_r" : [(4, 6, 0), "hand_r", "SKELETON", "STRETCH", "ring_02_r"],
	    "ring_02_r" : [(4, 6, 1), "ring_01_r", "SKELETON", "STRETCH", "ring_03_r"],
	    "ring_03_r" : [(4, 6, 2), "ring_02_r", "SKELETON", "NONE", "_r"],
	    "thumb_01_r" : [(4, 2, 2), "hand_r", "SKELETON", "STRETCH", "thumb_02_r"],
	    "thumb_02_r" : [(4, 3, 0), "thumb_01_r", "SKELETON", "STRETCH", "thumb_03_r"],
	    "thumb_03_r" : [(4, 3, 1), "thumb_02_r", "SKELETON", "NONE", "_r"],
	    "lowerarm_twist_01_r" : [(4, 2, 0), "lowerarm_r", "SKELETON", "TWIST_FOLLOW", "hand_r"],
	    "upperarm_twist_01_r" : [(4, 0, 1), "upperarm_r", "SKELETON", "TWIST_HOLD", "upperarm_r"],
	    "neck_01" : [(1, 1, 4), "spine_03", "SKELETON", "STRETCH", "head"],
	    "head" : [(2, 0, 0), "neck_01", "SKELETON", "NONE", ""],
	    "thigh_l" : [(5, 0, 0), "pelvis", "SKELETON", "STRETCH", "calf_l"],
	    "calf_l" : [(5, 1, 0), "thigh_l", "SKELETON", "STRETCH", "foot_l"],
	    "calf_twist_01_l" : [(5, 2, 0), "calf_l", "SKELETON", "TWIST_FOLLOW", "foot_l"],
	    "foot_l" : [(5, 2, 1), "calf_l", "SKELETON", "NONE", ""],
	    "ball_l" : [(5, 3, 0), "foot_l", "SKELETON", "NONE", ""],
	    "thigh_twist_01_l" : [(5, 0, 1), "thigh_l", "SKELETON", "TWIST_HOLD", "thigh_l"],
	    "thigh_r" : [(6, 0, 0), "pelvis", "SKELETON", "STRETCH", "calf_r"],
	    "calf_r" : [(6, 1, 0), "thigh_r", "SKELETON", "STRETCH", "foot_r"],
	    "calf_twist_01_r" : [(6, 2, 0), "calf_r", "SKELETON", "TWIST_FOLLOW", "foot_r"],
	    "foot_r" : [(6, 2, 1), "calf_r", "SKELETON", "NONE", "_r"],
	    "ball_r" : [(6, 3, 0), "foot_r", "SKELETON", "NONE", "_r"],
	    "thigh_twist_01_r" : [(6, 0, 1), "thigh_r", "SKELETON", "TWIST_HOLD", "thigh_r"],
	    "ik_foot_root" : [(0, 1, 1), "root", "ANIMATION", "ROOT_COPY", "CB_root"],
	    "ik_foot_l" : [(0, 1, 6), "ik_foot_root", "ANIMATION", "IK_DEFAULT", ""],
	    "ik_foot_r" : [(0, 1, 7), "ik_foot_root", "ANIMATION", "IK_DEFAULT", ""],
	    "ik_hand_root" : [(0, 1, 0), "root", "ANIMATION", "ROOT_COPY", "CB_root"],
	    "ik_hand_gun" : [(0, 1, 5), "ik_hand_root", "ANIMATION", "IK_DEFAULT", ""],
	    "ik_hand_l" : [(0, 1, 2), "ik_hand_gun", "ANIMATION", "IK_DEFAULT", ""],
	    "ik_hand_r" : [(0, 1, 3), "ik_hand_gun", "ANIMATION", "IK_DEFAULT", ""],
	    "root" : [(0, 0, 0), "", "ANIMATION", "NONE", ""]},
    "Mixamo" : {
	    "mixamorig:Hips" : [(1, 0, 0), "Armature", "ANIMATION", "STRETCH", "mixamorig:Spine"],
	    "mixamorig:Spine" : [(1, 1, 0), "mixamorig:Hips", "SKELETON", "STRETCH", "mixamorig:Spine1"],
	    "mixamorig:Spine1" : [(1, 1, 2), "mixamorig:Spine", "SKELETON", "STRETCH", "mixamorig:Spine2"],
	    "mixamorig:Spine2" : [(1, 1, 3), "mixamorig:Spine1", "SKELETON", "STRETCH", "mixamorig:Neck"],
	    "mixamorig:LeftShoulder" : [(1, 4, 0), "mixamorig:Spine2", "SKELETON", "STRETCH", "mixamorig:LeftArm"],
	    "mixamorig:LeftArm" : [(3, 0, 0), "mixamorig:LeftShoulder", "SKELETON", "STRETCH", "mixamorig:LeftForeArm"],
	    "mixamorig:LeftForeArm" : [(3, 1, 0), "mixamorig:LeftArm", "SKELETON", "STRETCH", "mixamorig:LeftHand"],
	    "mixamorig:LeftHand" : [(3, 2, 1), "mixamorig:LeftForeArm", "SKELETON", "NONE", ""],
	    "mixamorig:LeftHandIndex1" : [(3, 4, 0), "mixamorig:LeftHand", "SKELETON", "STRETCH", "mixamorig:LeftHandIndex2"],
	    "mixamorig:LeftHandIndex2" : [(3, 4, 1), "mixamorig:LeftHandIndex1", "SKELETON", "STRETCH", "mixamorig:LeftHandIndex3"],
	    "mixamorig:LeftHandIndex3" : [(3, 4, 2), "mixamorig:LeftHandIndex2", "SKELETON", "NONE", ""],
	    "mixamorig:LeftHandMiddle1" : [(3, 5, 0), "mixamorig:LeftHand", "SKELETON", "STRETCH", "mixamorig:LeftHandMiddle2"],
	    "mixamorig:LeftHandMiddle2" : [(3, 5, 1), "mixamorig:LeftHandMiddle1", "SKELETON", "STRETCH", "mixamorig:LeftHandMiddle3"],
	    "mixamorig:LeftHandMiddle3" : [(3, 5, 2), "mixamorig:LeftHandMiddle2", "SKELETON", "NONE", ""],
	    "mixamorig:LeftHandPinky1" : [(3, 7, 0), "mixamorig:LeftHand", "SKELETON", "STRETCH", "mixamorig:LeftHandPinky2"],
	    "mixamorig:LeftHandPinky2" : [(3, 7, 1), "mixamorig:LeftHandPinky1", "SKELETON", "STRETCH", "mixamorig:LeftHandPinky3"],
	    "mixamorig:LeftHandPinky3" : [(3, 7, 2), "mixamorig:LeftHandPinky2", "SKELETON", "NONE", ""],
	    "mixamorig:LeftHandRing1" : [(3, 6, 0), "mixamorig:LeftHand", "SKELETON", "STRETCH", "mixamorig:LeftHandRing2"],
	    "mixamorig:LeftHandRing2" : [(3, 6, 1), "mixamorig:LeftHandRing1", "SKELETON", "STRETCH", "mixamorig:LeftHandRing3"],
	    "mixamorig:LeftHandRing3" : [(3, 6, 2), "mixamorig:LeftHandRing2", "SKELETON", "NONE", ""],
	    "mixamorig:LeftHandThumb1" : [(3, 2, 2), "mixamorig:LeftHand", "SKELETON", "STRETCH", "mixamorig:LeftHandThumb2"],
	    "mixamorig:LeftHandThumb2" : [(3, 3, 0), "mixamorig:LeftHandThumb1", "SKELETON", "STRETCH", "mixamorig:LeftHandThumb3"],
	    "mixamorig:LeftHandThumb3" : [(3, 3, 1), "mixamorig:LeftHandThumb2", "SKELETON", "NONE", ""],
	    "mixamorig:RightShoulder" : [(1, 5, 0), "mixamorig:Spine2", "SKELETON", "STRETCH", "mixamorig:RightArm"],
	    "mixamorig:RightArm" : [(4, 0, 0), "mixamorig:RightShoulder", "SKELETON", "STRETCH", "mixamorig:RightForeArm"],
	    "mixamorig:RightForeArm" : [(4, 1, 0), "mixamorig:RightArm", "SKELETON", "STRETCH", "mixamorig:RightHand"],
	    "mixamorig:RightHand" : [(4, 2, 1), "mixamorig:RightForeArm", "SKELETON", "NONE", ""],
	    "mixamorig:RightHandIndex1" : [(4, 4, 0), "mixamorig:RightHand", "SKELETON", "STRETCH", "mixamorig:RightHandIndex2"],
	    "mixamorig:RightHandIndex2" : [(4, 4, 1), "mixamorig:RightHandIndex1", "SKELETON", "STRETCH", "mixamorig:RightHandIndex3"],
	    "mixamorig:RightHandIndex3" : [(4, 4, 2), "mixamorig:RightHandIndex2", "SKELETON", "NONE", ""],
	    "mixamorig:RightHandMiddle1" : [(4, 5, 0), "mixamorig:RightHand", "SKELETON", "STRETCH", "mixamorig:RightHandMiddle2"],
	    "mixamorig:RightHandMiddle2" : [(4, 5, 1), "mixamorig:RightHandMiddle1", "SKELETON", "STRETCH", "mixamorig:RightHandMiddle3"],
	    "mixamorig:RightHandMiddle3" : [(4, 5, 2), "mixamorig:RightHandMiddle2", "SKELETON", "NONE", ""],
	    "mixamorig:RightHandPinky1" : [(4, 7, 0), "mixamorig:RightHand", "SKELETON", "STRETCH", "mixamorig:RightHandPinky2"],
	    "mixamorig:RightHandPinky2" : [(4, 7, 1), "mixamorig:RightHandPinky1", "SKELETON", "STRETCH", "mixamorig:RightHandPinky3"],
	    "mixamorig:RightHandPinky3" : [(4, 7, 2), "mixamorig:RightHandPinky2", "SKELETON", "NONE", ""],
	    "mixamorig:RightHandRing1" : [(4, 6, 0), "mixamorig:RightHand", "SKELETON", "STRETCH", "mixamorig:RightHandRing2"],
	    "mixamorig:RightHandRing2" : [(4, 6, 1), "mixamorig:RightHandRing1", "SKELETON", "STRETCH", "mixamorig:RightHandRing3"],
	    "mixamorig:RightHandRing3" : [(4, 6, 2), "mixamorig:RightHandRing2", "SKELETON", "NONE", ""],
	    "mixamorig:RightHandThumb1" : [(4, 2, 2), "mixamorig:RightHand", "SKELETON", "STRETCH", "mixamorig:RightHandThumb2"],
	    "mixamorig:RightHandThumb2" : [(4, 3, 0), "mixamorig:RightHandThumb1", "SKELETON", "STRETCH", "mixamorig:RightHandThumb3"],
	    "mixamorig:RightHandThumb3" : [(4, 3, 1), "mixamorig:RightHandThumb2", "SKELETON", "NONE", ""],
	    "mixamorig:Neck" : [(1, 1, 4), "mixamorig:Spine2", "SKELETON", "STRETCH", "mixamorig:Head"],
	    "mixamorig:Head" : [(2, 0, 0), "mixamorig:Neck", "SKELETON", "NONE", ""],
	    "mixamorig:LeftUpLeg" : [(5, 0, 0), "mixamorig:Hips", "SKELETON", "STRETCH", "mixamorig:LeftLeg"],
	    "mixamorig:LeftLeg" : [(5, 1, 0), "mixamorig:LeftUpLeg", "SKELETON", "STRETCH", "mixamorig:LeftFoot"],
	    "mixamorig:LeftFoot" : [(5, 2, 1), "mixamorig:LeftLeg", "SKELETON", "NONE", ""],
	    "mixamorig:LeftToeBase" : [(5, 3, 0), "mixamorig:LeftFoot", "SKELETON", "NONE", ""],
	    "mixamorig:RightUpLeg" : [(6, 0, 0), "mixamorig:Hips", "SKELETON", "STRETCH", "mixamorig:RightLeg"],
	    "mixamorig:RightLeg" : [(6, 1, 0), "mixamorig:RightUpLeg", "SKELETON", "STRETCH", "mixamorig:RightFoot"],
	    "mixamorig:RightFoot" : [(6, 2, 1), "mixamorig:RightLeg", "SKELETON", "NONE", ""],
	    "mixamorig:RightToeBase" : [(6, 3, 0), "mixamorig:RightFoot", "SKELETON", "NONE", ""],
	    "Armature" : [(0, 0, 0), "", "ANIMATION", "NONE", ""]}
    }