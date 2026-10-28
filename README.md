# chameleons

A Blender workflow for blocking out, sculpting, rigging and posing creature
models, packaged as the **Chameleons Tools** add-on (`chameleons_tools/`).
Built for Blender 5.0 and works in 4.2 or newer.

## Install

**For development (recommended):** link the add-on folder into Blender's
extensions folder so edits in this repo show up after a restart:

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\Blender Foundation\Blender\5.0\extensions\user_default\chameleons_tools" -Target "<repo>\chameleons_tools"
```

Then in Blender go to *Edit > Preferences > Add-ons* and enable **Chameleons Tools**.

**As a package:** run `blender --command extension build --source-dir chameleons_tools`,
then use *Preferences > Add-ons > Install from Disk* on the zip it makes.

The tools live in the 3D Viewport sidebar (press `N`) on the **Chameleons** tab.

## Workflow

1. **Block out:** *Add Creature Skeleton* adds `CHM_Skeleton`, an edge mesh wrapped
   in Mirror, Skin and Subdivision modifiers. In Edit Mode, move points to change
   proportions and press `Ctrl+A` to scale a point's thickness. Edit only the left
   side (+X), since the right side is mirrored. Each named joint has a vertex group
   of the same name, and the rig is built from those points, so keep them.
2. **Sculpt:** *Make Sculpt Mesh* bakes the blockout into `CHM_Body`, voxel-remeshes
   it at *Voxel Size*, turns on X symmetry and switches to Sculpt Mode. Use
   *Remesh Body* while working on big forms, then *Add Detail Levels* (Multires)
   for fine detail. Remeshing is blocked once Multires exists, because it would
   erase that detail.
3. **Rig:** *Build Rig* creates `CHM_Rig` from the skeleton's joints:
   - spine, neck and head bones, plus a 5-bone tail
   - IK legs with `hand_ik` / `foot_ik` targets and elbow or knee pole controls
   - a `tail_curl` control
   *Bind Body to Rig* skins the body with automatic weights and warns you if any
   vertices were left without weights.
4. **Pose:** in Pose Mode, move the `*_ik` controls to place the feet and the
   `*_pole` controls to aim the elbows and knees. Rotate `tail_curl` to curl the
   whole tail; each tail bone can still be posed on top of that. *Reset Pose* and
   *Key Whole Pose* are in the panel. Blender's own tools still work alongside
   these: use `Ctrl+C` / `Ctrl+Shift+V` to paste a pose mirrored, and the Asset
   Browser's Pose Library to save poses.

To rig a mesh you made some other way, add the skeleton and line its points up
inside your mesh. Then tag your mesh with the custom property `chm_role = "body"`,
build the rig and bind.
