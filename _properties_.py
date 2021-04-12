import bpy
import os
from bpy.props import (BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)
    
# Blenders FBX export/import settings that don't need to be anything specfic...
class JK_PG_MMT_FBX(bpy.types.PropertyGroup):

    primary_bone_axis: EnumProperty(name="Primary Bone Axis", description="Primary Bone Axis",
        items=[('X', 'X', ""),('-X', '-X', ""),('Y', 'Y', ""),
            ('-Y', '-Y', ""),('Z', 'Z', ""),('-Z', '-Z', "")],
        default='Y', options=set())

    secondary_bone_axis: EnumProperty(name="Secondary Bone Axis", description="Secondary Bone Axis",
        items=[('X', 'X', ""),('-X', '-X', ""),('Y', 'Y', ""),
            ('-Y', '-Y', ""),('Z', 'Z', ""),('-Z', '-Z', "")],
        default='X', options=set())
    
    axis_forward: EnumProperty(name="Forward", description="Forward",
        items=[('X', 'X', ""),('-X', '-X', ""),('Y', 'Y', ""),
            ('-Y', '-Y', ""),('Z', 'Z', ""),('-Z', '-Z', "")],
        default='-Z', options=set())

    axis_up: EnumProperty(name="Up",description="Up",
        items=[('X', 'X', ""),('-X', '-X', ""),('Y', 'Y', ""),
            ('-Y', '-Y', ""),('Z', 'Z', ""),('-Z', '-Z', "")],
        default='Y', options=set())

    # only used on on export...

    add_leaf_bones: BoolProperty(name="Add Leaf Bones", description="Add Leaf Bones, Append a final bone to the end of each chain to specify last bone length (use this when you intend to edit the armature from exported data)",
        default=False, options=set())
    
    anim_step: FloatProperty(name="Sample Rate", description="How often to evaluate animated values (in frames)", 
        default=1.0, min=0.1, max=10.0, step=0.1, precision=2, options=set())
        
    simplify_factor: FloatProperty(name="Simplify", description="How much to simplify baked values (0.0 to disable, the higher the more simplified)", 
        default=0.0, min=0.0, max=10.0, step=0.1, precision=2, options=set())

    use_nla: BoolProperty(name="Use NLA Strips", description="Whether we want to export each NLA strip as an action", 
        default=False, options=set())

    all_actions: BoolProperty(name="All Actions", description="Whether we want to export all actions compatible with the active armature", 
        default=False, options=set())

    apply_modifiers: BoolProperty(name="Apply Modifiers", description="Apply modifers on export (except armature ones). If true prevents exporting shape keys",
        default=True, options=set())
        
    startend_keys: BoolProperty(name="Start/End Keyframes", description="Force start and end keyframes on export",
        default=True, options=set())

    # only used on import...
    
    manual_orient: BoolProperty(name="Manual Orientation", description="Specify orientation and scale, instead of using embedded data in FBX file",
        default=False, options=set())
    
    user_props: BoolProperty(name="Import User Properties", description="Import user properties as custom properties. WARNING! Setting True might cause import errors with some properties found in .FBXs",
        default=False, options=set())
        
    anim_offset: FloatProperty(name="Frame Offset", description="Offset to apply to animation during import, in frames", 
        default=1.0, step=0.1, precision=2, options=set())

    ignore_leaf_bones: BoolProperty(name="Ignore Leaf Bones", description="Ignore the last bone at the end of each chain (used to mark the length of the previous bone)",
        default=False, options=set())

