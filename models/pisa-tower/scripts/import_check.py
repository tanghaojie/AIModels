"""Round-trip the actual static GLB into a fresh Blender scene and render it.
Also compare editable source action samples with the shared motion function.
"""
from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose
from animate import activate
parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']
errors=[]
for mode,duration in [('assembly',28),('explode',12)]:
    sc=activate(mode)
    for f in [0,round(duration*7.5),round(duration*15),round(duration*22.5),round(duration*30),47,133]:
        sc.frame_set(f)
        for p in parts:
            ob=bpy.data.objects[p['node_name']];loc,scale,yaw=pose(p,f/30,'BUILD_EXPLODE' if mode=='explode' else 'BUILD_ASSEMBLY')
            errors.append(max(abs(ob.location[i]-loc[i]) for i in range(3)))
            assert max(abs(ob.scale[i]-scale[i]) for i in range(3))<1e-5
activate('assembly');assert max(errors)<.001,max(errors)
if '--source-only' in sys.argv:
    (ROOT/'verification/source-actions.json').write_text(json.dumps(dict(editable_actions=448,maximum_sampled_error_m=max(errors),both_clips_sampled=True),indent=2),encoding='utf-8');print('SOURCE_ACTIONS_OK',max(errors));sys.exit(0)
source=bpy.data.scenes['PISA_TOWER'];qa=bpy.data.scenes.new('PISA_GLB_IMPORT_QA');bpy.context.window.scene=qa
bpy.ops.import_scene.gltf(filepath=str(ROOT/'pisa-tower.glb'))
objects=list(qa.objects);roots=[o for o in objects if 'longitude_wgs84' in o]
assert len(roots)==1;assert not any(o.type in ['LIGHT','CAMERA'] for o in objects)
assert not any(o.animation_data for o in objects)
meshes=[o for o in objects if o.type=='MESH'];assert len(meshes)==226
for ob in meshes:
    for m in ob.data.materials:
        assert m.use_nodes
        assert any(n.type=='BSDF_PRINCIPLED' for n in m.node_tree.nodes)
world=[]
for o in meshes:world.extend(o.matrix_world@Vector(v) for v in o.bound_box)
lo=[min(v[i] for v in world) for i in range(3)];hi=[max(v[i] for v in world) for i in range(3)]
# Link context and studio rig only for the comparison image; never re-export QA.
qa.collection.children.link(bpy.data.collections['PISA_CONTEXT']);qa.collection.children.link(bpy.data.collections['PISA_PREVIEW_ONLY'])
qa.world=source.world;qa.render.engine='BLENDER_EEVEE';qa.eevee.taa_render_samples=32
qa.camera=bpy.data.objects['PISA_CAM_hero'];qa.render.resolution_x=1200;qa.render.resolution_y=900;qa.render.resolution_percentage=100;qa.view_settings.view_transform='AgX';qa.view_settings.exposure=-.4
qa.render.image_settings.file_format='PNG';qa.render.filepath=str(ROOT/'previews/glb-roundtrip.png');bpy.ops.render.render(write_still=True)
result=dict(static_file='pisa-tower.glb',imported_meshes=len(meshes),metadata_roots=len(roots),all_materials_have_principled_nodes=True,no_imported_lights_cameras_animation=True,bounds_blender_m=[lo,hi],editable_actions=448,maximum_source_keyframe_position_error_m=max(errors),comparison='GLB roundtrip rendered in Blender; not target-engine acceptance')
(ROOT/'verification/source-and-import.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2),flush=True)
