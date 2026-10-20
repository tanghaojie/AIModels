"""Render Blender evidence. Modes: quick, stills, stages, video, explodevideo."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose
SC=bpy.data.scenes['BURJ_KHALIFA'];bpy.context.window.scene=SC
PARTS=json.loads((ROOT/'parts.json').read_text())['parts'];PRE=ROOT/'previews'
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'stills'
for p in PARTS:bpy.data.objects[p['node_name']].animation_data_clear()
for action in list(bpy.data.actions):
    if action.name.startswith('BUILD_') and action.users==0:bpy.data.actions.remove(action)
def progress(frame,clip='BUILD_ASSEMBLY'):
    SC.frame_set(frame)
    for p in PARTS:
        ob=bpy.data.objects[p['node_name']];loc,scale,yaw=pose(p,frame/30,clip);ob.location=loc;ob.scale=scale;ob.rotation_euler=(0,0,yaw)
def light(mode):
    spec={'day':(43,245,2.8,.19,-.1),'sunset':(6,250,2.1,.12,.1),'blue':(-4,235,.035,.28,.7),'night':(-18,250,0,.13,1.0)}
    elev,rot,energy,strength,exposure=spec[mode]
    nodes=SC.world.node_tree.nodes;bg=next(n for n in nodes if n.type=='BACKGROUND')
    sky=next((n for n in nodes if n.type=='TEX_SKY'),None)
    if not sky:sky=nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING'
    sky.sun_elevation=math.radians(elev);sky.sun_rotation=math.radians(rot);sky.sun_disc=False
    for link in list(bg.inputs[0].links):SC.world.node_tree.links.remove(link)
    if mode in ['day','sunset']:SC.world.node_tree.links.new(sky.outputs[0],bg.inputs[0])
    else:bg.inputs[0].default_value=(.038,.073,.16,1)
    bg.inputs[1].default_value=strength
    sun=bpy.data.objects['BK_Sun'];sun.rotation_euler=(math.pi/2-math.radians(elev),0,math.radians(rot));sun.data.energy=energy;sun.data.color=(1,.65,.34) if mode=='sunset' else (1,.95,.86)
    bpy.data.objects['BK_Softbox'].data.energy=4000000 if mode in ['blue','night'] else 1000000
    bpy.data.objects['BK_Softbox'].data.color=(.48,.66,1) if mode in ['blue','night'] else (.82,.9,1)
    bpy.data.objects['BK_Rim'].data.energy=3500000 if mode in ['blue','night'] else 1800000
    bpy.data.objects['BK_Rim'].data.color=(1,.7,.43)
    for m in bpy.data.materials:
        if not m.name.startswith('BK_') or not m.use_nodes:continue
        bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if not bs:continue
        if m.name=='BK_Glazing' or m.name.endswith('_facade'):bs.inputs['Emission Strength'].default_value=0 if mode=='day' else .2 if mode=='sunset' else 1.3 if m.name=='BK_Glazing' else .6
        elif m.name=='BK_Warm_light':bs.inputs['Emission Strength'].default_value=.05 if mode=='day' else 3
    SC.view_settings.exposure=exposure
def render(name,cam='hero',lighting='day',frame=1080,clip='BUILD_ASSEMBLY',size=(1500,1800)):
    progress(frame,clip);light(lighting);SC.camera=bpy.data.objects['CAM_'+cam];SC.render.resolution_x=size[0];SC.render.resolution_y=size[1];SC.render.resolution_percentage=100;SC.render.image_settings.file_format='PNG';SC.render.filepath=str(PRE/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
if MODE=='quick':
    SC.eevee.taa_render_samples=16
    cam=bpy.data.objects['CAM_hero'];cam.location=(-220,-600,240);cam.rotation_euler=(Vector((0,0,385))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24
    render('draft-day-v3',size=(1000,1200))
elif MODE=='stills':
    for mode in ['day','sunset','blue','night']:render(mode,lighting=mode)
    for cam in ['entry','rear','aerial','detail','district']:render(cam,cam=cam,size=(1800,1400) if cam!='rear' else (1500,1800))
elif MODE=='beauty':
    SC.render.engine='CYCLES';SC.cycles.samples=64;SC.cycles.use_denoising=True;SC.cycles.max_bounces=6
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type!='CPU'
        SC.cycles.device='GPU'
    except Exception:SC.cycles.device='CPU'
    render('beauty-sunset',lighting='sunset',size=(1800,2160))
elif MODE=='stages':
    for f in [0,90,180,270,450,540,720,750,810,885,960,1080]:render('assembly-%04d'%f,cam='assembly',lighting='day',frame=f,size=(1280,960))
    for f in [0,105,210,315,420]:render('explode-%04d'%f,cam='explode',frame=f,clip='BUILD_EXPLODE',size=(1280,960))
elif MODE in ['video','explodevideo']:
    clip='BUILD_ASSEMBLY' if MODE=='video' else 'BUILD_EXPLODE';end=1080 if MODE=='video' else 420
    cam=bpy.data.objects['CAM_assembly' if MODE=='video' else 'CAM_explode'];light('day');SC.camera=cam;SC.render.resolution_x=1280;SC.render.resolution_y=960;SC.render.resolution_percentage=100;SC.eevee.taa_render_samples=16;SC.eevee.use_raytracing=False
    folder=PRE/'frames'/('assembly' if MODE=='video' else 'explode');folder.mkdir(parents=True,exist_ok=True);SC.render.image_settings.file_format='PNG'
    # 15 fps review movie retains the true 36/14 second clip timing.
    for f in range(0,end,2):
        progress(f,clip);SC.render.filepath=str(folder/('%04d.png'%(f//2)))
        if not Path(SC.render.filepath).exists():bpy.ops.render.render(write_still=True)
        if f%30==0:print('VIDEO_FRAME',f,flush=True)
