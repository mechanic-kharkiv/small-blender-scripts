"""
This will rename bones to alternative names and back to original with the stored name table.

Created on Mar 6, 2024

@author: (c) LIX A.S. Mechanic.Kharkiv
@last_edit: 2024-03-08
"""

bl_info = {
    "name": "Bone Renamer",
    "description": "It contains a bunch of commands to help batch-renaming the active armature's bones.",
    "location": "3D View > Pose Mode > Pose > Rename Bones... menu",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/bone_renamer",
    "doc_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/bone_renamer",
    "tracker_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/issues",
    "warning": "",
    "category": "Rigging",
    "author" : "(c) LIX A.S. Mechanic.Kharkiv"
}

import bpy
from collections import OrderedDict
import re

PROP_NAME_TABLE = "orig_alt_name_table"

REO_EXT_PAIR = re.compile(r"(?:^\s*)([\s\S]+?)(?:\t+)([\s\S]*?)$") # get two names separated with tab(s)

# Commands:
#     - Rename to alternative - Rename selected bones to their alternative names.
#     - Rename to original - Rename selected bones to their original names.
#     - Copy name table (All) - Copy entire name table to clipboard.
#     - Copy name table (Selected) - Copy name table for selected bones to clipboard.
#     - Paste name table (Replace) - Paste the name table from clipboard as new.
#     - Paste name table (Update) - Paste the name table from clipboard adding to existing.
#     - Paste as Regular Expressions - Create name table for selected bones from pasted (pattern, repl) pairs (tab-delimited) for re.sub().

def read_table(obj, selected_only):
    "returns dict : {orig : alt} from the property (unsorted), or None"
    res = obj.get(PROP_NAME_TABLE)
    if res is None:
        return None

    if not selected_only:
        return res.to_dict()

    else:
        table_mirror = {v : k for k,v in res.to_dict().items()}
        _ = {}
        for pb in obj.pose.bones:
            if not pb.bone.select:
                continue

            alt = res.get(pb.name)
            if alt:
                _[pb.name] = alt
            else:
                # maybe it's already alternative now
                orig = table_mirror.get(pb.name)
                if orig:
                    _[orig] = pb.name
                else:
                    # actually, no record, so return a stub
                    _[pb.name] = pb.name
        return _

def stub_table(obj, selected_only):
    "returns stub table for all or selected bones"
    res = {b.name : b.name for b in obj.pose.bones if not selected_only or b.bone.select}
    return res

def get_unique_name(new_name, existing):
    "returns new unique name for set of existing ones"
    _name = new_name
    while True:
        _name += "X"
        if _name not in existing:
            return _name

def parse_external(text, allow_empty_alt=False):
    """returns parsed dict from given external text data.
       if allow_empty_alt, then it will be returned as is to the line end.
    """
    res = OrderedDict()
    # split for lines and skip empties
    lines = [ln.replace("\r","") for ln in text.split("\n") if ln.strip() and "\t" in ln]
    for ln in lines:
        _ = REO_EXT_PAIR.search(ln)
        if _:
            _orig, _alt = _.group(1).strip(), _.group(2) if allow_empty_alt else _.group(2).strip()
            if not _orig or (not _alt and not allow_empty_alt):
                continue

            # both present
            res[_orig] = _alt
    return res


def show_name_table(obj, table, selected_only=False):
    print("%s %s bone name table of %s :" % ("-" * 10, "Selected" if selected_only else "All", obj.name))
    for k, v in sorted(table.items()):
        print("{}\t{}".format(k, v))

def copy_table(op, context, obj, selected_only):
    "copy the name table to clipboard."
    if not obj or obj.type != 'ARMATURE':
        op.report({'ERROR'}, "It works only with Armatures")
        return {'CANCELLED'}

    # read table from the property (if property does not exist, create a stub)
    table = read_table(obj, selected_only)
    if table is None:
        table = stub_table(obj, selected_only)
    # store to clipboard
    table = OrderedDict(sorted(table.items()))
    _ = tuple(("{}\t{}\n".format(k,v) for k,v in table.items()))
    context.window_manager.clipboard = "".join(_)
    show_name_table(obj, table, selected_only)
    return {'FINISHED'}

