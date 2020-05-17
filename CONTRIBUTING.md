# How to contribute to Mr. Mannequins Tools

## Did you find a bug?

* **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/Jim-Kroovy/Mr-Mannequins-Tools/issues).

* If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/Jim-Kroovy/Mr-Mannequins-Tools/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and a **test file** demonstrating the problem if possible.

## Did you write a patch that fixes a bug?

* Open a [new GitHub pull request](https://github.com/Jim-Kroovy/Mr-Mannequins-Tools/pulls) with the patch.

* Ensure the PR description clearly describes the problem and solution. Include the relevant issue number if applicable.

## Do you intend to add a new feature or change an existing one?

* Suggest your change in [Discord](https://discord.gg/wkPZJaH) and start writing code.

* Do not open an issue on GitHub until you have collected positive feedback about the change. GitHub issues are primarily intended for bug reports and fixes.

## Would you like to donate?

If you'd like to financially support development of Mr. Mannequins Tools, you can donate
on [Gumroad](https://gumroad.com/jimkroovy) or subscribe on [Patreon](https://patreon.com/JimKroovy).


## Do you want to hack on the source?

* **Clone Mr Mannequins Tools** to your [Blender addons directory](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html). Note that the name of the folder in addons must be *MrMannequinsTools* exactly, as that name is used to read/write preferences. Example setup with Windows using Powershell:

```powershell
cd "$env:APPDATA\Blender Foundation\Blender\2.81\scripts\addons"
git clone https://github.com/Jim-Kroovy/Mr-Mannequins-Tools.git MrMannequinsTools
```
(You must also extract the MMT_Stash folder from the most recent release .zip and place it within the MrMannequinsTools folder)

At this point, you can enable the addon in Blender Preferences.

* **Modify Python sources and run the [Reload Script](https://docs.blender.org/api/current/bpy.ops.script.html#bpy.ops.script.reload)** operator to see those changes take effect. You can find *Reload Script* using Blender's [Operator Search](https://docs.blender.org/manual/en/latest/interface/controls/templates/operator_search.html) or you can bind *Reload Script* to a key (e.g. `F8`) by adding a [Keymap](https://docs.blender.org/manual/en/latest/editors/preferences/keymap.html)
to the *Window* section and binding to the `script.reload` operator.
