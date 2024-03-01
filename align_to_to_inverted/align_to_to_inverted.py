"""
align_to_to_inverted.py
The script will align selected objects to current Transform Orientation set in the current 3D view.
It changes object's rotation values, but leaves its orientation intact. It is similar to blender's
standard 'Align to transform orientation' command, but rotates only transform, not the object data.

see also:  https://blender.stackexchange.com/q/110894/23172,

@author: (c) LIII-LIX A.S. Mechanic.Kharkiv
@last_edit: 2024-02-29

tested in 2.68, 2.76b, 2.92, 4.0.2;
"""

bl_info = {
    "name": "Align to Transform Orientation inverted",
    "description": "Operator to set objects' rotation as of current transform orientation.",
    "location": "3D View > Object Mode > Object > Transform menu",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "support": "COMMUNITY",
    'wiki_url': "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/align_to_to_inverted",
    'doc_url': "https://github.com/mechanic-kharkiv/small-blender-scripts/tree/master/align_to_to_inverted",
    'tracker_url': "https://github.com/mechanic-kharkiv/small-blender-scripts/issues",
    "warning": "",
    "category": "Object",
    "author" : "(c) LIII-LIX A.S. Mechanic.Kharkiv"
}

import bpy
from mathutils import Matrix
from bpy.props import BoolProperty
import operator
if bpy.app.version >= (2, 80, 0):
    matmul = operator.matmul
else:
    matmul = operator.mul

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
class AlignToTOInverted(bpy.types.Operator):
    """Aligns selected objects' rotation (object's only) to current TO"""
    bl_idname = "object.align_to_to_inverted"
    bl_label = "Align to Transform Orientation inverted"
    bl_options = {'REGISTER', 'UNDO'}

    to_active_object = BoolProperty(
            name="To active object",
            description="Use the active object rotation instead of transform orientation",
            default=False
        )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        # store current context (selection, active object)
        # find objects to process
        selection = [obj for obj in context.selected_objects]
        old_active = context.object

        # find current transform orientation target matrix
        space = context.space_data
        region_3d = space.region_3d

        if bpy.app.version < (2, 80, 0):
            to = space.transform_orientation # GLOBAL, LOCAL, NORMAL, GIMBAL, VIEW
            custom_to = space.current_orientation
        else:
            to = context.scene.transform_orientation_slots[0].type # GLOBAL, LOCAL, NORMAL, GIMBAL, VIEW, CURSOR
            custom_to = context.scene.transform_orientation_slots[0].custom_orientation

        m_rot_src = None
        using_active = False

        # is it to_active_object mode?
        if len(selection) > 1 and self.to_active_object:
            using_active = True
            m_rot_src = old_active.matrix_world
            #self.report({'INFO'}, "Using '%s' object's rotation" % (old_active.name))
        else:
            if custom_to is not None:
                # using custom transform orirntation
                m_rot_src = custom_to.matrix    # 3x3
                #print("Using Ttansform Oientation %s" % (custom_to.name))
            else:
                # using embedded transform orientation
                # to == LOCAL doesn't have any sense, as well as others
                if to in ('LOCAL', 'NORMAL', 'GIMBAL', 'CURSOR'):
                    self.report({'ERROR'}, "Align to '%s' is not supported" % (to))
                    return {'CANCELLED'}

                elif to == 'GLOBAL':
                    m_rot_src = Matrix.Identity(3)   # default global matrix

                elif to == 'VIEW':
                    # get matrix from viewport
                    m_rot_src = region_3d.view_rotation.to_matrix()

                else:
                    self.report({'ERROR'}, "Unknown transform orientatin '%s' is not supported" % (to))
                    return {'CANCELLED'}

                #self.report({'INFO'}, "Using Ttansform Oientation %s" % (to))

        # transposed (the same as inverted) rotation
        m_rot_src_i = m_rot_src.to_3x3().transposed()

        # enlarge for multiplication
        m_rot_src = m_rot_src.to_4x4()
        m_rot_src_i = m_rot_src_i.to_4x4()

        # apply transformations for each object
        bpy.ops.object.select_all(action='DESELECT')

        for obj in selection:

            if using_active and obj == old_active:
                continue

            try:
                # now we rotate it to revert TO rotation
                loc = obj.location.copy()
                obj.matrix_world = matmul(m_rot_src_i, obj.matrix_world)

                # applying this as default rotation
                if bpy.app.version < (2, 80, 0):
                    obj.select = True
                    context.scene.objects.active = obj
                else:
                    obj.select_set(state = True)
                    context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

                # and now we rotate it back to TO rotation
                obj.matrix_world = matmul(m_rot_src, obj.matrix_world)
                obj.location = loc
                if bpy.app.version < (2, 80, 0):
                    obj.select = False
                else:
                    obj.select_set(state = False)

            except Exception as e:
                self.report({'ERROR'}, "Exception %s on %s" % (e, obj.name))
                continue

        # restore saved context
        bpy.ops.object.select_all(action='DESELECT')
        if bpy.app.version < (2, 80, 0):
            for obj in selection:
                obj.select = True
            context.scene.objects.active = old_active
        else:
            for obj in selection:
                obj.select_set(state = True)
            context.view_layer.objects.active = old_active

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(
        AlignToTOInverted.bl_idname)


def register():
    bpy.utils.register_class(AlignToTOInverted)
    bpy.types.VIEW3D_MT_transform_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(AlignToTOInverted)
    bpy.types.VIEW3D_MT_transform_object.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.object.align_to_to_inverted()

