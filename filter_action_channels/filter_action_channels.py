# -*- coding: utf-8 -*-
"""
The script will remove unnecessary animation data from actions of selected Armatures.

- It removes all channels of absent bones (could be dangerous, if the action is used on
    another object, where they could exist);
    (Using fcurve.is_valid is not reliable, so we just look for the bone by name);
- It removes location channels if the bone is connected to its parent, hence cannot move;
    (also could be dangerous, if the action is intended for use on other objects);
- It kills all keyframes but the first, if their values don't change at all (safe);

@author: (c) LVII-LIX A.S. Mechanic.Kharkiv
@last_edit: 2024-03-12
"""

bl_info = {
    "name": "Filter action channels operator",
    "description": "Operator to filter redundant animation data in actions to compact them.",
    "location": "3D View > Object Mode > Object > Animation menu",
    "version": (1, 1, 1),
    "blender": (2, 80, 0),
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/filter_action_channels",
    "doc_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/filter_action_channels",
    "tracker_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/issues",
    "warning": "",
    "category": "Animation",
    "author" : "(c) LVII-LIX A.S. Mechanic.Kharkiv"
}

import bpy
import re
from _collections import defaultdict
from bpy.props import BoolProperty

EPSILON = 0.000001

# finds a bone name and channel name in the data path to groups 1, 2
REO_PATT_PARSE_DATA_PATH = re.compile(r'(?:pose\.bones\[")(.+?)(?:"]\.)(.+)')


def value_changes(fcurve):
    """ returns true if fcurve value changes even once. """
    if len(fcurve.keyframe_points) < 2:
        return False

    _old = fcurve.keyframe_points[0].co[1]
    return any(map(lambda kf : abs(_old - kf.co[1]) >= EPSILON, fcurve.keyframe_points))

def fcurve_is_sorted(fcurve):
    """ returns True if keyframes are sorted by time. """
    if len(fcurve.keyframe_points) < 2:
        return True

    keys = fcurve.keyframe_points
    v = keys[0].co[0]
    for key in keys:
        if key.co[0] < v:
            return False

        v = key.co[0]
    return True

def get_object_actions(obj, also_nla):
    "returns set of actions from the object."
    res = set()
    if obj.animation_data:
        if obj.animation_data.action:
            res.add(obj.animation_data.action)
        if also_nla:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action:
                        res.add(strip.action)
    return res

def get_existing_bones(obj):
    """ returns set of existing bone names of given armature object"""
    return {pb.name for pb in obj.pose.bones}

def get_disconnected_bones(obj):
    """ returns set of names of bones which can move"""
    return {pb.name for pb in obj.pose.bones if pb.parent is None or not pb.bone.use_connect}


def do_filter_channels(op, context):

    if not (op.filter_absent_bones or op.filter_connected_loc or op.filter_constant_keys):
        op.report({'WARNING'}, "No filter type selected!")
        return {'CANCELLED'}

    sel_objects = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']

    # get actions we are going to process
    actions_to_filter = set()
    for obj in sel_objects:
        actions_to_filter.update(get_object_actions(obj, op.also_nla))

    op.total_actions += len(actions_to_filter)
    if len(actions_to_filter) == 0:
        op.report({'WARNING'}, "No action to filter found!")
        return {'CANCELLED'}

    # actions could be shared between objects, so we try to combine bone names from
    # all referencing rigs for an action

    # look for objects to extract references
    if op.global_search:
        # look everywhere
        ref_look_objects = {obj for obj in bpy.data.objects if obj.type == 'ARMATURE'}
    else:
        # use only selection
        ref_look_objects = set(sel_objects)

    # now we search references to these actios in ref_look_objects
    action_refs = defaultdict(set)
    for obj in ref_look_objects:
        for action in get_object_actions(obj, True):
            if action in actions_to_filter:
                action_refs[action].add(obj)
    # now we have all needed actions with refs in action_refs
    del actions_to_filter

    for action, ref_objects in action_refs.items():

        # process single action
        if op.verbose:
            print()
        print("filtering action {} @ [{}]".format(action.name, ", ".join((o.name for o in ref_objects))))

        if op.filter_absent_bones:
            # find existing bones
            existing_bones = set()
            for _obj in ref_objects:
                existing_bones.update(get_existing_bones(_obj))

        if (op.filter_connected_loc):
            # find bones which can move
            disconnected_bones = set()
            for _obj in ref_objects:
                disconnected_bones.update(get_disconnected_bones(_obj))

        fcurves = action.fcurves
        fcurves_to_kill = []
        op.total_fcurves += len(fcurves)

        # analyze curves to be killed or filtered
        for fc in fcurves:

            op.total_keyframes += len(fc.keyframe_points)

            is_bone_fcurve = False
            if (op.filter_absent_bones or op.filter_connected_loc):
                # it's about bones, so process only bone fcurves
                _res = REO_PATT_PARSE_DATA_PATH.search(fc.data_path)
                if _res:
                    is_bone_fcurve = True
                    _bone_name, _channel = _res.group(1),_res.group(2)

            if (is_bone_fcurve and op.filter_absent_bones):
                # check if the bone exists
                if _bone_name not in existing_bones:
                    fcurves_to_kill.append(fc)
                    if op.verbose:
                        print("to kill {} [{}] absent bone".format(fc.data_path, fc.array_index))
                    op.killed_fcurves += 1
                    op.killed_keyframes += len(fc.keyframe_points)
                    continue

            if (is_bone_fcurve and op.filter_connected_loc):
                # is it loc of connected bone?
                if _channel.startswith("loc"):
                    if _bone_name not in disconnected_bones:
                        fcurves_to_kill.append(fc)
                        if op.verbose:
                            print("to kill {} [{}] connected".format(fc.data_path, fc.array_index))
                        op.killed_fcurves += 1
                        op.killed_keyframes += len(fc.keyframe_points)
                        continue

            if (op.filter_constant_keys):
                # does it need to be truncated to the first key only?
                if len(fc.keyframe_points) > 1 and not value_changes(fc):
                    if op.verbose:
                        print("to truncate {} [{}] constant".format(fc.data_path, fc.array_index))
                    op.killed_keyframes += len(fc.keyframe_points) - 1
                    if not op.dry_run:
                        # actual truncate
                        # paranoid?
                        if not fcurve_is_sorted(fc):
                            fc.update()
                        kfp = fc.keyframe_points
                        i = len(kfp)
                        while (i > 1):
                            i -= 1
                            kfp.remove(kfp[i], fast=True)
                        fc.update()

        # kill fcurves
        if (not op.dry_run and len(fcurves_to_kill) > 0):
            while(fcurves_to_kill):
                fc = fcurves_to_kill.pop()
                fcurves.remove(fc)

    return {'FINISHED'}