def paste_table(op, context, obj, replace=True):
    "paste the name table from the clipboard."
    if not obj or obj.type != 'ARMATURE':
        op.report({'ERROR'}, "It works only with Armatures")
        return {'CANCELLED'}

    # parse clipboard with format detection
    names_map = parse_external(context.window_manager.clipboard)
    stored = obj.get(PROP_NAME_TABLE)
    # store or update
    if replace or stored is None:
        # if replacing with no data, just kill the property
        if (not names_map or not len(names_map)) and stored is not None:
            stored.clear()
            del obj[PROP_NAME_TABLE]
        else:
            # store table
            if stored is None:
                obj[PROP_NAME_TABLE] = names_map
            else:
                stored.clear()
                stored.update(names_map)
    else:
        # update and stored
        stored.update(names_map)

    return {'FINISHED'}

def table_from_patterns(obj, pattern_text):
    """returns alt table from selected bones, and given RE patterns.
       patterns are given as tab-delimited pairs of (model, replace), one per line
    """
    #pattern_text =  r"(?i)(right_)(.*)" + "\t" + r"\2.R" + "\n" + r"(?i)(left_)(.*)" + "\t" + r"\2.L" + "\n"
    res = {}
    # get list of selected bone names
    origs = [b.name for b in obj.pose.bones if b.bone.select]
    if not len(origs):
        return res

    # parse patterns
    patterns = parse_external(pattern_text, allow_empty_alt=True)
    if not len(patterns):
        return res

    # apply patterns to each name, accumulating changes. register only changed
    for orig in origs:
        alt = orig
        for pattern, repl in patterns.items():
            alt = re.sub(pattern, repl, alt)
        if alt != orig:
            res[orig] = alt
    return res

def paste_as_patterns(op, context, obj):
    "Paste as Regular Expressions"
    if not obj or obj.type != 'ARMATURE':
        op.report({'ERROR'}, "It works only with Armatures")
        return {'CANCELLED'}

    table = table_from_patterns(obj, context.window_manager.clipboard)
    stored = obj.get(PROP_NAME_TABLE)
    # store table
    if stored is None:
        obj[PROP_NAME_TABLE] = table
    else:
        stored.clear()
        stored.update(table)
    show_name_table(obj, table, selected_only=True)
    return {'FINISHED'}

def rename_to(op, context, obj, to_alt):
    "rename selected bones to alternative names."
    if not obj or obj.type != 'ARMATURE':
        op.report({'ERROR'}, "It works only with Armatures")
        return {'CANCELLED'}

    print("Armature: %s" % obj.name)
    # get existing names
    existing = {pb.name for pb in obj.pose.bones}
    # get table for conversion
    table = read_table(obj, False)
    if not table:
        op.report({'ERROR'}, "Name table is not defined")
        return {'CANCELLED'}

    if not to_alt:
        table = {v: k for k,v in table.items()}

    # 1st pass
    # check if it's a valid operation (no doubles at the end)
    # first store unselected
    renamed = {pb.name for pb in obj.pose.bones if not pb.bone.select}
    # now add new renames
    for pb in obj.pose.bones:
        if not pb.bone.select:
            continue

        # find new name
        new_name = table.get(pb.name, pb.name)
        # check if it's already in the new names
        if new_name in renamed:
            op.report({'ERROR'}, "Cannot rename {} -> {}. Name exists.".format(pb.name, new_name))
            return {'CANCELLED'}

        renamed.add(new_name)

    # 2nd pass
    bones = [pb for pb in obj.pose.bones if pb.bone.select]
    temp_renamed = {}   # {actual_temp : old}

    for pb in bones:

        # if temp name, recall original
        old_orig_name = temp_renamed.get(pb.name)
        if not old_orig_name:
            old_orig_name = pb.name
        # find new name
        new_name = table.get(old_orig_name)
        if not new_name or old_orig_name == new_name:
            continue

        if new_name in existing:
            # if the name already exists
            # (temporarily exists, because we know the 1st pass was OK)
            # we rename conflicting to some temporary name (it will be renamed later)
            temp_name = get_unique_name(new_name, existing)
            temp_renamed[temp_name] = new_name
            pb1 = obj.pose.bones[new_name]
            print("  ahead rename %s -> %s" % (new_name, temp_name))
            pb1.name = temp_name
            existing.remove(new_name)
            existing.add(temp_name)

        # actually rename
        print("  rename %s -> %s" % (pb.name, new_name))
        existing.remove(pb.name)
        pb.name = new_name
        existing.add(new_name)

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
class BoneRenamerRenameToAlt(bpy.types.Operator):
    """Rename selected bones to their alternative names."""
    bl_idname = "armature.bone_renamer_rename_alt"
    bl_label = "Rename to alternative"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE'
                and context.active_object.get(PROP_NAME_TABLE))

    def execute(self, context):
        return rename_to(self, context, context.active_object, True)

