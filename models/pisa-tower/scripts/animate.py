"""Switch all editable source actions together; no accumulated state or clock change.
blender -b pisa-tower.blend --python scripts/animate.py -- assembly|explode
Output: pisa-tower-<mode>.blend (optional working copy; not catalog resources).
"""
from pathlib import Path
import bpy,json,sys
ROOT=Path(__file__).resolve().parents[1]

def activate(mode):
    name='BUILD_EXPLODE' if mode=='explode' else 'BUILD_ASSEMBLY'
    sc=bpy.data.scenes['PISA_TOWER'];bpy.context.window.scene=sc
    for p in json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']:
        ob=bpy.data.objects[p['node_name']];a=bpy.data.actions.get(name+'_'+p['part_id']);assert a
        ob.animation_data_create();ob.animation_data.action=a
        ob.animation_data.action_slot=a.slots[0]
    sc.frame_start=0;sc.frame_end=360 if mode=='explode' else 840;sc.frame_set(sc.frame_end)
    sc.camera=bpy.data.objects['PISA_CAM_explode' if mode=='explode' else 'PISA_CAM_hero']
    return sc

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'assembly';assert mode in ['assembly','explode']
    activate(mode);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('pisa-tower-'+mode+'.blend')),compress=True)
