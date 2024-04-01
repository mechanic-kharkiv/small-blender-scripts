'''
Created on Feb 1, 2024

@author: mechanic
'''

import bpy
import os
import re
from types import SimpleNamespace

__all__ = ["NO_PRESET", "get_presets_dir", "read_operator_preset",
           "rescan_preset_names", "preset_names",
           "preset_list_callback",
          ]

NO_PRESET = "<No preset>"
REC_SETTER = re.compile(r"^op\.\S+?\s*=") # setter line ("op.xxx = ") in a preset *.py script

def get_presets_dir(operator_bl_idname):
    " returns presets directory path for the given operator. "
    return os.path.join(bpy.utils.user_resource('SCRIPTS'),  # @UndefinedVariable
                        "presets", "operator",
                        operator_bl_idname)

def read_operator_preset(operator_bl_idname, preset_name, ignore_keys=()):
    " returns a dict with given preset values."
    # find the preset if given
    preset_path = os.path.join(get_presets_dir(operator_bl_idname), preset_name + ".py")
    if os.path.isfile(preset_path):
        # prepare the file content for execution, removing lines not containing setters ("op.xxx = ")
        with open(preset_path, "r") as f:
            text = "".join([s for s in f.readlines() if REC_SETTER.match(s) is not None])
        # execute the script to collect values
        op = SimpleNamespace()
        try:
            exec(text)
        except Exception as e:
            print("Exception on preset {} execution: {}".format(os.path.split(preset_path)[1], repr(e)))
        return {k : v for k, v in op.__dict__.items() if k not in ignore_keys}
    else:
        return {}

# here we store preset names taken from the last directory scan
preset_names = []

def rescan_preset_names(operator_bl_idname):
    """ rescans preset_names list for given operator. """
    global preset_names
    #print("[scan]", end="", flush=True)
    preset_names.clear()
    try:
        preset_names.extend((s[:-3] for s in sorted(os.listdir(get_presets_dir(operator_bl_idname))) if s.lower().endswith(".py")))
    except:
        pass


"""
For dynamic values a callback can be passed which returns
a list in the same format as the static list. This function
must take 2 arguments (self, context), context may be None.
WARNING: There is a known bug with using a callback, Python
must keep a reference to the strings returned or Blender
will crash.
"""
def preset_list_callback(self, context):
    """ returns previously scanned preset_names ready for EnumProperty.items. """
    #print(".", end="", flush=True)
    items = [tuple((NO_PRESET, NO_PRESET, "use defaults"))]
    for s in preset_names:
        t = tuple((s,s,"",))
        items.append(t)
    return items
