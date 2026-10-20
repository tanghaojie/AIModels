"""Apply measured neighbouring-roof clearance repairs without re-authoring geometry."""
from pathlib import Path
import bpy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import gltf
import build_model as builder
from animate import activate
cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8'));data=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))
for p in data['parts']:
    if p['part_id'] in cfg['clearance_part_ids'] and not p.get('clearance_height_m'):
        p['start_s']=max(1,p['start_s']-.5);p['assembly']['start_s']=p['start_s'];p['spawn_blender'][2]=cfg['clearance_height_m'];p['assembly']['spawn_translation_m']=gltf(p['spawn_blender']);p['clearance_height_m']=cfg['clearance_height_m'];base=p['assembled_blender'];p['assembly']['waypoints_m']=[gltf([base[0],base[1],p['spawn_blender'][2]])]
(ROOT/'parts.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for p in data['parts']:bpy.data.objects[p['node_name']].animation_data_clear()
for a in list(bpy.data.actions):
    if a.name.startswith('BUILD_ASSEMBLY_'):bpy.data.actions.remove(a)
builder.PARTS=data['parts'];builder.bake('BUILD_ASSEMBLY',28)
for a in bpy.data.actions:
    if a.name.startswith(('BUILD_ASSEMBLY_','BUILD_EXPLODE_')):a.use_fake_user=True
activate('assembly');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'pisa-tower.blend'),compress=True)
print('CLEARANCE_REPAIRED',len(cfg['clearance_part_ids']),flush=True)
