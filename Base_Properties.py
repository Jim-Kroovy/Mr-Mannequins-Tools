import bpy
import os

from bpy.props import (StringProperty, BoolProperty, BoolVectorProperty, IntProperty, IntVectorProperty, FloatProperty, EnumProperty, PointerProperty, CollectionProperty)

from . import (Base_Functions, Object_Functions_Stash)

# There is a known bug with using a callback, Python must keep a reference to the strings returned by the callback or Blender will misbehave or even crash.
# https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
Get_Stashed_Armatures_Results_Reference = []
Get_Stashed_Meshes_Results_Reference = []
Get_Stashed_Materials_Results_Reference = []
Get_Import_Animations_Results_Reference = []
Get_Import_Meshes_Results_Reference = []

class JK_MMT_Import_Props(bpy.types.PropertyGroup):
    
    def Get_Import_Animations(self, context):
        result = Base_Functions.Get_Imports_FBX(self, context, self.Path_animations)   
        global Get_Import_Animations_Results_Reference
        Get_Import_Animations_Results_Reference = result
        return result
    
    def Get_Import_Meshes(self, context):
        result = Base_Functions.Get_Imports_FBX(self, context, self.Path_meshes)   
        global Get_Import_Meshes_Results_Reference
        Get_Import_Meshes_Results_Reference = result
        return result  
    
    Animations: BoolProperty(
        name="Import Animations",
        description="Import Animations",
        default = False
        )
        
    Meshes: BoolProperty(
        name="Import Meshes",
        description="Import Meshes",
        default = False
        )
    
    Animation_fbxs: EnumProperty(
        name="FBX",
        description="Animation to import and convert",
        items=Get_Import_Animations,
        default=None
        )
    
    Mesh_fbxs: EnumProperty(
        name="FBX",
        description="Mesh to import",
        items=Get_Import_Meshes,
        default=None
        )
    
    Batch_animations: BoolProperty(
        name="Batch Import Animations",
        description="Import all animations from animation import folder",
        default = True
        )
        
    Batch_meshes: BoolProperty(
        name="Batch Import Meshes",
        description="Import all meshes from animation import folder",
        default = True
        )
    
    Path_animations: StringProperty(
        name="Animation Import Folder",
        description="Directory to import animations from",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )
    
    Path_meshes: StringProperty(
        name="Mesh Import Folder",
        description="Directory to import meshes from",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )

    Anim_to_active: BoolProperty(
        name="Anim to Active",
        description="Whether we try to retarget the imported animation to the active armature or just import it (Retargets by bone name not mapping indices)",
        default = False
        )

    Scale_keyframes: BoolProperty(
        name="Scale Keyframes",
        description="Scale animation length to current scene framerate",
        default = True
        )
    
    Root_motion: BoolProperty(
        name="Convert Root Motion",
        description="Convert root motion from imported armature object to targets root bone. If false no root motion will be used",
        default = True
        )
    
    Key_controls: BoolProperty(
        name="Key Controls",
        description="Keyframe 'Mute Default Constraints' off on the first frame of the imported animation. Also keyframes the IK targets 'Use FK'/'Use Parent' properties if applicable. These controls always get switched off for accurate importation",
        default = True
        )
        
    Anim_curves: BoolProperty(
        name="Use Accurate Import",
        description="Accurately import and convert animations using curves instead of constraints. WARNING: If true aimations may take much longer to import!",
        default = False
        )
    
    Show_advanced: BoolProperty(
        name="Advanced",
        description="Show advanced FBX import options. (Only edit these if you know what they do!)",
        default = False
        )

    Primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        description="Primary Bone Axis",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='Y'
        )

    Secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        description="Secondary Bone Axis",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='X'
        )
    
    Manual_orient: BoolProperty(
        name="Use Manual Orientation",
        description="Specify orientation and scale, instead of using embedded data in FBX file",
        default = False
        )

    Axis_forward: EnumProperty(
        name="Forward",
        description="Forward",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='-Z'
        )
    
    Axis_up: EnumProperty(
        name="Up",
        description="Up",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='Y'
        )
    
    User_props: BoolProperty(
        name="Import User Properties",
        description="Import user properties as custom properties. WARNING! Setting True might cause import errors with some properties found in .FBXs",
        default = False
        )

    Leaf_bones: BoolProperty(
        name="Ignore Leaf Bones",
        description="Ignore the last bone at the end of each chain (used to mark the length of the previous bone)",
        default = False
        )

    Frame_offset: IntProperty(
        name="Frame Offset",
        description="Offset imported actions keyframes to start from this frame",
        default = 1
        )

    Use_most_host: BoolProperty(
        name="Use Most Host Import",
        description="Import uses Most Host LAs FBX import script for animations",
        default = False
        )
    
    Apply_location: BoolProperty(
        name="Location",
        description="Applies location the armature gets imported with",
        default = False
        )

    Apply_rotation: BoolProperty(
        name="Rotation",
        description="Applies rotation the armature gets imported with",
        default = True
        )

    Apply_scale: BoolProperty(
        name="Scale",
        description="Applies scale the armature gets imported with",
        default = False
        )

    Add_root: BoolProperty(
        name="Add Root Bone",
        description="Adds a root bone to the imported FBX file at the correct location and rotation (if importing animations this also converts root motion from the object to the root bone)",
        default = True
        )

    Clean_up: BoolProperty(
        name="Clean Up",
        description="Cleans up any unwanted data imported from the FBX file",
        default = False
        )