# Mr Mannequins export settings...
class JK_PG_MMT_Export(bpy.types.PropertyGroup):
    
    meshes: BoolProperty(name="Export Meshes", description="Export selected meshes",
        default=False, options=set())
        
    batch_meshes: BoolProperty(name="Batch Meshes", description="Export each selected mesh to its own FBX or export all meshes to one FBX", 
        default=False, options=set())
        
    path_meshes: StringProperty(name="Mesh Export Folder", description="Export meshes to this folder", 
        default="//", maxlen=1024, options=set(), subtype='DIR_PATH')

    prefix_skeletal: StringProperty(name="Skeletal Prefix", description="Prefix of exported skeletal mesh FBX files", 
        default="")

    prefix_static: StringProperty(name="Static Prefix", description="Prefix of exported static mesh FBX files", 
        default="")

    path_actions: StringProperty(name="Action Export Folder", description="Export animations to this folder", 
        default="//", maxlen=1024, options=set(), subtype='DIR_PATH')

    prefix_action: StringProperty(name="Action Prefix", description="Prefix of exported action FBX files", 
        default="")

    actions: BoolProperty(name="Export Actions", description="Export selected actions",
        default=False, options=set())

    action_armature: StringProperty(name="Armature", description="Armature to export with actions",
        default="", maxlen=1024, options=set(), subtype='NONE')
    
    def update_batch_actions(self, context):
        # if we are batch exporting actions...
        if self.batch_actions:
            # we can't use NLA strips or all actions...
            self.fbx_props.use_nla, self.fbx_props.all_actions = False, False

    batch_actions: BoolProperty(name="Batch Actions", description="Export each action to its own FBX or export all actions to one FBX", 
        default=False, options=set(), update=update_batch_actions)
        
    show_advanced: BoolProperty(name="Show Advanced Settings", description="Show advanced FBX export options. (Only edit these if you know what they do!)", 
        default=False, options=set())

    send_to_unreal: BoolProperty(name="Use 'Send to Unreal'", description="(Coming Soon!) Use Epics own Send2Unreal export operator if the add-on is installed. (Go give James Baber some love for all dat Github support! And don't be raising dumb af issues on dat repo lol)",
        default=False, options=set())

    from_selection: BoolProperty(name="From Selection", description="Use Send To Unreal with selected objects instead of their mandatory collections",
        default=False, options=set())

    mute_nla: BoolProperty(name="Mute NLA Strips", description="If we want to mute the NLA strips to stop them influencing actions", 
        default=False, options=set())
        
    export_scale: FloatProperty(name="Export Scale", description="Scaling required on Export. (This should be 100 for UE4)", 
        default=100.0, options=set()) #step=0.1, precision=3
        
    apply_location: BoolProperty(name="Apply Location", description="Applies object locations on export. (Used to set the origin, if false location gets cleared)",
        default=False, options=set())

    apply_rotation: BoolProperty(name="Apply Rotation", description="Applies object rotations on export. (Used to set the direction, if false rotation gets cleared)",
        default=False, options=set())

    combine_deforms: BoolProperty(name="Combine Deforms", description="Export control and deform bones in one armature.",
        default=False, options=set())
    
    fbx_props: PointerProperty(type=JK_PG_MMT_FBX, options=set())

# Mr Mannequins import settings...    
class JK_PG_MMT_Import(bpy.types.PropertyGroup):
    
    meshes: BoolProperty(name="Import Meshes", description="Import meshes",
        default=False, options=set())

    mesh_fbx: StringProperty(name="FBX", description="Import meshes from this FBX", 
        default="//", maxlen=1024, options=set(), subtype='FILE_PATH')

    path_meshes: StringProperty(name="Mesh Folder", description="Directory to import meshes from",
        default="//", maxlen=1024, options=set(), subtype='DIR_PATH')

    batch_meshes: BoolProperty(name="Batch Meshes", description="Import all meshes from mesh import folder",
        default=False, options=set())
    
    actions: BoolProperty(name="Import Actions", description="Import actions", 
        default=False, options=set())

    action_fbx: StringProperty(name="FBX", description="Import actions from this FBX", 
        default="//", maxlen=1024, options=set(), subtype='FILE_PATH')
    
    batch_actions: BoolProperty(name="Batch Actions", description="Import actions from all FBXs in the action import folder",
        default=False, options=set())

    path_actions: StringProperty(name="Action Folder", description="Directory to import animations from",
        default="//", maxlen=1024, options=set(), subtype='DIR_PATH')

    scale_keyframes: BoolProperty(name="Scale To Framerate", description="Scale action length to current scene framerate",
        default=True, options=set())
    
    show_advanced: BoolProperty(name="Show Advanced Settings", description="Show advanced FBX import options. (Only edit these if you know what they do!)",
        default=False, options=set())

    apply_location: BoolProperty(name="Apply Location", description="Applies location objects get imported with",
        default=True, options=set())

    apply_rotation: BoolProperty(name="Apply Rotation", description="Applies rotation objects get imported with",
        default=True, options=set())

    apply_scale: BoolProperty(name="Apply Scale", description="Applies scale objects and actions get imported with",
        default=True, options=set())

    add_root: BoolProperty(name="Add Root Bones", description="Adds root bones to imported armatures at the correct origin and rotation (if importing actions this also converts root motion from the object to the root bone)",
        default=True, options=set())

    clean_up: BoolProperty(name="Clean Up", description="Cleans up any unwanted data imported from the FBX file",
        default=True, options=set())

    bake_to_active: BoolProperty(name="Bake To Active", description="Attempt to bake actions to the active armatures control bones",
        default=True, options=set())

    deform_to_active: BoolProperty(name="Deform To Active", description="(Coming Soon!) Attempt to deform meshes to fit the active armatures deform bones",
        default=True, options=set())
        
    fbx_props: PointerProperty(type=JK_PG_MMT_FBX, options=set())

    use_default_retargeting_translation: BoolProperty(name="Default Retargeting Translation", description="Only root, pelvis and default ik targets use location keyframess. This is just a temporary fix for importing mannequin animations that have odd location keyframes. I have every intention of adding a per bone option for this... likely in the next update",
        default=False, options=set())

