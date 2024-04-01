# -*- coding: 'utf-8' -*-
'''
This imports all fbx files into the current scene from the given directory.
Each imported object receives a property 'fbxpath' with original source file full path.

The embedded 'import_scene.fbx' since 4.20.2 (blender 2.81.6) (?) already supports multiple files,
but with no tag adding. So, let it be. :-)

Created on Jan 28, 2024

@author: (c) LIX A.S. Mechanic.Kharkiv
@last_edit: 2024-02-02
'''
# DONE: sort out the version tag usage to keep it compatible with 2.7x and newer
#   we just use 2.80: older complain, but allow it; the newer just accept.

# Actually it works OK from version 2.76. Maybe even older, just give it a try.

bl_info = {
    "name": "FBX batch import with preset (*.fbx)",
    "author": "(c) LIX A.S. Mechanic.Kharkiv",
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Import > FBX batch import",
    "description": "Import all fbx files from directory with named preset.",
    "support": 'COMMUNITY',
    "category": "Import-Export",
}

import bpy

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

import sys, os
#import time

from . import presets
if bpy.app.version < (2,80,0):
    from .classes27 import *
else:
    from .classes28 import *

FBXPATH_TAG_NAME = "fbxpath"

class DummyFile(object):
    """ NUL device emulator. """
    def write(self, x): pass

def import_fbx(operator, path, preset_dict={}):
    mess = "\nImporting {}".format(path)
    print(mess)
    operator.report({'DEBUG'}, mess)
    save_stdout = sys.stdout
    try:
        sys.stdout = DummyFile() # suppress its output
        bpy.ops.import_scene.fbx(filepath=path, **preset_dict)
    finally:
        sys.stdout = save_stdout


def do_batch_import(operator, context, src_dir, fbx_import_preset_name="", use_tags=True):
    mess = "Started batch fbx import from {} with preset [{}]".format(
        src_dir, fbx_import_preset_name)
    print("\n" + mess)
    operator.report({'INFO'}, mess)
    # check parameters
    if os.path.isfile(src_dir):
        src_dir, _ = os.path.split(src_dir)
    if not os.path.isdir(src_dir):
        operator.report({'ERROR'}, "{} is not a directory.".format(src_dir))
        return {'CANCELLED'}

    # obtain fbx_filenames to process
    # if a file or multiple files selected, use them, else entire directory
    if operator.files and len(operator.files) >= 1 and operator.files[0].name:
        fbx_filenames = [file.name for file in operator.files]
    else:
        fbx_filenames = [fname for fname in os.listdir(src_dir) if fname.lower().endswith(".fbx")]

    # read importer preset
    preset_dict = presets.read_operator_preset("import_scene.fbx", fbx_import_preset_name, ("filter_glob", "directory", "ui_tab", "filepath", "files"))

    # store current objects_list
    objects_list = [obj for obj in context.scene.objects]
    actions_list = [obj for obj in bpy.data.actions]
    cnt_meshes = cnt_armatures = cnt_actions = cnt_files = 0

    error_messages = []

    for file_name in fbx_filenames:
        # import the file
        fbx_path = os.path.join(src_dir, file_name)
        if not os.path.isfile(fbx_path):
            mess = "{} is not a file. Skipped.".format(file_name)
            print("ERROR: " + mess)
            operator.report({'ERROR'}, mess)
            continue

        try:
            import_fbx(operator, fbx_path, preset_dict)
        except Exception as e:
            mess = "file {}: {}".format(file_name, e)
            print("ERROR: " + mess)
            operator.report({'ERROR'}, mess)
            error_messages.append(mess)
            continue

        cnt_files += 1
        # find all new_objects added with last import
        new_objects = [obj for obj in context.scene.objects if obj not in objects_list]
        new_actions = [obj for obj in bpy.data.actions if obj not in actions_list]
        actions_list = [obj for obj in bpy.data.actions]
        cnt_actions += len(new_actions)

        if len(new_objects):
            mess = "imported objects: " + ", ".join((obj.name for obj in new_objects))
            print(mess)
            operator.report({'DEBUG'}, mess)
        if len(new_actions):
            mess = "imported actions: " + ", ".join((obj.name for obj in new_actions))
            print(mess)
            operator.report({'DEBUG'}, mess)

        for new_object in new_objects:
            if (use_tags):
                # add a custom property with source path
                new_object[FBXPATH_TAG_NAME] = fbx_path
            # register the new object
            objects_list.append(new_object)
            if new_object.type == 'MESH':
                cnt_meshes += 1
            elif new_object.type == 'ARMATURE':
                cnt_armatures += 1

    mess = "Finished. Imported meshes [{}]; armatures [{}]; actions [{}]; from {} files.".format(
                    cnt_meshes, cnt_armatures, cnt_actions, cnt_files
                    )
    print(mess)
    operator.report({'INFO'}, mess)
    if len(error_messages):
        operator.report({'WARNING'}, "There was some files ({}) with errors. See console for details.".format(len(error_messages)))
        print("files with ERRORS:")
        for i, mess in enumerate(error_messages):
            print(i+1, mess)

    return {'FINISHED'}


# ========= UI stuff ============

class FbxBatchImport(Operator, FbxImportHelper, BatchImportOpProps):
    """Import all fbx files from directory with named preset."""
    bl_idname = "import_scene_batch.fbx"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "FBX batch import (directory, preset)"

    # ImportHelper mixin class uses this
    filename_ext = ".fbx"

    def execute(self, context):
        _preset =  self.preset_name if self.preset_name != presets.NO_PRESET else ""
        return do_batch_import(self, context, os.path.dirname(self.filepath), _preset, self.add_tags)

    def invoke(self, context, event):
        presets.rescan_preset_names("import_scene.fbx")
        return FbxImportHelper.invoke(self, context, event)

def menu_func_import(self, context):
    self.layout.operator(FbxBatchImport.bl_idname, text=FbxBatchImport.bl_label)

def register():
    bpy.utils.register_class(FbxBatchImport)
    if bpy.app.version < (2,80,0):
        bpy.types.INFO_MT_file_import.append(menu_func_import)
    else:
        bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(FbxBatchImport)
    if bpy.app.version < (2,80,0):
        bpy.types.INFO_MT_file_import.remove(menu_func_import)
    else:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
    # test call
    bpy.ops.import_scene_batch.fbx('INVOKE_DEFAULT')