class JK_MMT_Export_Props(bpy.types.PropertyGroup):
    
    Meshes: BoolProperty(
        name="Export Meshes",
        description="Export selected meshes that have an armature modifier to the active rig",
        default = False
        )
        
    Batch_meshes: BoolProperty(
        name="Batch Export Meshes",
        description="Export each selected mesh to its own FBX. If false all selected meshes gets exported into one FBX",
        default = False
        )

    Animations: BoolProperty(
        name="Export Animations",
        description="Export the current action used by the active rig",
        default = False
        )
                
    Batch_animations: BoolProperty(
        name="Batch Export Animations",
        description="Export all actions the rig can use to their own FBXs. If false only export active action",
        default = False
        )
        
    Apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifers on export (except armature ones). If true prevents exporting shape keys",
        default = False
        )
        
    Startend_keys: BoolProperty(
        name="Start/End Keyframes",
        description="Force start and end keyframes on export",
        default = False
        )
    
    Show_advanced: BoolProperty(
        name="Advanced",
        description="Show advanced FBX export options. (Only edit these if you know what they do!)",
        default = False
        )
    
    Bake_deforms: BoolProperty(
        name="Bake Deforms",
        description="Bakes keyframes to deforming bones before exporting. Should fix fragile constraints such as Child Ofs and constraints that have targets outside of the armature. (WARNING: Work in progress)",
        default = False
        )
    
    Bake_step: IntProperty(
        name="Bake Step",
        description="How often to evaluate keyframes when baking using 'Bake Deforms' to pre-bake keyframes",
        default = 1
        )

    Add_leaf_bones: BoolProperty(
        name="Add Leaf Bones",
        description="Add Leaf Bones, Append a final bone to the end of each chain to specify last bone length (use this when you intend to edit the armature from exported data)",
        default = False
        )

    Primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        description="Primary Bone Axis",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='Y'
        )

    Secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        description="Secondary Bone Axis",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='X'
        )
    
    Axis_forward: EnumProperty(
        name="Forward",
        description="Forward",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='-Z'
        )
    
    Axis_up: EnumProperty(
        name="Up",
        description="Up",
        items=[('X', 'X', ""),
        ('-X', '-X', ""),
        ('Y', 'Y', ""),
        ('-Y', '-Y', ""),
        ('Z', 'Z', ""),
        ('-Z', '-Z', "")],
        default='Y'
        )

    Anim_step: FloatProperty(
        name="Sample Rate", 
        description="How often to evaluate animated values (in frames)", 
        default=1.0
        )
        
    Simplify_factor: FloatProperty(
        name="Simplify", 
        description="How much to simplify baked values (0.0 to disable, the higher the more simplified)", 
        default=0.0
        )
                
    Path_meshes: StringProperty(
        name="Mesh Export Folder",
        description="Export meshes to this folder",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )
    
    Path_animations: StringProperty(
        name="Animation Export Folder",
        description="Export animations to this folder",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
        )

    Use_most_host: BoolProperty(
        name="Use Most Host Export",
        description="Export uses Most Host LAs FBX export script for animations",
        default = True
        )

