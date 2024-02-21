# -*- coding: 'utf-8' -*-

bl_info = {
    "name": "Marker Library",
    'author': '(c) LVII - LIX A.S. Mechanic.Kharkiv',
    'version': (1, 1, 0),
    'blender': (2, 80, 0),
    'location': 'Properties > Scene > Marker Library panel',
    'description': 'Stores scene markers in library named items to restore them later.',
    'wiki_url': "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/marker_library",
    'tracker_url': "https://github.com/mechanic-kharkiv/small-blender-scripts/issues",
    'support': 'COMMUNITY',
    "category": "Scene",
}

"""
@author: Mechanic.Kharkiv
@last_edit: 2024-02-21
"""

import bpy

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

# Define the collection properties

# single marker
@make_annotations
class MarkerDefinition(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Name", default="?")
    frame = bpy.props.IntProperty(name="Frame", default=-1)
    camera = bpy.props.StringProperty(name="Camera", default="")
    select = bpy.props.BoolProperty(name="Selected", default=False)

# named marker collection
@make_annotations
class MarkerCollectionItem(bpy.types.PropertyGroup):
    markers = bpy.props.CollectionProperty(type=MarkerDefinition)
    name = bpy.props.StringProperty(name="Test Str Prop", default="Unknown")

# group with library, and current id for convenience
@make_annotations
class MarkerLibrary(bpy.types.PropertyGroup):
    library = bpy.props.CollectionProperty(type=MarkerCollectionItem, description="Marker library items collection")
    current_item = bpy.props.IntProperty(name="current item index", default=-1)

# operators

class MarkerLibraryStore(bpy.types.Operator):
    """Store scene markers into current item [or create new if none]"""
    bl_idname = "scene.marker_library_store"
    bl_label = "Store into current"
    bl_options = {'REGISTER', 'UNDO'}

    def new_unique_name(self, context, collection):
        """ returns new unique name for a new item """
        ob = context.active_object
        if ob:
            prefix = "@"+ob.name
        else:
            prefix = "New"
        i = 0
        while True:
            i += 1
            new_name = "{}-{:03d}".format(prefix,i)
            if collection.find(new_name) < 0:
                break
        return new_name

    def execute(self, context):
        scene = context.scene
        mml = scene.my_marker_library
        mmll = mml.library

        # check if we need to create a new item
        no_current = (len(mmll) == 0 or mml.current_item < 0 or mml.current_item >= len(mmll))
        if (no_current):
            my_item = mmll.add()
            my_item.name = self.new_unique_name(context, mmll)
            mml.current_item = len(mmll)-1
        else:
            my_item = mmll[mml.current_item]

        markers = scene.timeline_markers

        #print("Storing {} markers to the collection item {}".format(len(markers), my_item.name))

        my_item.markers.clear()
        for m in markers:
            mf = my_item.markers.add()
            mf.frame = m.frame
            mf.name = m.name
            mf.camera = m.camera.name if m.camera else ""
            mf.select = m.select

        return {'FINISHED'}


class MarkerLibraryStoreNew(bpy.types.Operator):
    """Store scene markers into new item"""
    bl_idname = "scene.marker_library_store_new"
    bl_label = "Store into new"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mml = scene.my_marker_library
        mml.current_item = -1
        return bpy.ops.scene.marker_library_store()


class MarkerLibraryRestore(bpy.types.Operator):
    """Restore scene markers from current item"""
    bl_idname = "scene.marker_library_restore"
    bl_label = "Restore from current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        mml = scene.my_marker_library
        mmll = mml.library
        no_current = (len(mmll) == 0 or mml.current_item < 0 or mml.current_item >= len(mmll))
        return not no_current

    def execute(self, context):
        scene = context.scene
        mml = scene.my_marker_library
        mmll = mml.library

        # check if we need to create a new item
        no_current = (len(mmll) == 0 or mml.current_item < 0 or mml.current_item >= len(mmll))
        if (no_current):
            return {'CANCELLED'}

        my_item = mmll[mml.current_item]
        markers = scene.timeline_markers

        #print("Restoring {} markers from the collection item {}".format(len(my_item.markers), my_item.name))

        markers.clear()
        for m in my_item.markers:
            marker = markers.new(m.name)
            marker.frame=m.frame
            if (m.camera != ""):
                camera = scene.objects.get(m.camera)
                if camera:
                    marker.camera = camera
            marker.select = m.get("select", False) # might be absent (from old version)

        return {'FINISHED'}

class MarkerLibraryRemove(bpy.types.Operator):
    """Remove the current item"""
    bl_idname = "scene.marker_library_remove"
    bl_label = "Remove current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        mml = scene.my_marker_library
        mmll = mml.library
        no_current = (len(mmll) == 0 or mml.current_item < 0 or mml.current_item >= len(mmll))
        return not no_current

    def execute(self, context):
        scene = context.scene
        mml = scene.my_marker_library
        mmll = mml.library

        no_current = (len(mmll) == 0 or mml.current_item < 0 or mml.current_item >= len(mmll))
        if (no_current):
            return {'CANCELLED'}

        mmll.remove(mml.current_item)
        if mml.current_item >= len(mmll):
            mml.current_item = len(mmll)-1
        return {'FINISHED'}

class MarkersCopy(bpy.types.Operator):
    """Copy scene markers to clipboard"""
    bl_idname = "scene.markers_copy"
    bl_label = "Copy markers"
    bl_options = set()

    def execute(self, context):
        context.window_manager.clipboard = "\n".join(["{}\t{}\t{}\t{}".format(
            m.frame, m.name, m.camera.name if m.camera else "", 1 if m.select else 0)
            for m in context.scene.timeline_markers])+"\n\n"
        return {'FINISHED'}

class MarkersPaste(bpy.types.Operator):
    """Paste scene markers from clipboard"""
    bl_idname = "scene.markers_paste"
    bl_label = "Paste markers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        markers = context.scene.timeline_markers
        markers.clear()
        for s in context.window_manager.clipboard.split("\n"):
            if s:
                try:
                    _frame, _name, _camera, _select = s.split("\t")
                    m = markers.new(_name)
                    m.frame=int(_frame)
                    if (_camera != ""):
                        m.camera = context.scene.objects.get(_camera, None)
                    m.select = _select == "1"
                except:
                    pass
        return {'FINISHED'}

def get_frame_range(scene):
    """ returns range start, end of active scene frame range. """
    frame_start = scene.frame_preview_start if scene.use_preview_range else scene.frame_start
    frame_end = scene.frame_preview_end if scene.use_preview_range else scene.frame_end
    return (frame_start, frame_end)

def get_marked_frames(scene):
    """ returns set of currently marked frame numbers """
    return set({m.frame for m in scene.timeline_markers})

def get_unmarked_frames(scene):
    """ returns a set with currently unmarked frame numbers """
    marked = get_marked_frames(scene)
    start, end = get_frame_range(scene)
    return {frame for frame in range(start, end+1) if frame not in marked}

def clear_markers_in_range(scene):
    """ removes all markers in the scene frame range. """
    tms = scene.timeline_markers
    start, end = get_frame_range(scene)
    i = len(tms)
    while (i > 0):
        i -= 1
        marker = tms[i]
        if (start <= marker.frame and marker.frame <= end):
            tms.remove(marker)


class SceneMarkersInvert(bpy.types.Operator):
    """Invert the scene markers in the active frame range."""
    bl_idname = "scene.markers_invert"
    bl_label = "Invert scene markers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        scene = context.scene
        unmarked_frames = get_unmarked_frames(scene)
        clear_markers_in_range(scene)
        for frame in unmarked_frames:
            m = scene.timeline_markers.new("F_{}".format(frame))
            m.frame=frame
        return {'FINISHED'}

class MarkerLibraryPanel(bpy.types.Panel):
    """Creates a Panel in the Scene properties window"""
    bl_label = "Marker Library"
    bl_idname = "SCENE_PT_marker_library"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        mml = bpy.context.scene.my_marker_library #.library  .current_item

        # template_list now takes two new args.
        # The first one is the identifier of the registered UIList to use (if you want only the default list,
        # with no custom draw code, use "UI_UL_list").
        layout.template_list("UI_UL_list", "my_ui_list", mml, "library", mml, "current_item")

        #layout.prop(mml, "current_item", expand=True)

        row = layout.row()
        row.operator("scene.marker_library_restore")
        row.operator("scene.marker_library_remove")
        row = layout.row()
        row.operator("scene.marker_library_store")
        row.operator("scene.marker_library_store_new")
        layout.separator()
        row = layout.row()
        row.operator("scene.markers_invert")
        layout.separator()
        row = layout.row()
        row.operator("scene.markers_copy", icon="COPYDOWN")
        row.operator("scene.markers_paste", icon="PASTEDOWN")


def register():
    bpy.utils.register_class(MarkerDefinition)
    bpy.utils.register_class(MarkerCollectionItem)
    bpy.utils.register_class(MarkerLibrary)
    bpy.types.Scene.my_marker_library = \
        bpy.props.PointerProperty(type=MarkerLibrary)
    bpy.utils.register_class(MarkerLibraryStore)
    bpy.utils.register_class(MarkerLibraryStoreNew)
    bpy.utils.register_class(MarkerLibraryRestore)
    bpy.utils.register_class(MarkerLibraryRemove)
    bpy.utils.register_class(SceneMarkersInvert)
    bpy.utils.register_class(MarkersCopy)
    bpy.utils.register_class(MarkersPaste)
    bpy.utils.register_class(MarkerLibraryPanel)


def unregister():
    bpy.utils.unregister_class(MarkerLibraryPanel)
    bpy.utils.unregister_class(MarkersPaste)
    bpy.utils.unregister_class(MarkersCopy)
    bpy.utils.unregister_class(SceneMarkersInvert)
    bpy.utils.unregister_class(MarkerLibraryStore)
    bpy.utils.unregister_class(MarkerLibraryStoreNew)
    bpy.utils.unregister_class(MarkerLibraryRestore)
    bpy.utils.unregister_class(MarkerLibraryRemove)
    del(bpy.types.Scene.my_marker_library)
    bpy.utils.unregister_class(MarkerLibrary)
    bpy.utils.unregister_class(MarkerCollectionItem)
    bpy.utils.unregister_class(MarkerDefinition)

def test_show():
    """ show current library in console """
    scene = bpy.context.scene
    mml = scene.my_marker_library.library
    for my_item in mml:
        print(len(my_item.markers), my_item.name, ':')
        for m in my_item.markers:
            print("\tname={} frame={}".format(m.name, m.frame))

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass

    register()
    test_show()
