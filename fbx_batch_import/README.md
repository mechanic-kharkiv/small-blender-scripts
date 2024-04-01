## FBX batch import ##

### Description ###

  This add-on allows batch import of fbx files in the given directory. It uses a named preset, saved ahead in standard blender fbx importer (`io_scene_fbx`).

  It also marks imported objects with special property `fbxpath` to allow other scripts to know what exactly were loaded from where.

  > The embedded `io_scene.fbx` since 4.20.2 (blender 2.81.6) already supports multiple files,
but with no tag adding. So, let it be. :-)

### Usage ###

  If you need non-default fbx import settings, first you need to invoke the standard importer `File > Import > FBX (.fbx)`, set desired settings and save them as a named preset.

  Next you Execute `File > Import > FBX batch import (directory, preset)`, set your preset, and directory to import from. When you run import it will import all fbx files in this directory.

### Installation ###

Add-on consists of few files in the directory **fbx_batch_import**:
    - \__init__.py
    - classes27.py
    - classes28.py
    - presets.py

To install it you need to pack these files **along with the directory `fbx_batch_import`** into a zip archive (an archive name may be arbitrary), then follow the standard installation procedure with the 'Install from file' button in the 'Add-ons' section of the 'Preferences' dialog.

  > If your blender version is far from 2.80, it may warn you about versions mismatch - don't worry, it's deliberately contrived this way. If you're able to enable the add-on with the checkbox, this warning is about nothing at all.


### Uninstallation ###

You can disable or remove the add-on in the 'Add-ons' section of the 'Preferences' dialog.


### Compatibility ###

  It was tested in:

  - v2.76b (windows 64 bit);
  - v2.79b (windows 64 bit);
  - v2.92 (windows 64 bit);
  - v4.0.2 (windows 64 bit);

  In other versions of blender this will probably work, but be prepared for surprises.


### Feedback ###

Feel free to comment, fork and pull request, or create an issue.

It might not be super fast, but I'll definitely will track those things.
