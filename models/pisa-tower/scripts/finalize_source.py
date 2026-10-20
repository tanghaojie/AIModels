"""Retain both editable action sets and a neutral opening view, without changing meshes."""
from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import build_model as builder
from animate import activate
builder.PARTS=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']
sc=bpy.data.scenes['PISA_TOWER'];bpy.context.window.scene=sc
for a in bpy.data.actions:
    if a.name.startswith('BUILD_ASSEMBLY_'):a.use_fake_user=True
if not bpy.data.actions.get('BUILD_EXPLODE_foundation_ring'):builder.bake('BUILD_EXPLODE',12)
for a in bpy.data.actions:
    if a.name.startswith('BUILD_EXPLODE_'):a.use_fake_user=True
if not bpy.data.objects.get('PISA_CAM_explode'):
    d=bpy.data.cameras.new('PISA_CAM_explode');o=bpy.data.objects.new(d.name,d);bpy.data.collections['PISA_PREVIEW_ONLY'].objects.link(o);o.location=(-155,-210,110);d.lens=42;d.clip_end=10000;o.rotation_euler=(Vector((0,0,48))-o.location).to_track_quat('-Z','Y').to_euler()
activate('assembly')
for name,loc,target,lens in [('low',(-42,-72,7),(-2,0,28),30),('rear',(75,-110,45),(-2,0,28),48)]:
    o=bpy.data.objects['PISA_CAM_'+name];o.location=loc;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
sun=bpy.data.objects['PISA_Sun'];sun.rotation_euler=(math.radians(42),0,math.radians(-60));sun.data.energy=3;sun.data.color=(1,.94,.82)
for name,energy in [('Fill',8000),('Rim',15000),('TowerFlood',1000)]:bpy.data.objects['PISA_'+name].data.energy=energy
bg=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.36,.49,.68,1);bg.inputs[1].default_value=.45
sc.view_settings.exposure=-.4
for im in bpy.data.images:
    if im.packed_file:im.filepath='//textures/'+Path(im.filepath).name
for ar in bpy.context.screen.areas:
    if ar.type=='VIEW_3D':
        ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.overlay.show_overlays=False
        ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.shading.use_scene_world=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'pisa-tower.blend'),compress=True)
print('EDITABLE_ACTIONS',len([a for a in bpy.data.actions if a.name.startswith(('BUILD_ASSEMBLY_','BUILD_EXPLODE_'))]),flush=True)
