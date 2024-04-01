'''
Created on Feb 1, 2024

@author: mechanic
'''

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from .presets import preset_list_callback

class FbxImportHelper(ImportHelper):
    filter_glob: StringProperty(
            default="*.fbx",
            options={'HIDDEN'},
            maxlen=1024,
            )

    files: CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )


class BatchImportOpProps():
    add_tags: BoolProperty(
            name="Add 'fbxpath' tags",
            description="Add fbxpath property to all imported objects",
            default=True,
            )

    preset_name: EnumProperty(
            name="Preset",
            description="Previously saved preset for import options",
            items=preset_list_callback,
            )
