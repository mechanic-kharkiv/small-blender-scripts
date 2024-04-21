# -*- coding: 'utf-8' -*-
'''
This patches standard fbx importer in memory to allow it to import multiple selected fbx files into
the current scene from the given directory.
Optionally each imported object receives a property 'fbxpath' with the original source file full path.
It tags objects, armature and mesh data blocks, and actions.

The embedded 'io_scene_fbx' since 4.20.2 (blender 2.81.6) (?) already supports multiple files,
but with no tag adding. So, let it be. :-)

Created on Jan 28, 2024

@author: (c) LIX A.S. Mechanic.Kharkiv
@last_edit: 2024-04-22
'''
# DONE: sort out the version tag usage to keep it compatible with 2.7x and newer
#   we just use 2.80: older complain, but allow it; the newer just accept.

# Actually it works OK from version 2.76. Maybe even older, just give it a try.

bl_info = {
    "name": "FBX format batch import patch",
    "author": "(c) LIX A.S. Mechanic.Kharkiv",
    "version": (2, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Import > FBX (.fbx)",
    "description": "Patches standard fbx importer to handle multiple files and tag the imported stuff.",
    "support": 'COMMUNITY',
    "category": "Import-Export",
    "wiki_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/fbx_batch_import",
    "doc_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/fbx_batch_import",
    "tracker_url": "https://github.com/mechanic-kharkiv/small-blender-scripts/issues",
}

import sys
import ast
from collections import OrderedDict
import bpy

FBX_IMPORT_MODULE_NAME = "io_scene_fbx"
FBX_IMPORT_CLASS_NAME = "ImportFBX"
MENU_INCLUDE_CLASS_28 = "FBX_PT_import_include"

DEBUG = 0

def load_module_if_not_yet(module_name):
    " if it's not cashed yet, load it. returns the module."
    module = sys.modules.get(module_name)
    if not module:
        print("loading the %s module" % module_name)
        spec = None
        # finding spec
        for path_finder in sys.meta_path:
            spec = path_finder.find_spec(module_name, None)
            #print("path_finder", path_finder, "spec", spec)
            if spec:
                break

        if not spec:
            return False
        module = spec.loader.load_module(spec.name)
    return module


class AstNode:
    "a wrapper to hold navigation references"
    __slots__ = ("ast", "lineno", "last_lineno", "parent", "children")

    def __init__(self, ast_node, parent=None, children=None):
        self.ast = ast_node
        self.lineno = ast_node.lineno
        self.last_lineno = -1
        self.parent = parent
        if children is None:
            children = []
        self.children = children

    def update_line_numbers(self):
        "find last_lineno for the node (last used line in children)"

        def get_last_line(ast_node):
            ln = ast_node.lineno if hasattr(ast_node, "lineno") else -1
            for nd1 in ast.iter_child_nodes(ast_node):
                ln = max(ln, get_last_line(nd1))
            return ln

        if hasattr(self.ast, "lineno"):
            self.lineno = self.ast.lineno
        self.last_lineno = get_last_line(self.ast)

def iter_patch_points(nd, result, parent=None):
    " adds found nodes (:AstNode) in result as named fields."
    global ast_classes
    if nd is None:
        return None

    if type(nd) is ast.ClassDef:
        # we look just for one class
        if nd.name in (FBX_IMPORT_CLASS_NAME, MENU_INCLUDE_CLASS_28):
            descr = AstNode(nd, parent)
            if nd.name  == FBX_IMPORT_CLASS_NAME:
                result["cls"] = descr
            else:
                result["cls.draw28"] = descr
            for nd1 in ast.iter_child_nodes(nd):
                descr.children.extend(iter_patch_points(nd1, result, descr))
            descr.update_line_numbers()
            yield descr

    elif type(nd) is ast.Name:
        # we look for some class field names
        if (nd.id in ("files","filename_ext") and parent and type(parent.ast) is ast.ClassDef):
            descr = AstNode(nd, parent)
            result["cls." + nd.id] = descr
            descr.update_line_numbers()
            yield descr

    elif type(nd) is ast.Str:
        # look if there is line 'keywords["use_cycles"] = ..'
        if (nd.s == "use_cycles" and parent and type(parent.ast) is ast.FunctionDef and parent.ast.name == "execute"):
            result["cls.execute.use_cycles"] = True

    elif type(nd) is ast.FunctionDef:
        # we look for class methods
        if nd.name in ("execute","draw") and parent and type(parent.ast) is ast.ClassDef:
            descr = AstNode(nd, parent)
            if nd.name == "draw" and parent.ast.name == MENU_INCLUDE_CLASS_28:
                result["cls.draw28"] = descr
            else:
                result["cls." + nd.name] = descr
            for nd1 in ast.iter_child_nodes(nd):
                descr.children.extend(iter_patch_points(nd1, result, descr))
            descr.update_line_numbers()
            yield descr

    else:
        for nd1 in ast.iter_child_nodes(nd):
            yield from iter_patch_points(nd1, result, parent)

# lines to insert into source_lines
patch_lines = {
    "draw_flags" : """
        layout.prop(self, 'add_tags')
        layout.prop(self, 'action_fake_user')
        layout.prop(self, 'action_filter_names')
        layout.prop(self, 'verbose')
    """,

    "files" : 'files = bpy.props.CollectionProperty(name="File Path", type=bpy.types.OperatorFileListElement)',

    "prop3" : """
        add_tags = BoolProperty(
            name="Add 'fbxpath' tags",
            description="Add fbxpath property to all imported objects",
            default=True)

        """,

    "prop2" : """
        action_fake_user = BoolProperty(name="Fake User for Actions", default=True, description="Set fake user for new actions")

        """,

    "prop1" : """
        action_filter_names = BoolProperty(name="Filter Action Names", default=False, description="Use {object|file} as action name")

        """,

    "prop0" : 'verbose = BoolProperty(name="Verbose", default=False, description="Verbose console output")\n',

    "dummy" : """
        class DummyFile(object):
            def write(self, x): pass

        """,

    "use_cycles" : "    keywords['use_cycles'] = (context.scene.render.engine == 'CYCLES')",

    "execute" : r"""
        def import_single_fbx(self, context, path, **keywords):
            import sys
            from . import import_fbx
            save_stdout = sys.stdout
            try:
                if not self.verbose:
                    print("\nImporting {}".format(path))
                    sys.stdout = DummyFile() # suppress its output
                ret = import_fbx.load(self, context, filepath=path, **keywords)
            finally:
                sys.stdout = save_stdout
            return ret

        def execute(self, context):
            FBXPATH_TAG_NAME = "fbxpath"
            keywords = self.as_keywords(ignore=("add_tags", "verbose", "action_fake_user", "action_filter_names",
                "filter_glob", "directory", "ui_tab", "filepath", "files"))

            import os

            if self.files:
                dirname = os.path.dirname(self.filepath)
                fbx_files = [os.path.join(dirname, file.name) for file in self.files]
            else:
                fbx_files = [self.filepath,]

            # store current objects_list
            objects_list = [obj for obj in context.scene.objects]
            actions_list = [obj for obj in bpy.data.actions]
            cnt_meshes = cnt_armatures = cnt_actions = cnt_files = 0

            error_messages = []

            ret = {'CANCELLED'}
            for path in fbx_files:
                try:
                    if self.import_single_fbx(context, path, **keywords) == {'FINISHED'}:
                        ret = {'FINISHED'}
                except Exception as e:
                    mess = "file {}: {}".format(path, e)
                    print("ERROR: " + mess)
                    self.report({'ERROR'}, mess)
                    error_messages.append(mess)
                    continue

                cnt_files += 1
                # find all new_objects added with last import
                new_objects = [obj for obj in context.scene.objects if obj not in objects_list]
                new_actions = [obj for obj in bpy.data.actions if obj not in actions_list]
                actions_list = [obj for obj in bpy.data.actions]
                cnt_actions += len(new_actions)

                for new_object in new_objects:
                    if self.add_tags:
                        # add a custom property with the source path
                        new_object[FBXPATH_TAG_NAME] = path
                        if new_object.data:
                            new_object.data[FBXPATH_TAG_NAME] = path
                    # register the new object
                    objects_list.append(new_object)
                    if new_object.type == 'MESH':
                        cnt_meshes += 1
                    elif new_object.type == 'ARMATURE':
                        cnt_armatures += 1

                for new_action in new_actions:
                    new_action.use_fake_user = self.action_fake_user
                    if self.add_tags:
                        # fill the property with the source path
                        setattr(new_action, FBXPATH_TAG_NAME, path)
                    if self.action_filter_names:
                        new_action.name = "{}|{}".format(new_action.name.split("|")[0], os.path.splitext(os.path.basename(path))[0])

                if len(new_objects):
                    mess = "imported objects: " + ", ".join((obj.name for obj in new_objects))
                    print(mess)
                    self.report({'DEBUG'}, mess)
                if len(new_actions):
                    mess = "imported actions: " + ", ".join((act.name for act in new_actions))
                    print(mess)
                    self.report({'DEBUG'}, mess)

            mess = "Finished. Imported meshes [{}]; armatures [{}]; actions [{}]; from {} files.".format(
                            cnt_meshes, cnt_armatures, cnt_actions, cnt_files
                            )
            print(mess)
            self.report({'INFO'}, mess)
            if len(error_messages):
                self.report({'WARNING'}, "There was some files ({}) with errors. See console for details.".format(len(error_messages)))
                print("files with ERRORS:")
                for i, mess in enumerate(error_messages):
                    print(i+1, mess)

            return ret

        """,
}

def add_padding(s, pad_sz):
    "adds padding to every line of multiline s"
    import inspect
    pad = " "*pad_sz
    return "\n".join((pad + s1 for s1 in inspect.cleandoc(s).split("\n")))

def patch_module(module):
    " patches module source, recompiles it, and returns the patched one"
    # first read the code
    src_lines = []
    with open(module.__file__, "r", encoding="utf-8") as f:
        while True:
            s = f.readline()
            if s == "":
                break
            src_lines.append(s[:-1]) # no LF

    # parse it
    root = ast.parse("\n".join(src_lines))

    # find the patch points to insert code to
    path_points = OrderedDict()
    _ = tuple(iter_patch_points(root, path_points))

    # insert patching code (from bottom to top)
    for pp_id in reversed(path_points):

        if pp_id == "cls.execute.use_cycles":
            # no node, just a flag
            ss = add_padding(patch_lines["execute"], 0).split("\n")
            if patch_lines["use_cycles"] not in ss:
                ss = (s if not s.startswith("    import os") else patch_lines["use_cycles"] + "\n\n" + s for s in ss)
                patch_lines["execute"] = "\n".join(ss)
            continue

        pp_node = path_points[pp_id]

        if pp_id == "cls.execute":
            s = add_padding(patch_lines["execute"], pp_node.ast.col_offset)
            ln = pp_node.last_lineno
            while ln >= pp_node.lineno:
                ln -= 1
                src_lines.pop(ln)
            src_lines.insert(pp_node.lineno - 1, s)

        elif pp_id == "cls.draw":
            # insert properties into draw()
            if pp_node.last_lineno - pp_node.lineno > 3:
                # some have just pass
                s = add_padding(patch_lines["draw_flags"], pp_node.ast.col_offset + 4)
                src_lines.insert(pp_node.last_lineno, s)

        elif pp_id == "cls.draw28":
            # insert add_tags, verbose checkboxes
            s = add_padding(patch_lines["draw_flags"], pp_node.ast.col_offset + 4)
            s = s.replace("self", "operator")
            src_lines.insert(pp_node.last_lineno, s)

        elif pp_id == "cls.filename_ext":
            ln = pp_node.lineno - 1
            # insert 'files' if none yet
            if "cls.files" not in path_points:
                s = " "*(pp_node.ast.col_offset) + patch_lines['files']
                if bpy.app.version >= (2, 80):
                    s = s.replace(" = ", ": ", 1)
                src_lines.insert(ln, s)

            # insert "anyway" properties
            i = 0
            while True:
                s = patch_lines.get("prop" + str(i), None)
                i += 1
                if not s:
                    break

                if bpy.app.version >= (2, 80):
                    s = s.replace(" = ", ": ", 1)
                s = add_padding(s, pp_node.ast.col_offset)
                src_lines.insert(ln, s)

        elif pp_id == "cls":
            # insert DummyFile class
            s = add_padding(patch_lines["dummy"], pp_node.ast.col_offset)
            # we intentionally skip a line for possible decorator
            src_lines.insert(pp_node.lineno - 2, s)

    if DEBUG:
        bpy.context.window_manager.clipboard = "\n".join(src_lines)

    # using the same module
    code = compile("\n".join(src_lines), filename=module.__file__, mode='exec')
    exec(code, module.__dict__)
    return module


def install_fbx_hook():
    "this will patch the cashed module with our version if not already patched. True if success."
    # load module into the cache if needed
    orig_module = load_module_if_not_yet(FBX_IMPORT_MODULE_NAME)

    # check if it's already patched
    patched = hasattr(orig_module.ImportFBX, "add_tags")
    if patched:
        print("Module {} is already patched".format(FBX_IMPORT_MODULE_NAME))
        return True

    # unregister original
    try:
        sys.modules[FBX_IMPORT_MODULE_NAME].unregister()
    except:
        pass

    # replace module with the patched one
    patched_module = patch_module(orig_module)
    if not patched_module:
        return False

    # and re-register it
    sys.modules[FBX_IMPORT_MODULE_NAME] = patched_module
    sys.modules[FBX_IMPORT_MODULE_NAME].register()

    print("Module {} was successfully patched".format(FBX_IMPORT_MODULE_NAME))
    return True


def uninstall_fbx_hook():
    " reloads original module. (e.g. if user disables the add-on)"
    import imp
    if FBX_IMPORT_MODULE_NAME in sys.modules:
        try:
            sys.modules[FBX_IMPORT_MODULE_NAME].unregister()
        except:
            pass

        imp.reload(sys.modules[FBX_IMPORT_MODULE_NAME])
    else:
        __import__(FBX_IMPORT_MODULE_NAME)
    try:
        sys.modules[FBX_IMPORT_MODULE_NAME].register()
        print("Original " + FBX_IMPORT_MODULE_NAME + " have been reloaded.")
    except Exception as e:
        print(e)


def register():
    bpy.types.Action.fbxpath = bpy.props.StringProperty(description="imported from")
    install_fbx_hook()

def unregister():
    uninstall_fbx_hook()
    del bpy.types.Action.fbxpath

if __name__ == "__main__":
    register()
    # test call
    bpy.ops.import_scene.fbx('INVOKE_DEFAULT')
