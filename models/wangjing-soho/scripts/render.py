"""Render source evidence; no frontend/browser automation. -- [quick|stills|video|explode]."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose
SC=bpy.data.scenes['WANGJING_SOHO'];bpy.context.window.scene=SC
P=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'stills'
PRE=ROOT/'previews';PRE.mkdir(exist_ok=True)
# Render directly from the same deterministic motion function as the GLB. Free the
# editable source's several million F-curve keys in this disposable render process.
for p in P:
    ob=bpy.data.objects[p['node_name']];ob.animation_data_clear()
for action in list(bpy.data.actions):
    if action.name.startswith(('BUILD_ASSEMBLY_','BUILD_EXPLODE_')) and action.users==0:bpy.data.actions.remove(action)
def progress(frame,clip='BUILD_ASSEMBLY'):
    SC.frame_set(frame)
    for p in P:
        ob=bpy.data.objects[p['node_name']];loc,scale,yaw=pose(p,frame/30,clip);ob.location=loc;ob.scale=scale;ob.rotation_euler=(0,0,yaw)
def lighting(mode):
    specs={'day':(35,300,2.5,.12,-.2),'sunset':(6,310,2.2,.065,.1),'blue':(-4,220,.08,.25,1),'night':(-15,240,0,.12,1.4)}
    elev,rot,energy,strength,exp=specs[mode];w=SC.world.node_tree;bg=next(n for n in w.nodes if n.type=='BACKGROUND');sky=next(n for n in w.nodes if n.type=='TEX_SKY')
    for link in list(bg.inputs[0].links):w.links.remove(link)
    if mode in ['day','sunset']:w.links.new(sky.outputs[0],bg.inputs[0])
    else:bg.inputs[0].default_value=(.06,.105,.22,1)
    sky.sun_elevation=math.radians(elev);sky.sun_rotation=math.radians(rot);bg.inputs[1].default_value=strength
    sun=bpy.data.objects['WJ_Sun'];sun.rotation_euler=(math.pi/2-math.radians(elev),0,math.radians(rot));sun.data.energy=energy;sun.data.color=(1,.66,.38) if mode=='sunset' else (1,.95,.88);sun.data.angle=math.radians(1)
    bpy.data.objects['WJ_Softbox'].data.energy=320000 if mode in ['blue','night'] else 18000
    SC.eevee.use_raytracing=True
    for m in bpy.data.materials:
        if not m.name.startswith('WJ_') or not m.use_nodes:continue
        bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if bs and ('Glass_lowE' in m.name or m.name.endswith('_facade')):bs.inputs['Emission Strength'].default_value=0 if mode=='day' else .5 if mode=='sunset' else 2.3
        elif bs and 'Landscape_light' in m.name:bs.inputs['Emission Strength'].default_value=.1 if mode=='day' else 3
    SC.view_settings.exposure=exp
def render(name,camera='hero',light='day',frame=900,size=(1600,1100),clip='BUILD_ASSEMBLY'):
    progress(frame,clip);lighting(light);SC.camera=bpy.data.objects['CAM_'+camera]
    SC.render.resolution_x=size[0];SC.render.resolution_y=size[1];SC.render.resolution_percentage=100;SC.render.image_settings.file_format='PNG';SC.render.filepath=str(PRE/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
if MODE=='quick':render('draft-day',size=(1000,688))
elif MODE=='cyclesquick':
    SC.render.engine='CYCLES';SC.cycles.samples=24;SC.cycles.use_denoising=True;SC.cycles.max_bounces=6
    render('cycles-draft-day',size=(1000,688))
elif MODE=='beauty':
    SC.render.engine='CYCLES';SC.cycles.samples=64;SC.cycles.use_denoising=True;SC.cycles.max_bounces=6
    render('beauty-day',light='day')
elif MODE=='stills':
    for light in ['day','sunset','blue','night']:render(light,light=light)
    for cam in ['low','rear','aerial','detail','district']:render(cam,camera=cam,light='day')
    for frame in [0,120,225,450,600,660,735,810,900]:render('assembly-%03d'%frame,camera='assembly',light='sunset',frame=frame,size=(1280,880))
elif MODE=='explode':
    for frame in [0,90,180,270,360]:render('explode-%03d'%frame,camera='assembly',light='day',frame=frame,size=(1280,880),clip='BUILD_EXPLODE')
elif MODE in ['video','explodevideo']:
    lighting('sunset');SC.camera=bpy.data.objects['CAM_assembly'];SC.render.resolution_x=960;SC.render.resolution_y=660;SC.render.resolution_percentage=100
    SC.eevee.taa_render_samples=8;SC.eevee.use_raytracing=False;SC.render.image_settings.file_format='PNG';folder=PRE/('frames' if MODE=='video' else 'frames-explode');folder.mkdir(exist_ok=True)
    # 10 fps preview, same 30 fps animation timing; reusable source retains 30 fps.
    for f in range(0,900 if MODE=='video' else 360,3):
        progress(f,'BUILD_ASSEMBLY' if MODE=='video' else 'BUILD_EXPLODE');SC.render.filepath=str(folder/('%04d.png'%(f//3)))
        if not Path(SC.render.filepath).exists():bpy.ops.render.render(write_still=True)
        if f%30==0:print('VIDEO_FRAME',f,flush=True)
