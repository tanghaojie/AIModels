"""Switch the editable source to either performance in Blender.

blender --background burj-khalifa.blend --python scripts/animate.py -- explode output.blend
When run from Blender's text editor, defaults to assembly without saving.
"""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import build_model as build
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'assembly';assert mode in ['assembly','explode']
build.SC=bpy.data.scenes['BURJ_KHALIFA'];bpy.context.window.scene=build.SC
build.PARTS=json.loads((ROOT/'parts.json').read_text())['parts'];build.MOVING=[bpy.data.objects[p['node_name']] for p in build.PARTS]
build.bake('BUILD_ASSEMBLY' if mode=='assembly' else 'BUILD_EXPLODE')
build.SC.frame_end=1080 if mode=='assembly' else 420;build.SC.frame_set(build.SC.frame_end)
if len(args)>1:bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1]).resolve()),compress=True)
print('SOURCE_ANIMATION',mode,'frames',build.SC.frame_end,flush=True)
