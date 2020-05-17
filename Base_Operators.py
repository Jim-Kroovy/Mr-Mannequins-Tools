import bpy

from bpy. props import (StringProperty, FloatProperty, FloatVectorProperty, IntProperty, BoolProperty)

class JK_OT_Reset_Child_Ofs(bpy.types.Operator):
    """Resets all child ofs constraints after scaling"""
    bl_idname = "jk.reset_child_ofs"
    bl_label = "Reset Child Ofs"
    
    Armature: StringProperty(
        name="Armature",
        description="Name of the armature to fix child of constraints for",
        default="",
        maxlen=1024,
        )
    
    def execute(self, context):
        #scene = context.scene
        armature = bpy.context.object
        #bpy.ops.object.mode_set(mode='POSE')
        for p_bone in armature.pose.bones:
            for constraint in p_bone.constraints:
                if constraint.type == 'CHILD_OF':
                    bpy.context.active_object.data.bones.active = p_bone.bone
                    context_copy = bpy.context.copy()
                    context_copy["constraint"] = p_bone.constraints[constraint.name]
                    bpy.ops.constraint.childof_clear_inverse(context_copy, constraint=constraint.name, owner='BONE')
                    bpy.ops.constraint.childof_set_inverse(context_copy, constraint=constraint.name, owner='BONE')
        #bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

class JK_OT_Prep_Anim(bpy.types.Operator):
    """Prepares animation for export process"""
    bl_idname = "jk.prep_anim"
    bl_label = "Prepare Animation"
    
    Action: StringProperty(
        name="Action",
        description="Name of the action to prepare for export",
        default="",
        maxlen=1024,
        )

    def execute(self, context):
        action = bpy.data.actions[self.Action] #bpy.context.object.animation_data.action            
        # set the start and end frames...
        bpy.context.scene.frame_start = action.frame_range[0]
        bpy.context.scene.frame_end = action.frame_range[1]
        # hop into pose mode...
        bpy.ops.object.mode_set(mode='POSE')
        # reveal any hidden bones before selecting everything and clearing all transforms...
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
        # then back to object mode...
        bpy.ops.object.mode_set(mode='OBJECT')
         # set the current frame outside the frame range...(stops the current frame getting keyed as the rest pose on export)
        if (bpy.context.scene.frame_current > action.frame_range[0] and bpy.context.scene.frame_current < action.frame_range[1]) or (bpy.context.scene.frame_current == action.frame_range[0] or bpy.context.scene.frame_current == action.frame_range[1]):
            if action.frame_range[0] == 0:
                bpy.context.scene.frame_set(action.frame_range[1] + 1)
            else:
                bpy.context.scene.frame_set(action.frame_range[0] - 1)
        return {'FINISHED'} 

class JK_OT_Scale_Anim(bpy.types.Operator):
    """Scales location keyframes of an action"""
    bl_idname = "jk.scale_anim"
    bl_label = "Scale Animation"
    
    Action: StringProperty(
        name="Action",
        description="Name of the action to scale for export",
        default="",
        maxlen=1024,
        )
    
    Reverse: BoolProperty(
        name="Reverse",
        description="Scale animation to the armatures scale",
        default=False,
        )

    def execute(self, context):
        armature = bpy.context.object
        action = bpy.data.actions[self.Action]
        last_mode = bpy.context.object.mode
        print(last_mode)
        bpy.ops.object.mode_set(mode='POSE')
        if self.Reverse:
            scale = armature.scale
        else:
            # scale xyz by 100 multiplied by the unit scale...
            unit_scaling = 100 * bpy.context.scene.unit_settings.scale_length
            scale = (armature.scale[0] * unit_scaling, armature.scale[1] * unit_scaling, armature.scale[2] * unit_scaling)            
        # iterate through the location curves...
        for curve in [fcurve for fcurve in action.fcurves if fcurve.data_path.endswith('location')]:
            # and iterate through the keyframe values... print(curve.data_path, curve.array_index)
            for key in curve.keyframe_points:
                # should probably find a better method of getting bone name from path but curve.data_path[12:-11] works for now... (curve.data_path = "pose.bones[bone.name].location")
                if curve.data_path[12:-11] in armature.pose.bones:
                    # multiply keyframed location by scale per channel...
                    key.co[1] = key.co[1] * scale[curve.array_index]
                    key.handle_left[1] = key.handle_left[1] * scale[curve.array_index] 
                    key.handle_right[1] = key.handle_right[1] * scale[curve.array_index]
        bpy.ops.object.mode_set(mode=last_mode)
        return {'FINISHED'}

class JK_OT_Scale_Selected(bpy.types.Operator):
    """Scales all selected objects"""
    bl_idname = "jk.scale_selected"
    bl_label = "Scale Selected"

    Scaled: BoolProperty(
        name="Scaled",
        description="Stops the active object and it's children being scaled",
        default=False,
        )

    def execute(self, context):
        #scene = context.scene
        last_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        active = bpy.context.object
        objects = bpy.context.selected_objects
        # scale object xyz by 100 multiplied by the unit scale...
        unit_scaling = 100 * bpy.context.scene.unit_settings.scale_length
        parents = []
        for obj in objects:
            if obj.parent == None:
                parents.append(obj)  
        for parent in parents:
            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = parent
            parent.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            if self.Scaled:
                if parent != active:
                    parent.scale = [parent.scale[0] * unit_scaling, parent.scale[1] * unit_scaling, parent.scale[2] * unit_scaling]
            else:
                parent.scale = [parent.scale[0] * unit_scaling, parent.scale[1] * unit_scaling, parent.scale[2] * unit_scaling]
            bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.select_all(action='DESELECT')
        # return active object...
        bpy.context.view_layer.objects.active = active
        bpy.context.object.select_set(True)
        bpy.ops.object.mode_set(mode=last_mode)
        return {'FINISHED'}

# scales the time/length of the imported animation in the dopesheet...
class JK_OT_Scale_Keyframes(bpy.types.Operator):
    """Scales keyframes from one framerate to another"""
    bl_idname = "jk.scale_keyframes"
    bl_label = "Scale Keyframes"
    
    Start: FloatProperty(
        name="Start",
        description="Starting framerate",
        default=1.0,
        )

    End: FloatProperty(
        name="End",
        description="Desired framerate",
        default=1.0,
        )
    
    Offset: IntProperty(
        name="Offset",
        description="Offset the start of the animation by this much",
        default=1,
        )

    def execute(self, context):    
        # get reference to the current area type...
        last_area = bpy.context.area.type
        # switch to the dope sheet and turn of auto snapping...
        bpy.context.area.type = 'DOPESHEET_EDITOR'
        bpy.context.space_data.ui_mode = 'ACTION'
        bpy.context.space_data.auto_snap = 'NONE'
        # set the current frame to the start frame of the animation... (which is going to be the offset used by import)
        bpy.context.scene.frame_current = self.Offset
        # scale the keyframes by pre_fps divided by post fps so the animation has the right length for the desired pre fps... (when animation FBX is imported it seems to automatically set the render fps to what the the FBX was using)
        bpy.ops.transform.transform(mode='TIME_SCALE', value=(self.Start / self.End, 0, 0, 0), orient_axis='X', orient_type='VIEW', orient_matrix=((-1, -0, -0), (-0, -1, -0), (-0, -0, -1)), orient_matrix_type='VIEW', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        # return the area back to what it was...
        bpy.context.area.type = last_area
        # set the render fps to what it was before importing...
        bpy.context.scene.render.fps = self.Start
        return {'FINISHED'}
       