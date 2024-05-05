## FBX batch import ##

### Description ###

This add-on patches the embedded blender fbx importer (`io_scene_fbx` by Campbell Barton and others) in memory to allow it to import multiple selected fbx files into the current scene.

Optionally each imported object receives a property `fbxpath` with the original source file full path.
It tags objects, armature and mesh data blocks, and actions. These tags are intended to be used by user scripts.

  > id_data objects like `Object`, `Mesh`, `Armature` get a custom property, but for `Action` it adds a property also called `fbxpath`. So in scrips you'd rather use `action.fbxpath` instead of `action["fbxpath"]`.

  > The embedded `io_scene.fbx` since 4.20.2 (blender 2.81.6) already supports multiple files,
but with no tag adding. So, let it be. :-)

Also it has some additional options:

  - `Fake User for Actions` (default=True)
    Allows to control whether the `Fake User` flag for the imported actions will be set or not;

  - `Filter Action Names`, (default=False)
    Uses `"$object_name|$fbx_file_name"` as imported action name. It's useful if there are complex action names with useless garbage inside;


### Usage ###

  Install the add-on, enable it.

  Next time you invoke `File > Import > FBX (.fbx)` you will face the new checkboxes (

  - `Add 'fbxpath' tags`,
  - `Fake User for Actions`,
  - `Filter Action Names`,
  - `Verbose`

  ) in the import dialog which means you have your standard fbx importer patched.

### Installation ###

Add-on consists of single file `fbx_batch_import_patch.py`.

You can install it in two ways:

  1. open in blender's text editor, and run (*Text => Run Script <Alt+P>*) (this will install the add-on for the current session only);

  2. use the standard installation procedure with the 'Install from file' button in the 'Add-ons' section of the 'Preferences' dialog (this type of installation is permanent);

  > If your blender version is far from 2.80, it may warn you about versions mismatch - don't worry, it's deliberately contrived this way. If you're able to enable the add-on with the checkbox, this warning is about nothing at all.


### Uninstallation ###

You can disable or remove the add-on in the 'Add-ons' section of the 'Preferences' dialog.

On disabling (or uninstalling) it reloads and re-registers the original importer module immediately, there is no need to restart blender or reload scripts.


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
