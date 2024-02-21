## Marker library ##

### Description ###

  This script (add-on) will help to organize scene markers. Markers are those little marks on the timeline, which have labels, can switch cameras, and are quickly positioned with `'Jump to next marker'`, `'Jump to previous marker'` commands.

  If you've ever regretted that there's only one set of markers per scene, then this is the add-on for you.

  It stores your scene markers into a collection of named items, which can be quickly restored along with selection, names, and bind cameras. The library is saved within the *.blend* file.

  It also can copy your markers to clipboard in plain text to paste it into another scene, or another blender instance, or any text editor later.

  Each scene in the *.blend* file has its own marker library.

  >You can duplicate it, if you use `'Copy settings'` when duplicating an existing scene.


### Usage ###

  The UI controls of the add-on sit in the **Marker library** panel of the **Scene** tab in **Properties** editor.

  There are the list of stored marker sets, and buttons to operate the list and the scene markers.

Blender **Undo** command works for all the operators in this panel.

#### Command buttons ####

1. Library commands

    * **Restore from current** - Restore scene markers from current selected item into the scene.

    * **Store into current** - Store scene markers into current selcted item \(or create new if there is none yet).

    * **Store into new** - Store scene markers into a new item.

        >When you store a new library item, its name will contain the active object name (if any). So, you can have marker sets "on per-object basis".
        >Anyway, you can rename items with double-click, or \<Ctrl>+Click on the item, if you wish.

    * **Remove current** - Remove the current item.

2. Scene markers commands

    * **Copy markers** - Copy scene markers to clipboard.

    * **Paste markers** - Paste scene markers from clipboard.

    * **Invert scene markers** - Invert the scene markers in the active frame range.

        This command removes markers from frames already containing markers, and creates markers for frames that have no markers. Names for new markers are `F_nn`, where `nn` = frame number.

        It respects the current range of frames (either the scene or the preview, that is active).

        This is useful if you, for example, have an image sequence, which you use to paint textures from, and have some bad frames in the sequence which you want to skip. So, you just set markers on those bad frames, invert, and then jump between good frames only.

        >It's handy to set key bindings `Page Up`, `Page Down` for command `'Jump to marker' ('screen.marker_jump')` with its `'Next Marker'` flag set and reset respectively.
        >It sits in *Preferences > Keymap > Screen > Screen (Global)*.


### Installation ###

Add-on consists of single file **marker_library.py**.

You can install it in two ways:

  1. open in blender's text editor, and run (*Text => Run Script <Ctrl+P>*) (this will install the add-on for the current session only);

  2. use the standard installation procedure with the 'Install from file' button in the 'Add-ons' section of the 'Preferences' dialog (this type of installation is permanent);

        >If your blender version is far from 2.80, it may warn you about versions mismatch - don't worry, it's deliberately contrived this way. If you're able to enable the add-on with the checkbox, this warning is about nothing at all.


### Uninstallation ###

You can disable or remove the add-on in the 'Add-ons' section of the 'Preferences' dialog.

>With the add-on disabled or removed, your existing libraries do still exist in .blend files, and would be accessed again when you enable or re-install the add-on.


### Compatibility ###

  It was tested in:

  - v2.68a (windows 64 bit);
  - v2.76b (windows 64 bit);
  - v2.92 (windows 64 bit);

  In other versions of blender this will probably work, but be prepared for surprises.


### Feedback ###

Feel free to comment, fork and pull request, or create an issue.

It might not be super fast, but I'll definitely will track those things.
