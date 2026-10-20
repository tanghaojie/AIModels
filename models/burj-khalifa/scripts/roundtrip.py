"""Import final static GLBs with Blender's actual importer and inspect assets."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];report=[]
for path in [ROOT/'burj-khalifa.glb',ROOT.parents[1]/'model-assets'/'geo-context'/'burj-khalifa-2000-v1'/'district.glb']:
    # Only create new scenes; no deletion of pre-existing scene contents.
    sc=bpy.data.scenes.new('BK_ROUNDTRIP_'+path.stem);bpy.context.window.scene=sc
    bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
    meshes=[o for o in sc.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
    assert meshes and all(o.data.uv_layers for o in meshes)
    assert not any(o.type in ['CAMERA','LIGHT'] for o in sc.objects)
    geo=[o for o in sc.objects if 'longitude_wgs84' in o]
    if path.stem=='burj-khalifa':assert len(geo)==1 and abs(bounds[1][2]-828)<.01
    report.append(dict(file=str(path.relative_to(ROOT.parents[1])),blender=bpy.app.version_string,meshes=len(meshes),materials=len({m.name for o in meshes for m in o.data.materials}),all_meshes_have_uv=True,bounds_blender_m=bounds,cameras_or_lights=0,geo_metadata_count=len(geo)))
(ROOT/'verification'/'blender-roundtrip.json').write_text(json.dumps(report,indent=2));print('ROUNDTRIP_PASSED',flush=True)
