"""Present the saved source cleanly; preserve its mesh and animation data."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['WANGJING_SOHO'];bpy.context.window.scene=scene;scene.frame_set(900)
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.overlay.show_overlays=False;space.shading.color_type='MATERIAL';space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wangjing-soho.blend'),compress=True)
(ROOT/'verification'/'source.json').write_text(json.dumps(dict(blender=bpy.app.version_string,scene=scene.name,objects=len(scene.objects),fps=scene.render.fps,frames=[scene.frame_start,scene.frame_end],packed_images=sum(bool(im.packed_file) for im in bpy.data.images),preview_collection='WJ_PREVIEW_ONLY',current_frame=scene.frame_current,actual_actions=len([a for a in bpy.data.actions if a.name.startswith('BUILD_ASSEMBLY_')])),indent=2))
