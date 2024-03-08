## Bone Renamer ##

### Description ###

This add-on helps to batch-rename armature's bones. It binds  to an armature a dictionary to translate the original bone name to the alternative one. And then you can rename all selected bones back and forth with this dictionary with a single command.

The name dictionary is stored in the blend file, so you can swap bone names anytime you need.

The dictionary is stored as an object custom property ("orig_alt_name_table"). It's not shared with other objects. You can use copy/paste commands to transfer the dictionary to another object.

There is no UI to edit the dictionary, instead it uses any text or spreadsheet editor, importing and exporting the data via the system clipboard. You can copy the stored dictionary as a table, edit it externally, and paste it back. If there is no dictionary, it copies 'stub' dictionary for selected bones for you to begin with.

>When renaming bones Blender respects the linked action, as well as all actions stored in NLA strips (even stashed ones), hence all affected animation channels of those actions will be renamed as well to work correctly with the renamed bones.

### Usage ###

The UI controls of the add-on sit in the 3D-view's `Pose -> Rename bones...` menu. These commands rename bones to the alternative names and back, and also allow to modify the stored bone name dictionary.

Blender `Undo` command works for those operators which modify any scene data.

#### Menu Commands ####

1. Commands to rename selected bones
    These commands perform actual **selected bones** renaming. If they're disabled in the menu then there is no stored dictionary yet, and you have to define it first.

    * **Rename to alternative** - Rename selected bones to their alternative names.
    * **Rename to original** - Rename selected bones to their original names.

    These commands handle renaming even with overlapping names. So you can easily swap names of two bones in one go:
    ```
    Head	Hips
    Hips	Head
    ```
    This will lead to bone name doubling during the rename process, so at one moment there must be two bones with the same name. These commands manage this situation with in-between rename to temporary unique name to avoid collisions. The output will be like this:
    ```
    Armature: Skeleton
        ahead rename Head -> HeadX
        rename Hips -> Head
        rename HeadX -> Hips
   ```
   But if your rename is going to produce name conflicts at the end, this will be determined ahead, and it will stop with an error message. No renaming of any bone will be performed. So, it's pretty safe.

2. Commands to extract the stored dictionary (or 'stub' table):
    These commands copy the stored dictionary in a table format to the clipboard.
    If there is no stored dictionary yet, both commands return 'stub' table with the original bone names in both columns. This table is supposed to be edited externally.
    >They also show copied data in the console, which allows quickly see the dictionary content without pasting it somewhere.

    * **Copy name table (All)** - Copy entire name table to clipboard.
    * **Copy name table (Selected)** - Copy name table for selected bones to clipboard.
        >If some bones are already renamed, and there is no such original name in the dictionary for this bone, it will look in the alternative names to find matching dictionary entry to copy. 

3. Commands to modify the dictionary:
    All these commands assume the clipboard has a new name mapping table. This table consists of (original_name, alternative_name) pairs, `tab`-delimited, one pair per line.
    E.g.:
    ```
    Head	Head
    Hips	Hips
    Left_Eye	Eye.L
    Left_Foot	Foot.L
    Left_Hand	Hand.L
    Right_Eye	Eye.R
    Right_Foot	Foot.R
    Right_Hand	Hand.R
    ```
    >Note that there are two pairs which do nothing (*Head* and *Hips*). There is no need to have such pairs in the dictionary, but there is no harm of having them there.
    You can store only those name pairs which actually differ.
    Use one or more `tab`s to delimit names.
    Empty lines, and lines with no `tab` character are **ignored**.

    >None of these commands actually rename any bone. They are just about modifying the dictionary. To actually rename the bones, you'd use one of `Rename..` commands.

    * **Paste name table (Replace)** - Paste the name table from clipboard as new.

        This replaces any existing dictionary with the new one you paste. If you paste something, which is not a dictionary, it will just remove the stored data from the object.

    * **Paste name table (Update)** - Paste the name table from clipboard adding to existing.

        This is similar to previous, but it does not clear existing dictionary, but updates it with the new data. If the new data contains a new mapping for already existing original name, it will replace this entry.

    * **Paste as Regular Expressions** - Create name table for selected bones from pasted (pattern, repl) pairs (tab-delimited) for re.sub().

        This is a shortcut to edit names in-place, not using an external editor 'find and replace' tools. You just enter one or more pairs of regular expression pattern, and the substitute, copy them to the clipboard, then select needed bones (generally, all bones), and execute this command.

        Say, you have bones named like `Left_Foot`, `Right_Foot`, which is not good if you try to paste flipped keyframes (blender can't understand this naming as left and right symmetrical names). In this case you'd want to rename them all to become like `Foot.L`, `Foot.R`. For such renaming you'd use something like
        ```
        (?i)(left_)(.*)<tab>\2.L
        (?i)(right_)(.*)<tab>\2.R
        ```
        , where `<tab>` means a character (`"\t"` or `0x09`);
        `(?i)` means *case insensitive*;
        `(left_)` and `(right_)` are groups, you wish to match;
        `(.*)` is part, which remains unchanged;
        `\2` means second matched group (in this case, unchanged part);
        `.L` and `.R` are suffixes, you add to unchanged part.
        >Note the `<tab>` character between `"(?i)(left_)(.*)"` and `"\2.L"`. It separates the **pattern** and the **replace** part.
        >In case you want to delete some part of the name, for example you want `mixamorig:head` to become just `head`, you give only the first part (**pattern**), and a `<tab>` character, followed by a `newline`. And this will be understood as an empty **replace**. Be sure to include a `<tab>` though.
        E.g. `mixamorig:<tab><lf>`.

        This command replaces the stored dictionary with the search and replace result. It works on **selected bones only**.
        Each given (**pattern**, **replace**) part is applied to each bone name in order they are given, and if that final result differs from the original bone name, it's included in the final dictionary.
        >This command as well as both `Copy ..` commands, shows the resulting dictionary in the console for convenience.

### Installation ###

The add-on consists of one single file `bone_renamer.py`.

You can install it in two ways:

  1. open in blender's text editor, and run (*Text => Run Script <Ctrl+P>*) (this will install the add-on for the current session only);

  2. use the standard installation procedure with the 'Install from file' button in the 'Add-ons' section of the 'Preferences' dialog (this type of installation is permanent);

        >If your blender version is far from 2.80, it may warn you about versions mismatch - don't worry, it's deliberately contrived this way. If you're able to enable the add-on with the checkbox, this warning is about nothing at all.

### Uninstallation ###

You can disable or remove the add-on in the 'Add-ons' section of the 'Preferences' dialog.

>With the add-on disabled or removed, your existing bone name dictionaries do still exist in .blend files, and would be accessed again when you enable or re-install the add-on.

### Compatibility ###

It was tested in:
- v2.76b (windows 64 bit);
- v2.79b (windows 64 bit);
- v4.0.2 (windows 64 bit);

In other versions of blender this will probably work, but be prepared for surprises.

### Feedback ###

Feel free to comment, fork and pull request, or create an issue.
It might not be super fast, but I'll definitely will track those things.
