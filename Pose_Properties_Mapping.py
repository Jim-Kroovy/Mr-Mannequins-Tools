import bpy

from bpy.props import (BoolProperty, StringProperty, CollectionProperty)

# mapping name broken down into strings...
class JK_MMT_Section_Mapping(bpy.types.PropertyGroup):
    
    Show_strings: BoolProperty(
        name="Edit",
        description="Show the strings of this section",
        default=False
        )

    Section: StringProperty(
        name="Name",
        description="Name to append suffixes to",
        default="",
        maxlen=1024,
        )
    
    First: StringProperty(
        name="Index",
        description="First section suffix",
        default="",
        maxlen=1024,
        )
        
    Second: StringProperty(
        name="Side",
        description="Second section suffix",
        default="",
        maxlen=1024,
        )

# name of the section + collection of broken down names...
class JK_MMT_Joint_Mapping(bpy.types.PropertyGroup):
    
    Show_sections: BoolProperty(
        name="Expand",
        description="Show the sections of this joint",
        default=False
        )
    
    Joint: StringProperty(
        name="Section",
        description="Joint of part",
        default="",
        maxlen=1024,
        )

    First: StringProperty(
        name="Index",
        description="First joint suffix",
        default="",
        maxlen=1024,
        )

    Second: StringProperty(
        name="Side",
        description="Second joint suffix",
        default="",
        maxlen=1024,
        )
    
    Sections: CollectionProperty(type=JK_MMT_Section_Mapping)    

# name of the part + collection of sections...    
class JK_MMT_Part_Mapping(bpy.types.PropertyGroup):
    
    Show_joints: BoolProperty(
        name="Expand",
        description="Show the joints of this part",
        default=False
        )

    Part: StringProperty(
        name="Part",
        description="Part of body",
        default="",
        maxlen=1024,
        )
    
    First: StringProperty(
        name="Index",
        description="First part suffix",
        default="",
        maxlen=1024,
        )

    Second: StringProperty(
        name="Side",
        description="Second part suffix",
        default="",
        maxlen=1024,
        )
    
    Joints: CollectionProperty(type=JK_MMT_Joint_Mapping)  

