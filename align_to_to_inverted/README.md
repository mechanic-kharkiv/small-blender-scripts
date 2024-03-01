## Align to Transform Orientation inverted ##

### Description ###

  This add-on adds a command to align an object rotation without rotating the object itself. It works like the standard `Align to Transform Orientation`, but after aligning the object it rotates the object underligning data back to compensate the rotation change.

  It also can use the active object as the target rotation. In this case the active object gives its rotation to all selected objects.

### Usage ###

  Select an object (or multiple objects) in object mode, then set desired Transform Orientation in the current viewport, and execute the `Align to Transform Orientation inverted` command in the `Object -> Transform` menu.

  If you want to align transforms not to a Transform Orientation, but to an object, then you have the `To active object` flag in the operator parameters.
  
  Be aware that not all of the Transform Orientations are supported. If you will try to use one of ('LOCAL', 'NORMAL', 'GIMBAL', 'CURSOR'), it will say, that this is not supported. Only 'GLOBAL', 'VIEW', and any custom TO will do.


### Installation ###

Add-on consists of single file **align_to_to_inverted.py**.

You can install it in two ways:

  1. open in blender's text editor, and run (*Text => Run Script <Ctrl+P>*) (this will install the add-on for the current session only);

  2. use the standard installation procedure with the 'Install from file' button in the 'Add-ons' section of the 'Preferences' dialog (this type of installation is permanent);

        >If your blender version is far from 2.80, it may warn you about versions mismatch - don't worry, it's deliberately contrived this way. If you're able to enable the add-on with the checkbox, this warning is about nothing at all.


### Uninstallation ###

You can disable or remove the add-on in the 'Add-ons' section of the 'Preferences' dialog.


### Compatibility ###

  It was tested in:

  - v2.68a (windows 64 bit);
  - v2.76b (windows 64 bit);
  - v2.92 (windows 64 bit);
  - v4.0.2 (windows 64 bit);

  In other versions of blender this will probably work, but be prepared for surprises.


### Feedback ###

Feel free to comment, fork and pull request, or create an issue.

It might not be super fast, but I'll definitely will track those things.