# all the main add-on options...
class JK_MMT_Base_Props(bpy.types.PropertyGroup):

    def Get_Stashed_Armatures(self, context):
        result = Object_Functions_Stash.Get_Stashed_Items(self.MMT_path, bpy.context.object, self.S_path, 'ARMATURE')
        global Get_Stashed_Armatures_Results_Reference
        Get_Stashed_Armatures_Results_Reference = result
        return result

    def Get_Stashed_Meshes(self, context):
        result = Object_Functions_Stash.Get_Stashed_Items(self.MMT_path, bpy.context.object, self.S_path, 'MESH')
        global Get_Stashed_Meshes_Results_Reference
        Get_Stashed_Meshes_Results_Reference = result
        return result

    def Get_Stashed_Materials(self, context):
        result = Object_Functions_Stash.Get_Stashed_Items(self.MMT_path, bpy.context.object, self.S_path, 'MATERIAL')
        global Get_Stashed_Materials_Results_Reference
        Get_Stashed_Materials_Results_Reference = result
        return result 
    
    MMT_path: StringProperty(
        name="",
        description="Where the addon scripts are",
        default=os.path.dirname(os.path.realpath(__file__)),
        maxlen=1024,
        )
    
    MMT_last_active: StringProperty(
        name="",
        description="Last active armature name",
        default="",
        maxlen=1024,
        )
        
    S_path: EnumProperty(
        name="Stash",
        description="Where you want to save and load mesh/materials to and from",
        items=Object_Functions_Stash.Get_Stashes,
        default=None
        )
    
    S_path_add: StringProperty(
        name="",
        description="Directory to create stash folder in. Must have write permissions",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )
    
    S_path_folder: StringProperty(
        name="Folder",
        description="The name used for a new stash folder. If folder already exists it gets added to stashes",
        default="UE4",
        maxlen=1024,
        )
    
    L_apply_scale_armatures: BoolProperty(
        name="Apply Scale",
        description="Automatically apply scaling given for the current scenes unit scale",
        default = True
        )
    
    A_overwrite_existing_meshes: BoolProperty(
        name="Overwrite Meshes",
        description="Overwrite existing meshes when saving them. Default mannequin meshes cannot be overwritten",
        default = False
        )
    
    L_apply_scale_meshes: BoolProperty(
        name="Apply Scale",
        description="Automatically apply scaling given for the current scenes unit scale",
        default = True
        )
     
    L_autoload_materials: BoolProperty(
        name="Auto-Load Materials",
        description="Automatically load any new materials when loading a mesh",
        default = True
        )
        
    L_active_parent: BoolProperty(
        name="Parent to active",
        description="Parent loaded mesh to active armature",
        default = True
        )
    
    A_autosave_materials: BoolProperty(
        name="Auto-Save Materials",
        description="Automatically save all materials used by selected meshes",
        default = True
        )
    
    A_overwrite_existing_materials: BoolProperty(
        name="Overwrite Materials",
        description="Overwrite existing materials when saving them. Default mannequin materials cannot be overwritten",
        default = False
        )
        
    A_pack_images: BoolProperty(
        name="Pack Images",
        description="Pack images into material files when saving them. If false any images use original filepaths",
        default = True
        )
    
    L_rigs: EnumProperty(
        name="Rig",
        description="Armature to load",
        items=Get_Stashed_Armatures,
        default=None
        )
        
    L_meshes: EnumProperty(
        name="Mesh",
        description="Mesh to load/remove",
        items=Get_Stashed_Meshes,
        default=None
        )
        
    L_materials: EnumProperty(
        name="Material",
        description="Material to load/remove",
        items=Get_Stashed_Materials,
        default=None
        )
    
    Export_active: StringProperty(
        name="Export Settings",
        description="The current export settings",
        default=""
        )
    
    Export_props: CollectionProperty(type=JK_MMT_Export_Props)
    
    Import_active: StringProperty(
        name="Import Settings",
        description="The current export settings",
        default=""
        )

    Import_props: CollectionProperty(type=JK_MMT_Import_Props)