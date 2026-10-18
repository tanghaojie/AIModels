"""Blender round-trip check of the *exported* assembly GLB, not a browser test."""
import bpy,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose
scene=bpy.data.scenes.new('WJ_EXPORTED_GLB_CHECK');bpy.context.window.scene=scene;scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(ROOT/'wangjing-soho-assembly.glb'))
parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']
samples=[];maximum=0
for frame in [0,30,120,225,450,600,660,735,810,900]:
    scene.frame_set(frame);bpy.context.view_layer.update();error=0
    for p in parts:
        ob=scene.objects[p['node_name']];expected,scale,yaw=pose(p,frame/30)
        # Blender imports glTF Y-up into Z-up. Imported frames must match source metres.
        actual=ob.matrix_world.translation
        error=max(error,max(abs(actual[k]-expected[k]) for k in range(3)))
    maximum=max(maximum,error);samples.append(dict(frame=frame,max_position_error_m=error))
report=dict(blender=bpy.app.version_string,file='wangjing-soho-assembly.glb',imported_nodes=len(scene.objects),samples=samples,max_position_error_m=maximum,passed=maximum<.001)
(ROOT/'verification'/'blender-roundtrip.json').write_text(json.dumps(report,indent=2));print('ROUNDTRIP',json.dumps(report),flush=True)
assert maximum<.001,report