Default_mapping = {               
    ("Anim", "", "") : 
        {("Root", "", "") : [ 
            ("", "", "")],
        ("IK", "", "") : [
            ("Root", "Hands", ""),
            ("Root", "Feet", ""),
            ("Hand", "", "L"),
            ("Hand", "", "R"),
            ("Hand", "Grip", "L"),
            ("Hand", "Grip", "R"),
            ("Foot", "", "L"),
            ("Foot", "", "R")]},
    ("Torso", "", "") : 
        {("Hip", "", "") : [
            ("Sacrum", "", ""),
            ("Pelvis", "", "L"),
            ("Pelvis", "", "R")],
        ("Spine", "", "") : [
            ("Lumbar", "Lower", ""),
            ("Lumbar", "Upper", ""),
            ("Thoracic", "Lower", ""),
            ("Thoracic", "Upper", ""),
            ("Cervical", "Lower", ""),
            ("Cervical", "Upper", "")],
        ("Abdomen", "", "") : [
            ("Belly", "", "")],
        ("Chest", "", "") : [
            ("Lung", "", "L"),
            ("Lung", "", "R"),
            ("Breast", "", "L"),
            ("Breast", "", "R")],
        ("Shoulder", "", "L") : [
            ("Clavicle", "", ""),
            ("Scapula", "", "")],
        ("Shoulder", "", "R") : [
            ("Clavicle", "", ""),
            ("Scapula", "", "")]},
    ("Head", "", "") : 
        {("Skull", "", "") : [
            ("Occipital", "", ""),
            ("Mandible", "", ""),
            ("Face", "", "")],
        ("Brow", "", "") : [
            ("", "", "Middle"),
            ("", "01", "L"),
            ("", "01", "R"),
            ("", "02", "L"),
            ("", "02", "R")],
        ("Eye", "", "L") : [ 
            ("Ball", "", ""),
            ("Lid", "Upper", ""),
            ("Lid", "Lower", "")],
        ("Eye", "", "R") : [
            ("Ball", "", ""),
            ("Lid", "Upper", ""),
            ("Lid", "Lower", "")],
        ("Nose", "", "") : [
            ("", "Upper", ""),
            ("", "Lower", ""),
            ("Nostril", "", "L"),
            ("Nostril", "", "R")],
        ("Cheek", "", "L") : [
            ("", "", "")],
        ("Cheek", "", "R") : [
            ("", "", "")],
        ("Lips", "", "") : [    
            ("", "Upper", ""),
            ("", "Lower", ""),
            ("", "Upper", "L"),
            ("", "Upper", "R"),
            ("", "Lower", "L"),
            ("", "Lower", "R"),
            ("", "Corner", "L"),
            ("", "Corner", "R")],
        ("Tongue", "", "") : [     
            ("Tongue", "", "01"),
            ("Tongue", "", "02"),
            ("Tongue", "", "03")],
        ("Throat", "", "") : [
            ("Cartilage", "", "")],       
        ("Ear", "", "L") : [       
            ("", "", "")],
        ("Ear", "", "R") : [       
            ("", "", "")],
        ("Hair", "", "") : [
            ("Rear", "", "01"),
            ("Rear", "", "02"),
            ("Rear", "", "03")]},
    ("Arm", "", "L") : 
        {("Shoulder", "", "") : [
            ("Humerus", "", ""),
            ("Twist", "", "")],
        ("Elbow", "", "") : [
            ("Ulna", "", ""),
            ("Radius", "", ""),
            ("Twist", "", "")],
        ("Wrist", "", "") : [
            ("Twist", "", ""),
            ("Carpus", "", ""),
            ("Metacarpal", "01", ""),
            ("Metacarpal", "02", ""),
            ("Metacarpal", "03", ""),
            ("Metacarpal", "04", ""),
            ("Metacarpal", "05", ""),
            ("Equip", "", "")],    
        ("Thumb", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", "")],
        ("Index", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Middle", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Ring", "", "") : [            
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Little", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")]},
    ("Arm", "", "R") : 
        {("Shoulder", "", "") : [
            ("Humerus", "", ""),
            ("Twist", "", "")],
        ("Elbow", "", "") : [
            ("Ulna", "", ""),
            ("Radius", "", ""),
            ("Twist", "", "")],
        ("Wrist", "", "") : [
            ("Twist", "", ""),
            ("Carpus", "", ""),
            ("Metacarpal", "01", ""),
            ("Metacarpal", "02", ""),
            ("Metacarpal", "03", ""),
            ("Metacarpal", "04", ""),
            ("Metacarpal", "05", ""),
            ("Equip", "", "")],    
        ("Thumb", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", "")],
        ("Index", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Middle", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Ring", "", "") : [            
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Little", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")]}, 
    ("Leg", "", "L") :
        {("Hip", "", "") : [
            ("Femur", "", ""),
            ("Twist", "", "")],
        ("Knee", "", "") : [
            ("Tibia", "", ""),
            ("Fibula", "", ""),
            ("Twist", "", "")],
        ("Ankle", "", "") : [
            ("Twist", "", ""),
            ("Tarsals", "", ""),
            ("Metatarsal", "01", ""),
            ("Metatarsal", "02", ""),
            ("Metatarsal", "03", ""),
            ("Metatarsal", "04", ""),
            ("Metatarsal", "05", "")],     
        ("Big", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", "")],
        ("Index", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Middle", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Ring", "", "") : [            
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Little", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")]},
    ("Leg", "", "R") :
        {("Hip", "", "") : [
            ("Femur", "", ""),
            ("Twist", "", "")],
        ("Knee", "", "") : [
            ("Tibia", "", ""),
            ("Fibula", "", ""),
            ("Twist", "", "")],
        ("Ankle", "", "") : [
            ("Twist", "", ""),
            ("Tarsals", "", ""),
            ("Metatarsal", "01", ""),
            ("Metatarsal", "02", ""),
            ("Metatarsal", "03", ""),
            ("Metatarsal", "04", ""),
            ("Metatarsal", "05", "")],     
        ("Big", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", "")],
        ("Index", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Middle", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Ring", "", "") : [            
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")], 
        ("Little", "", "") : [
            ("Phalanx", "01", ""),
            ("Phalanx", "02", ""),
            ("Phalanx", "03", "")]},
    ("Tail", "", "") : 
        {("Spine", "", "") : [
            ("Caudal", "", "01"),
            ("Caudal", "", "02"),
            ("Caudal", "", "03"),
            ("Caudal", "", "04"),
            ("Caudal", "", "05")]},    
    ("Wing", "", "L") : 
        {("Shoulder", "", "") : [
            ("Humerus", "", ""),
            ("Twist", "", "")],
        ("Elbow", "", "") : [
            ("Ulna", "", ""),
            ("Radius", "", ""),
            ("Twist", "", "")],
        ("Wrist", "", "") : [
            ("Carpus", "", ""),
            ("Twist", "", "")]},
    ("Wing", "", "R") : 
        {("Shoulder", "", "") : [
            ("Humerus", "", ""),
            ("Twist", "", "")],
        ("Elbow", "", "") : [
            ("Ulna", "", ""),
            ("Radius", "", ""),
            ("Twist", "", "")],
        ("Wrist", "", "") : [
            ("Carpus", "", ""),
            ("Twist", "", "")]},
        }