@make_annotations
class BoneRenamerRenameToOrig(bpy.types.Operator):
    """Rename selected bones to their original names."""
    bl_idname = "armature.bone_renamer_rename_orig"
    bl_label = "Rename to original"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE'
                and context.active_object.get(PROP_NAME_TABLE))

    def execute(self, context):
        return rename_to(self, context, context.active_object, False)

@make_annotations
class BoneRenamerCopyTableAll(bpy.types.Operator):
    """Copy entire name table to clipboard."""
    bl_idname = "armature.bone_renamer_copy_table_all"
    bl_label = "Copy name table (All)"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE')

    def execute(self, context):
        return copy_table(self, context, context.active_object, False)

@make_annotations
class BoneRenamerCopyTableSel(bpy.types.Operator):
    """Copy name table for selected bones to clipboard."""
    bl_idname = "armature.bone_renamer_copy_table_sel"
    bl_label = "Copy name table (Selected)"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE')

    def execute(self, context):
        return copy_table(self, context, context.active_object, True)

@make_annotations
class BoneRenamerPasteTableNew(bpy.types.Operator):
    """Paste the name table from clipboard as new."""
    bl_idname = "armature.bone_renamer_paste_replace"
    bl_label = "Paste name table (Replace)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE')

    def execute(self, context):
        return paste_table(self, context, context.active_object, replace=True)

@make_annotations
class BoneRenamerPasteTableUpdate(bpy.types.Operator):
    """Paste the name table from clipboard adding to existing."""
    bl_idname = "armature.bone_renamer_paste_update"
    bl_label = "Paste name table (Update)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE'
                and context.active_object.get(PROP_NAME_TABLE) and len(context.active_object[PROP_NAME_TABLE]))

    def execute(self, context):
        return paste_table(self, context, context.active_object, replace=False)

@make_annotations
class BoneRenamerPasteTablePatterns(bpy.types.Operator):
    """Create name table for selected bones from pasted (pattern, repl) pairs (tab-delimited) for re.sub()."""
    bl_idname = "armature.bone_renamer_paste_patterns"
    bl_label = "Paste as Regular Expressions"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'ARMATURE')

    def execute(self, context):
        return paste_as_patterns(self, context, context.active_object)



class RenameBonesMenu(bpy.types.Menu):
    bl_label = "Rename Bones..."
    bl_idname = "VIEW3D_MT_pose_rename_bones"

    def draw(self, context):
        layout = self.layout

        layout.operator(BoneRenamerRenameToAlt.bl_idname)
        layout.operator(BoneRenamerRenameToOrig.bl_idname)
        layout.separator()
        layout.operator(BoneRenamerCopyTableAll.bl_idname, icon='COPYDOWN')
        layout.operator(BoneRenamerCopyTableSel.bl_idname, icon='COPYDOWN')
        layout.separator()
        layout.operator(BoneRenamerPasteTableNew.bl_idname, icon='PASTEDOWN')
        layout.operator(BoneRenamerPasteTableUpdate.bl_idname, icon='PASTEDOWN')
        layout.separator()
        layout.operator(BoneRenamerPasteTablePatterns.bl_idname, icon='PASTEDOWN')


def draw_menu(self, context):
    self.layout.menu(RenameBonesMenu.bl_idname)


classes = [
        BoneRenamerRenameToAlt,
        BoneRenamerRenameToOrig,
        BoneRenamerCopyTableAll,
        BoneRenamerCopyTableSel,
        BoneRenamerPasteTableNew,
        BoneRenamerPasteTableUpdate,
        BoneRenamerPasteTablePatterns,
        RenameBonesMenu,
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_pose.append(draw_menu)

def unregister():
    bpy.types.VIEW3D_MT_pose.remove(draw_menu)
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