# this was taken from https://github.com/CGCookie/blender-addon-updater
def make_annotations(cls):
    """Add annotation attribute to fields to avoid Blender 2.8+ warnings"""
    if not hasattr(bpy.app, "version") or bpy.app.version < (2, 80):
        return cls
    if bpy.app.version < (2, 93, 0):
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, tuple)}
    else:
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, bpy.props._PropertyDeferred)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls

@make_annotations
class FilterActionChannels(bpy.types.Operator):
    """Removes unnecessary keyframes and fcurves from actions of the selected armatures."""
    bl_idname = "object.filter_action_channels"
    bl_label = "Filter action(s) channels"
    bl_options = {'REGISTER', 'UNDO'}

    filter_constant_keys = BoolProperty(
            name="Filter constant keys",
            description="Remove all keyframe except the first if they don't change the channel's value (safe).",
            default=True
        )

    filter_absent_bones = BoolProperty(
            name="Filter absent bones",
            description="Remove channels with no corresponding pose bones in the object (could be dangerous if the action is shared with other objects).",
            default=True
        )

    filter_connected_loc = BoolProperty(
            name="Filter connected Loc",
            description="Remove location channels for connected bones (could be dangerous if the action is shared with other objects).",
            default=True
        )

    also_nla = BoolProperty(
            name="Also filter NLA actions",
            description="Process also all actions mentioned in NLA strips.",
            default=True
        )

    global_search = BoolProperty(
            name="Global references search",
            description="Look for referencing armatures beyond the selection.",
            default=True
        )

    dry_run = BoolProperty(
            name="Dry run",
            description="No actual removing of anything, but showing statistics.",
            default=False
        )

    verbose = BoolProperty(
            name="Verbose",
            description="Show detailed log in the console.",
            default=False
        )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0 and any(map(lambda obj: obj.type == 'ARMATURE', context.selected_objects))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # statistics
        self.total_actions = 0
        self.total_fcurves = 0
        self.total_keyframes = 0
        self.killed_fcurves = 0
        self.killed_keyframes = 0

        op_res = do_filter_channels(self, context)

        if 'FINISHED' in op_res:
            s = "{} of {} keyframes ({:.2f}%), {} of {} fcurves {} killed in {} actions".format(
                self.killed_keyframes, self.total_keyframes,
                (0  if self.total_keyframes == 0 else self.killed_keyframes / self.total_keyframes * 100),
                self.killed_fcurves, self.total_fcurves,
                "gotta be" if self.dry_run else "were",
                self.total_actions
                )
            self.report({'INFO'}, s)

        return op_res


def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT';
    self.layout.operator(
        FilterActionChannels.bl_idname)

def register():
    bpy.utils.register_class(FilterActionChannels)
    bpy.types.VIEW3D_MT_object_animation.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object_animation.remove(menu_func)
    bpy.utils.unregister_class(FilterActionChannels)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()

    # test call
    #bpy.ops.object.filter_action_channels(dry_run=True, verbose=True)