# object specific properties i need to export correctly...
class JK_PG_MMT_Object(bpy.types.PropertyGroup):

    def get_flavour(self):
        flavour = 'NONE'
        if self.id_data.type == 'ARMATURE':
            flavour = 'ACTION'
        elif self.id_data.type == 'MESH':
            if self.id_data.find_armature():
                flavour = 'SKELETAL'
            else:
                flavour = 'STATIC'
        return flavour

    def update_flavour(self, context):
        # if this object is an armature...
        if self.id_data.type == 'ARMATURE':
            # it can only be exported as an action object...
            self.flavour = 'ACTION'
        # else if the flavour is skeletal...
        elif self.flavour == 'SKELETAL':
            # find it's armature...
            self.armature = self.id_data.find_armature()
            # if we didn't find an armature...
            if not self.armature:
                # then the mesh has to be static...
                self.flavour = 'STATIC'
        # else if the flavour is being set to static...
        elif self.flavour == 'STATIC':
            # make sure not to leave a armature reference...
            self.armature = None
        # else if the flavour is being set to action...
        elif self.flavour == 'ACTION':
            # clear all references...
            self.armature, self.collision = None, None
            self.detail_levels.clear()

    flavour: EnumProperty(name="Export Type",description="The type of FBX export this object should use",
        items=[('NONE', 'None', "Export not currently supported for this object type"),
            ('SKELETAL', 'Skeletal Mesh', "A skeletal mesh with an armature"),
            ('STATIC', 'Static Mesh', "A static mesh"),
            ('ACTION', 'Action Armature', "An armature with animations")],
        default='NONE', update=update_flavour)

    is_template: BoolProperty(name="Is template", description="Is this object part of a template that comes with the add-on",
        default=False, options=set())

    use_export: BoolProperty(name="Export", description="Should this object be exported",
        default=True, options=set())

    #def update_is_exporting(self, context):
        #if self.id_data.data.jk_adc.is_deformer and self.is_exporting:
            #controller = self.id_data.data.jk_adc.armature
            #action = self.id_data.animation_data.action
            #print(self.id_data, action)
            #for pb in controller.pose.bones:
                #pb.location, pb.scale, pb.rotation_euler = [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]
                #pb.rotation_quaternion, pb.rotation_axis_angle = [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]
            #if action:
                #bpy.context.scene.frame_start, bpy.context.scene.frame_end = int(round(action.frame_range[0], 0)), int(round(action.frame_range[1], 0))
            #controller.animation_data.action = action
        #self.last_exporting = self.is_exporting

    #last_exporting: BoolProperty(name="Last Exporting", description="Was this object being exported...",
        #default=False, options=set())

    #is_exporting: BoolProperty(name="Exporting", description="Is this object being exported...",
        #default=False, update=update_is_exporting)

    #detail_levels: CollectionProperty(type=bpy.types.Object, description="The levels of detail for this mesh. (only used by static and skeletal mesh objects)")

    #collision: PointerProperty(type=bpy.types.Object, description="The collision object for this mesh. (only used by static mesh objects)")

    #armature: PointerProperty(type=bpy.types.Object, description="The armature used by this skeletal mesh. (only used by skeletal mesh objects)")

    #prefix: StringProperty(name="Object Prefix", description="Prefix of the object FBX files", 
        #default="")

    #def get_actions(self):
        #actions = []
        #if self.flavour == 'ACTION':
           #actions = [act for act in bpy.data.actions if _functions_.get_armature_uses_action(self.id_data, act)]
        #return actions
        # clear and fill the actions collection...
        #self.actions.clear()
        #for action in actions:
            #self.actions.add(action)

    #actions: CollectionProperty(type=bpy.types.Action, description="The actions that can be used by this armature. (Only used by action armature objects)")

    #export_settings: PointerProperty(type=JK_PG_MMT_Export, description="The FBX export settings of this object")

# all the main add-on options...
#class JK_PG_MMT_Scene(bpy.types.PropertyGroup):
    
    #resources: StringProperty(name="Resources", description="Where the templates are",
        #default=os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), maxlen=1024, options=set(), subtype='DIR_PATH')

    #export_active: StringProperty(name="Export Settings", description="The current export settings",
        #default="", maxlen=1024, options=set(), subtype='NONE')
    
    #export_default: PointerProperty(type=JK_PG_MMT_Export, options=set())
    
    #export_props: CollectionProperty(type=JK_PG_MMT_Export, options=set())
    
    #import_active: StringProperty(name="Import Settings", description="The current export settings", 
        #default="", maxlen=1024, options=set(), subtype='NONE')

    #import_default: PointerProperty(type=JK_PG_MMT_Import, options=set())

    #import_props: CollectionProperty(type=JK_PG_MMT_Import, options=set())