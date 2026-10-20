"""Render Blender evidence and film frames. No frontend or browser automation.
blender -b pisa-tower.blend --python scripts/render.py -- quick|stills|video|explode
"""
from pathlib import Path
import bpy,sys,json,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose
SC=bpy.data.scenes['PISA_TOWER'];bpy.context.window.scene=SC
PARTS=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'stills'
PRE=ROOT/'previews';PRE.mkdir(exist_ok=True)
for p in PARTS:bpy.data.objects[p['node_name']].animation_data_clear()
for action in list(bpy.data.actions):
    if action.name.startswith(('BUILD_ASSEMBLY_','BUILD_EXPLODE_')) and action.users==0:bpy.data.actions.remove(action)

def progress(frame,clip='BUILD_ASSEMBLY'):
    SC.frame_set(frame)
    for p in PARTS:
        ob=bpy.data.objects[p['node_name']];loc,scale,yaw=pose(p,frame/30,clip);ob.location=loc;ob.scale=scale;ob.rotation_euler=(0,0,yaw)

def lighting(mode):
    # Explicit artistic lighting rigs; these are not ephemeris calculations.
    specs={'day':(48,3.0,(.36,.49,.68),.45,-.4),'sunset':(7,2.2,(.37,.30,.27),.32,-.25),'blue':(-4,0,(.07,.13,.27),.3,.5),'night':(-15,0,(.012,.026,.067),.32,.8)}
    elev,energy,color,ambient,exposure=specs[mode];bg=next(n for n in SC.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(*color,1);bg.inputs[1].default_value=ambient
    sun=bpy.data.objects['PISA_Sun'];sun.data.energy=energy;sun.data.color=(1,.59,.29) if mode=='sunset' else (1,.94,.82);sun.rotation_euler=(math.pi/2-math.radians(elev),0,math.radians(-60));sun.data.angle=math.radians(1.5)
    world=SC.world.node_tree
    for link in list(bg.inputs[0].links):world.links.remove(link)
    if mode in ['day','sunset']:
        sky=next((n for n in world.nodes if n.type=='TEX_SKY'),None) or world.nodes.new('ShaderNodeTexSky')
        available=[i.identifier for i in sky.bl_rna.properties['sky_type'].enum_items]
        if 'NISHITA' in available:sky.sky_type='NISHITA'
        sky.sun_elevation=math.radians(elev);sky.sun_rotation=math.radians(-60);sky.sun_disc=False
        world.links.new(sky.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.16 if mode=='day' else .2
    night=mode in ['blue','night']
    bpy.data.objects['PISA_TowerFlood'].data.energy=22000 if night else 1000
    bpy.data.objects['PISA_Rim'].data.energy=14000 if night else 15000
    bpy.data.objects['PISA_Fill'].data.energy=5000 if night else 8000
    for name in ['ivory','ochre','rose','cream','WarmLight']:
        m=bpy.data.materials['PISA_'+name];bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Emission Strength'].default_value=(1.8 if night else .15 if mode=='sunset' else 0) if name!='WarmLight' else (3 if night else .05)
    SC.view_settings.exposure=exposure
    SC.render.film_transparent=False;SC.eevee.use_raytracing=False

def render(name,cam='hero',light='day',frame=840,size=(1800,1350),clip='BUILD_ASSEMBLY'):
    progress(frame,clip);lighting(light);SC.camera=bpy.data.objects['PISA_CAM_'+cam]
    if clip=='BUILD_EXPLODE':
        # Accommodate the measured 100 m exploded envelope.
        SC.camera=bpy.data.objects['PISA_CAM_assembly'];SC.camera.location=(-155,-210,110);SC.camera.data.lens=42;SC.camera.rotation_euler=(Vector((0,0,48))-SC.camera.location).to_track_quat('-Z','Y').to_euler()
    SC.render.resolution_x=size[0];SC.render.resolution_y=size[1];SC.render.resolution_percentage=100;SC.render.image_settings.file_format='PNG';SC.render.filepath=str(PRE/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)

if MODE=='quick':render('draft-day',size=(1000,750))
elif MODE=='cycles':
    SC.render.engine='CYCLES';SC.cycles.samples=32;SC.cycles.use_denoising=True;SC.cycles.max_bounces=6
    render('beauty-day',size=(1600,1200))
    render('beauty-night',light='night',size=(1600,1200))
elif MODE=='stills':
    SC.eevee.taa_render_samples=64
    for light in ['day','sunset','blue','night']:render(light,light=light)
    for cam in ['low','rear','detail','aerial','district']:render(cam,cam=cam)
    for f in [0,30,150,210,420,630,720,840]:render('assembly-%03d'%f,cam='assembly',light='sunset',frame=f,size=(1200,900))
    for f in [0,90,180,270,360]:render('explode-%03d'%f,cam='assembly',light='day',frame=f,size=(1200,900),clip='BUILD_EXPLODE')
elif MODE=='repairs':
    for name,loc,target,lens in [('low',(-42,-72,7),(-2,0,28),30),('rear',(75,-110,45),(-2,0,28),48)]:
        o=bpy.data.objects['PISA_CAM_'+name];o.location=loc;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();render(name,cam=name)
    for f in [0,90,180,270,360]:render('explode-%03d'%f,cam='assembly',light='day',frame=f,size=(1200,900),clip='BUILD_EXPLODE')
elif MODE=='clearance':
    for f in [150,210,420]:render('assembly-%03d'%f,cam='assembly',light='sunset',frame=f,size=(1200,900))
elif MODE in ['video','explode']:
    clip='BUILD_ASSEMBLY' if MODE=='video' else 'BUILD_EXPLODE';end=840 if MODE=='video' else 360
    lighting('sunset' if MODE=='video' else 'blue');SC.eevee.taa_render_samples=12
    SC.render.resolution_x=960;SC.render.resolution_y=720;SC.render.resolution_percentage=100;SC.render.image_settings.file_format='PNG'
    folder=PRE/'frames'/MODE;folder.mkdir(parents=True,exist_ok=True)
    cam=bpy.data.objects['PISA_CAM_assembly'];SC.camera=cam
    if MODE=='explode':cam.location=(-155,-210,110);cam.data.lens=42;cam.rotation_euler=(Vector((0,0,48))-cam.location).to_track_quat('-Z','Y').to_euler()
    for f in range(0,end+1,3):
        progress(f,clip)
        # Slow orbital dolly in the final hold; clear side view for earlier arrivals.
        if MODE=='video' and f>=720:
            u=(f-720)/120;h=u*u*(3-2*u);a=-2.18+h*.4;r=210-65*h;cam.location=(r*math.cos(a),r*math.sin(a),82-38*h);cam.rotation_euler=(Vector((-1,0,30-2*h))-cam.location).to_track_quat('-Z','Y').to_euler()
        SC.render.filepath=str(folder/('%04d.png'%(f//3)))
        if not Path(SC.render.filepath).exists():bpy.ops.render.render(write_still=True)
        if f%30==0:print('VIDEO_FRAME',f,flush=True)
