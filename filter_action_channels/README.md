## Filter action channels operator ##

### Description ###

The add-on adds an operator to remove unnecessary animation data from animation actions of selected Armatures. It works exclusively on armatures, and their actions.

It doesn't crunch animation keyframes, but only removes those keyframes / F-curves, which give nothing to the animation. So, it's kind of lossless operation:

- It removes all channels of absent bones (could be dangerous, if the action is used on another object, where they could exist);
- It removes location channels if the bone is connected to its parent, hence cannot move (also could be dangerous, if the action is intended for use on other objects);
- It kills all keyframes in the F-curve but the first, if their values don't change at all (safe);

>Dangerous means, that if in one armature there are some bones absent, or connected to their parents, and you filter an action, which is linked to this armature, those channels will be removed, but the same very action could be linked later to another armature, where these bones exist (or are not connected to parents, hence can move). In this case the latter armature will suffer from the animation data loss.

However, some logic was implemented in this script to diminish such danger conditions. It will keep as much data, as it can, looking for armatures which are referencing each processing action directly or with object's NLA strips (both stashed and alive).

Having this reference info, the script can see, that there is more than one armature belonging to any particular action. So, when filtering each action it uses existing bone list, and connected bone list, composed from all armatures that reference this action. This way, if a bone is not connected in *any* of the referencing armatures, then it will not be considered connected, and if a bone exists in *any* referencing armature, it will not be considered absent, and filters will not touch those channels. You can somehow control the reference search with the `Global references search` flag.

Anyway, this feature can handle only armatures in the current blend file, and if they reference actions in their NLA stacks. It cannot see any references beyond the blend file. So, plan ahead what exactly you shrink this way.

### Usage ###

The menu item `3D View > Object Mode > Object > Animation > Filter action(s) channels` invokes a popup window, which allows you to select which filters you want to apply, and some additional options. Here you set desired parameters, and press `OK` button to execute the operation.

It will report operation statistics into the system console, and into the `Info` window.

If you want to change some parameters after execution, you can use the blender's operator parameters window, which will 'undo-then-re-apply' the operator with new parameters.

Also you can use blender `Undo` command as usual.

#### Operator parameters ####

1. Filters to apply:

    * **Filter constant keys** - Remove all keyframes except the first if they don't change the channel's value.

        This filter checks if any keyframe value vary more than `EPSILON = 0.000001` from other values in this F-curve. If this is the case, this F-curve is considered constant, and will be truncated to the only keyframe (first).

    * **Filter absent bones** - Remove channels with no corresponding pose bones in the referencing armatures.

        This one removes F-curves which use names of bones absent in all referencing armatures.

    * **Filter connected Loc** - Remove location channels for connected bones.

        Connected bones cannot move but rotate and scale only. This filter detects location F-curves on bones which are connected to their parents in *all* referencing armatures, and removes these F-curves entirely.

2. Additional options:

    * **Also filter NLA actions** - Process also all actions mentioned in NLA strips.

        This flag adds all actions mentioned in all NLA strips of selected armatures to the actions to filter.

        If this flag is reset, the only action to process per selected object is the one which is directly linked to this object (if any).

    * **Global references search** - Look for referencing armatures beyond the selection.

        This option allows to search for referencing armatures in all objects in the blend file (even in other scenes). It extracts all actions references from all strips in all NLA tracks, regardless of their state (muted, stashed, solo, etc).

        If this flag is reset, this search will include only selected objects' actions and their NLA stacks.

        >Keeping this flag ON makes operations safer, because it gives more referencing armatures to each action, and this will preserve more data, if those armatures add to channel names to keep untouched.

    * **Dry run** - No actual removing of anything, but showing statistics.

        This doesn't apply any operations, but reports them.

    * **Verbose** - Show detailed log in the console.

        In verbose mode it reports to the console all actions performed, affected F-curves' names, and filtering conditions.

### Installation ###

The add-on consists of one single file `filter_action_channels.py`.

You can install it in two ways:

  1. open in blender's text editor, and run (*Text => Run Script <Alt+P>*) (this will install the add-on for the current session only);

  2. use the standard installation procedure with the 'Install from file' button in the 'Add-ons' section of the 'Preferences' dialog (this type of installation is permanent);

        >If your blender version is far from 2.80, it may warn you about versions mismatch - don't worry, it's deliberately contrived this way. If you're able to enable the add-on with the checkbox, this warning is about nothing at all.

### Uninstallation ###

You can disable or remove the add-on in the 'Add-ons' section of the 'Preferences' dialog.

### Compatibility ###

It was tested in:
- v2.76b (windows 64 bit);
- v2.79b (windows 64 bit);
- v4.0.2 (windows 64 bit);

In other versions of blender this will probably work, but be prepared for surprises.

### Feedback ###

Feel free to comment, fork and pull request, or create an issue.

It might not be super fast, but I'll definitely will track those things.
