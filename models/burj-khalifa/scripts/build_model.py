"""Blender 5.2 architectural source, static export and editable flight animation.

Run in a background Blender process. Only named BK collections/scene replaced.
"""
import bpy,math,json,random,sys,tempfile
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
TEMP=ROOT.parents[1]/'tmp'/'blender-burj';TEMP.mkdir(parents=True,exist_ok=True);tempfile.tempdir=str(TEMP)
from geometry import *
from motion import pose,gltf
CFG=json.loads((ROOT/'config.json').read_text());R=json.loads((ROOT/'recipe.json').read_text(encoding='utf-8'))
OUT=ROOT.parents[1]/'model-assets'/'geo-context'/'burj-khalifa-2000-v1';RNG=random.Random(CFG['seed']);PARTS=[];MOVING=[]
def coll(name):
    c=bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(c)
    c=bpy.data.collections.new(name);SC.collection.children.link(c);return c
def empty(name,collection,parent=None,location=(0,0,0)):
    ob=bpy.data.objects.new(name,None);collection.objects.link(ob);ob.parent=parent;ob.location=location;return ob
def part(name,m,pivot,category,start,end,ex,dependencies=(),zone='tower',level=''):
    node=empty('PART_'+name,ASSET,GEO,pivot);node['part_id']=name
    ob=m.object('MESH_'+name,ASSET,node,pivot);ob.location=(0,0,0)
    a=math.atan2(pivot[1],pivot[0]) if math.hypot(*pivot[:2])>2 else RNG.uniform(0,math.tau)
    distance=RNG.uniform(85,145);spawn=[pivot[0]+math.cos(a)*distance,pivot[1]+math.sin(a)*distance,pivot[2]+120+RNG.uniform(220,360)]
    p=dict(part_id=name,node_name=node.name,parent_node_name='GEO_ROOT',category=category,level=str(level),zone=zone,animated=True,pivot_note='component centroid / installation plane; mesh local to pivot',assembled_blender=list(pivot),explode_blender=list(ex),assembled=dict(translation_m=gltf(pivot),rotation_xyzw=[0,0,0,1],scale=[1,1,1]),explode_offset_m=gltf(ex),start_s=start,end_s=end,spawn_blender=spawn,yaw=RNG.uniform(-.1,.1),assembly=dict(phase=category,order=len(PARTS),start_s=start,end_s=end,spawn_translation_m=gltf(spawn),waypoints_m=[],depends_on=list(dependencies)))
    PARTS.append(p);MOVING.append(node);return name
def sector(p,k):
    angle=math.radians(R['tower']['angle_degrees']);v=[]
    pts=p['points'][:p['rings'][0]]
    for j,a in enumerate(pts):
        b=pts[(j+1)%len(pts)];ph=math.atan2((a[1]+b[1])/2,(a[0]+b[0])/2)
        wing=int(((ph-angle+math.pi/3)%math.tau)/(math.tau/3))
        if wing==k:v.append((j,a,b))
    return v
def ring_band(m,edges,z,height=.22):
    for j,a,b in edges:
        delta=np.array(b)-a;length=np.linalg.norm(delta)
        if length<.01:continue
        inward=np.array([-delta[1],delta[0]])/length*.22;ai=np.array(a)+inward;bi=np.array(b)+inward
        m.quad((*a,z),(*b,z),(*b,z+height),(*a,z+height),'Stainless',smooth=True)
        m.quad((*a,z+height),(*b,z+height),(*bi,z+height),(*ai,z+height),'Stainless')
        m.quad((*bi,z),(*ai,z),(*ai,z+height),(*bi,z+height),'Stainless')
        m.quad((*ai,z),(*bi,z),(*b,z),(*a,z),'Stainless')
def tower():
    floors=R['tower']['floors'];coreids=[]
    for i in range(17):
        z0=i*36.8;z1=min(625.6,(i+1)*36.8);rad=max(5,12-z0*.009);m=Mesh()
        pts=[(rad*math.cos(j*math.tau/6),rad*math.sin(j*math.tau/6)) for j in range(6)]
        p=dict(points=pts,rings=[6],triangles=[[0,j,j+1] for j in range(1,5)])
        m.extrude(p,z0,z1-z0,'Concrete','Concrete',bottom=True)
        # Buttressed corridor walls, schematic; consistent at exposed explosions.
        for k in range(3):
            a=math.radians(R['tower']['angle_degrees']+k*120);length=max(7,35-z0*.045)
            m.box((math.cos(a)*length*.5,math.sin(a)*length*.5,(z0+z1)/2),(length,.6,z1-z0),'Concrete',a)
        coreids.append(part(f'core_{i:02}',m,(0,0,(z0+z1)/2),'core',1+i*.25,2+i*.25,(0,0,18+i*7),coreids[-1:],level=i))
    slabs=[]
    for group in range(0,len(floors),3):
        ff=floors[group:group+3];z0=ff[0]['z0'];z1=ff[-1]['z1'];m=Mesh()
        for f in ff:m.extrude(f,f['z0']+.03,.2,'Slab','Slab',bottom=True)
        idx=min(16,int(z0/36.8));s=4+z0/625.6*11
        sid=part(f'floorpack_{group:03}',m,(0,0,(z0+z1)/2),'floors',s,s+1.1,(0,0,12+z0*.22),[coreids[idx]],level=group);slabs.append(sid)
        for k in range(3):
            m=Mesh();points=[]
            for f in ff:
                za,zb=f['z0'],f['z1'];edges=sector(f,k)
                if zb-za<.7:continue
                for j,a,b in edges:
                    # Metric tiled bay mapping: 1.5 m wide, 3.8 m high.
                    length=math.dist(a,b);cell=(j*11+group*5+k*13)%128;u=(cell%16)/16;v=(cell//16)/8
                    uv=[(u,v),(u+length/24,v),(u+length/24,v+(zb-za-.24)/30.4),(u,v+(zb-za-.24)/30.4)]
                    m.quad((*a,za+.24),(*b,za+.24),(*b,zb),(*a,zb),'Louvre_dark' if f['mechanical'] else 'Glazing',uv,smooth=True)
                ring_band(m,edges,za,.22)
                # Fine stainless reveal 0.52 m above each floor line.
                for j,a,b in edges:m.quad((*a,za+.58),(*b,za+.58),(*b,za+.66),(*a,za+.66),'Aluminium',smooth=True)
                if f['mechanical']:
                    for zz in np.arange(za+.5,zb,.48):
                        for j,a,b in edges:m.quad((*a,zz),(*b,zz),(*b,zz+.09),(*a,zz+.09),'Aluminium',smooth=True)
                # Terrace slab and rail where the next floor recedes. Deck is a
                # closed floor, rail within its own skin part, never floating lights.
                if any(abs(zb-v)<.1 for v in R['tower']['setbacks_m']):
                    m.poly(f,zb-.09,'Roof');rail=[]
                    for j,a,b in edges:
                        tube(m,[(*a,zb+.16),(*a,zb+1.15)],.032,'Stainless',4)
                        tube(m,[(*a,zb+1.15),(*b,zb+1.15)],.04,'Stainless',4)
            # Continuous geometric mullions across the three-floor installation.
            for j,a,b in sector(ff[0],k):
                if j%3==0:tube(m,[(*a,z0+.25),(*a,z1-.08)],.058,'Stainless',4)
            if not m.f:continue
            a=math.radians(R['tower']['angle_degrees']+k*120);pv=(math.cos(a)*20,math.sin(a)*20,(z0+z1)/2)
            s=9+z0/625.6*13+k*.12
            part(f'wing_{k}_skin_{group:03}',m,pv,'facade',s,s+1.3,(math.cos(a)*65,math.sin(a)*65,18+z0*.22),[sid],zone=f'wing_{k}',level=group)
    # The steel crown progressively resolves from the tri-lobed body to a slim
    # telescoping mast. It is deliberately not a cone or a single oversized spike.
    crown=[(625.6,641,9.8,9.2),(641,658,9.2,8.5),(658,674,8.5,7.8),(674,690,7.8,6.8),(690,706,6.8,5.6),(706,723,5.6,4.4),(723,739,4.4,3.2),(739,759,3.2,2.2),(759,780,2.2,1.65),(780,801,1.65,1.0),(801,818,1.0,.6),(818,828,.6,.22)]
    previous=[]
    for i,(za,zb,r0,r1) in enumerate(crown):
        m=Mesh();n=36
        # Above 625 m the crown is visibly asymmetric in photographs.
        shift=(1.6*math.cos(i*1.5),1.6*math.sin(i*1.5)) if i<6 else (0,0)
        A=[(r0*math.cos(j*math.tau/n)+shift[0],r0*math.sin(j*math.tau/n)+shift[1],za) for j in range(n)]
        B=[(r1*math.cos(j*math.tau/n)+shift[0],r1*math.sin(j*math.tau/n)+shift[1],zb) for j in range(n)]
        for j in range(n):
            k=(j+1)%n;m.quad(A[j],A[k],B[k],B[j],'Glazing' if i<6 else 'Stainless',[(j/16,za/30.4),((j+1)/16,za/30.4),((j+1)/16,zb/30.4),(j/16,zb/30.4)],True)
            if j%3==0:tube(m,[A[j],B[j]],.055 if i<6 else .025,'Stainless',4)
        m.face(A[::-1],'Steel');m.face(B,'Stainless')
        for zz in np.arange(za,zb,3.8 if i<6 else 7):
            r=r0+(r1-r0)*(zz-za)/(zb-za);p=[(r*math.cos(j*math.tau/n)+shift[0],r*math.sin(j*math.tau/n)+shift[1],zz) for j in range(n)];tube(m,p+[p[0]],.075,'Stainless',4)
        if i in [3,6,8]:
            for a in [0,math.pi/2,math.pi,math.pi*1.5]:tube(m,[(math.cos(a)*r0,math.sin(a)*r0,za),(math.cos(a)*(r0+2),math.sin(a)*(r0+2),za+4)],.09,'Steel',6)
        st=22+i*.11;name=part(f'crown_{i:02}',m,(0,0,(za+zb)/2),'crown',st,st+1.1,(0,0,150+i*9),previous or [slabs[-1]],level='crown');previous=[name]
    # Three glazed entrance pavilions, shallow petal canopies and column rows.
    for k in range(3):
        a=math.radians(R['tower']['angle_degrees']+k*120+60);c=Vector((math.cos(a)*47,math.sin(a)*47,0));m=Mesh()
        for j in range(48):
            ph=j*math.tau/48;ph1=(j+1)*math.tau/48
            def pt(t,z):
                u,v=25*math.cos(t),14*math.sin(t);return (c.x+u*math.cos(a)-v*math.sin(a),c.y+u*math.sin(a)+v*math.cos(a),z)
            m.quad(pt(ph,0),pt(ph1,0),pt(ph1,8.8),pt(ph,8.8),'Glazing',[(j/16,0),((j+1)/16,0),((j+1)/16,.29),(j/16,.29)],True)
            if j%3==0:tube(m,[pt(ph,0),pt(ph,8.8)],.11,'Stainless',6)
        ring=[pt(j*math.tau/64,9) for j in range(64)];m.face(ring,'Aluminium');tube(m,ring+[ring[0]],.22,'Stainless',6)
        for j in range(8):
            u=(j-3.5)*3;v=12;m.box((c.x+u*math.cos(a)-v*math.sin(a),c.y+u*math.sin(a)+v*math.cos(a),4.5),(.15,.15,9),'Stainless')
        part(f'entry_{k}',m,tuple(c+Vector((0,0,4.5))),'entrance',23+k*.1,24.3+k*.1,(math.cos(a)*90,math.sin(a)*90,10),['core_00'],zone=f'entry_{k}')
def site():
    m=Mesh()
    for p in R['site_ground']:m.extrude(p,-.23,.3,'Concrete','Travertine')
    m.object('SITE_podium',ASSET,GEO)
    plants=Mesh();furniture=Mesh()
    # Interpretive landscape follows the three-fold circulation visible in SOM's
    # overhead photograph. Explicitly approximate, not georeferenced planting.
    for k in range(3):
        angle=math.radians(R['tower']['angle_degrees']+k*120)
        for ring in [0,1]:
            center=Vector((math.cos(angle)*105,math.sin(angle)*105));l=32 if ring==0 else 21;w=15 if ring==0 else 8
            pts=[]
            for j in range(72):
                ph=j*math.tau/72;u=l*math.cos(ph);v=w*math.sin(ph)
                pts.append((center.x+u*math.cos(angle)-v*math.sin(angle),center.y+u*math.sin(angle)+v*math.cos(angle)))
            p=dict(points=pts,rings=[72],triangles=[[0,j,j+1] for j in range(1,71)])
            plants.extrude(p,.09,.25 if ring==0 else .48,'Travertine','Grass' if ring==0 else 'Water')
            tube(furniture,[(*v,.38) for v in pts+[pts[0]]],.075,'Warm_light',5)
        for j in range(10):
            a=angle+(j-4.5)*.10;r=125+(j%2)*10;x,y=r*math.cos(a),r*math.sin(a);palm(plants,x,y,RNG.uniform(7,11),a)
            if j%2==0:
                furniture.box((x*.94,y*.94,.55),(3.8,.8,.38),'Wood',a+math.pi/2)
                tube(furniture,[(x,y,.2),(x,y,4.6)],.055,'Steel',6);furniture.box((x,y,4.65),(1.7,.15,.1),'Warm_light',a)
    # Fine paving inlays and radial arrival paths.
    for r in [76,86,143]:
        pts=[(r*math.cos(j*math.tau/192),r*math.sin(j*math.tau/192),.085) for j in range(193)];tube(furniture,pts,.055,'Dark_stone',4)
    for k in range(24):
        a=k*math.tau/24;tube(furniture,[(77*math.cos(a),77*math.sin(a),.085),(142*math.cos(a),142*math.sin(a),.085)],.035,'Dark_stone',4)
    plants.object('SITE_palms_gardens',ASSET,GEO);furniture.object('SITE_furniture_inlays',ASSET,GEO)
def district():
    meshes={}
    def tile(key):
        key=tuple(key)
        if key not in meshes:meshes[key]=Mesh()
        return meshes[key]
    m=Mesh()
    for p in R['ground']:m.poly(p,-.5,'Sand')
    m.object('CONTEXT_ground',CONTEXT,CTXROOT)
    for p in R['land']:tile((90,90)).poly(p,-.27 if p['kind']=='water' else -.31,'Water' if p['kind']=='water' else 'Grass')
    for p in R['roads']:tile((91,91)).poly(p,-.1 if p['kind'] not in ['footway','path','steps','pedestrian'] else -.075,'Asphalt' if p['kind'] not in ['footway','path','steps','pedestrian'] else 'Travertine')
    for p in R['buildings']:
        m=tile(p['tile']);m.extrude(p,p['min_height']-.015,p['height']-p['min_height'],p['style']+'_facade','Roof',uvscale=12,bottom=p['min_height']>0)
        if str(p['id'])=='reference-dubai-mall':
            # Distinctive rotundas/skylight strips visible in the archived aerial.
            # Their dimensions/placement are illustrative within the traced shell.
            for x,y,r in [(175,-320,32),(325,-440,29),(450,-490,27)]:
                disk(m,(x,y),r,28,2.2,'Travertine',64);disk(m,(x,y),r*.68,30.2,.4,'Glazing',64)
                ring=[(x+r*.72*math.cos(j*math.tau/64),y+r*.72*math.sin(j*math.tau/64),30.8) for j in range(65)];tube(m,ring,.18,'Stainless',5)
            for x,y in [(260,-340),(360,-520),(435,-380)]:
                for j in range(8):m.box((x+(j-3.5)*5,y,29),(2.8,66,1.5),'Aluminium')
        # Source footprint is unchanged. Roof parapets and a few ventilators are
        # illustrative features rather than invented additional buildings.
        if p['height']>30 and len(p['points'])<60:
            pts=p['points'][:p['rings'][0]];c=np.mean(pts,axis=0)
            for a,b in zip(pts,pts[1:]+pts[:1]):tube(m,[(*a,p['height']+.3),(*b,p['height']+.3)],.18,'Concrete',4)
            if math.dist(c,(0,0))<1100:m.box((*c,p['height']+.8),(3,4,1.5),'HVAC')
    for k,m in sorted(meshes.items()):m.object('CONTEXT_%s_%s'%k,CONTEXT,CTXROOT)
    marks=Mesh();cars=Mesh();palms=Mesh()
    for p in R['roads']:
        if p['kind'] not in ['motorway','trunk','primary','secondary','tertiary','residential']:continue
        pts=p['centerline']
        for a,b in zip(pts[:-1],pts[1:]):
            length=math.dist(a,b)
            if length<2:continue
            tangent=(np.array(b)-a)/length;ang=math.atan2(tangent[1],tangent[0])
            for t in np.arange(2,length,11):
                mid=np.array(a)+tangent*t
                if np.linalg.norm(mid)>1950:continue
                marks.box((*mid,-.065),(3,.12,.012),'Marking',ang)
            if length>25 and RNG.random()<.22:
                mid=(np.array(a)+b)/2+np.array([-tangent[1],tangent[0]])*p['width']*.22
                if np.linalg.norm(mid)<1800:
                    cars.box((*mid,.58),(4.4,1.9,1.1),'Car_'+str(RNG.randrange(3)),ang);cars.box((*mid,1.23),(2.1,1.6,.55),'Glazing',ang)
            if length>35 and RNG.random()<.2:
                mid=(np.array(a)+b)/2+np.array([-tangent[1],tangent[0]])*(p['width']/2+3)
                if 165<np.linalg.norm(mid)<1000:palm(palms,*mid,RNG.uniform(6,9),ang)
    marks.object('CONTEXT_lane_markings',CONTEXT,CTXROOT);cars.object('CONTEXT_vehicles',CONTEXT,CTXROOT);palms.object('CONTEXT_street_palms',CONTEXT,CTXROOT)
def camera(name,loc,target,lens=46,ortho=None):
    d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);PREVIEW.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=5;d.clip_end=16000
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return ob
def fit_motion_camera(name,clip):
    cam=bpy.data.objects[name];basis=cam.rotation_euler.to_matrix();inv=basis.transposed();points=[]
    for node,p in zip(MOVING,PARTS):
        corners=[Vector(c) for child in node.children if child.type=='MESH' for c in child.bound_box]
        times=[p['start_s']+(p['end_s']-p['start_s'])*j/10 for j in range(11)]+[27,32,36] if clip=='BUILD_ASSEMBLY' else [0,14]
        for t in times:
            loc,scale,yaw=pose(p,t,clip)
            if scale[0]<.001:continue
            co,si=math.cos(yaw),math.sin(yaw)
            for v in corners:
                w=Vector((v.x*co-v.y*si,v.x*si+v.y*co,v.z))+Vector(loc);q=inv@(w-cam.location);points.append((q.x,q.y))
    pts=np.array(points);lo=pts.min(axis=0);hi=pts.max(axis=0);center=(lo+hi)/2
    cam.location+=basis@Vector((center[0],center[1],0));cam.data.ortho_scale=max((hi[0]-lo[0])*1.12,(hi[1]-lo[1])*4/3*1.12)
def export(collection,path):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in collection.objects:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_texcoords=True,export_normals=True,export_materials='EXPORT')
def bake(clip='BUILD_ASSEMBLY'):
    end=1080 if clip=='BUILD_ASSEMBLY' else 420;frames=np.arange(end+1,dtype=np.float32)
    for node,p in zip(MOVING,PARTS):
        node.animation_data_clear();node.keyframe_insert('location',frame=0,group='Flight');node.keyframe_insert('scale',frame=0,group='Flight');node.keyframe_insert('rotation_euler',frame=0,group='Flight');node.animation_data.action.name=clip+'_'+p['part_id']
        poses=[pose(p,float(f)/30,clip) for f in frames];channels={'location':np.array([x[0] for x in poses]),'scale':np.array([x[1] for x in poses]),'rotation_euler':np.array([[0,0,x[2]] for x in poses])}
        for layer in node.animation_data.action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(node.animation_data.action_slot)
                if bag:
                    for curve in bag.fcurves:
                        curve.keyframe_points.clear();curve.keyframe_points.add(len(frames));curve.keyframe_points.foreach_set('co',np.column_stack((frames,channels[curve.data_path][:,curve.array_index])).astype(np.float32).ravel());val=curve.keyframe_points[0].bl_rna.properties['interpolation'].enum_items['LINEAR'].value;curve.keyframe_points.foreach_set('interpolation',np.full(len(frames),val,dtype=np.int32));curve.update()
def main():
    global SC,ASSET,CONTEXT,PREVIEW,GEO,CTXROOT
    SC=bpy.data.scenes.get('BURJ_KHALIFA')
    if SC:bpy.data.scenes.remove(SC)
    SC=bpy.data.scenes.new('BURJ_KHALIFA');bpy.context.window.scene=SC
    ASSET=coll('BK_ASSET');CONTEXT=coll('BK_CONTEXT');PREVIEW=coll('BK_PREVIEW_ONLY');GEO=empty('GEO_ROOT',ASSET);CTXROOT=empty('DISTRICT_ROOT',CONTEXT)
    MAT.clear();MI.clear()
    for datablocks,prefix in [(bpy.data.materials,'BK_'),(bpy.data.actions,'BUILD_')]:
        for d in list(datablocks):
            if d.name.startswith(prefix) and d.users==0:datablocks.remove(d)
    metadata=dict(geo_metadata_version=1,longitude_wgs84=CFG['anchor'][0],latitude_wgs84=CFG['anchor'][1],horizontal_crs='EPSG:4326',vertical_reference='WGS84_ELLIPSOID',coordinate_source='OpenStreetMap tower footprint and SOM site aerial; 2026-10-20',coordinate_accuracy='approximate',height_source='terrain_at_load',units='meters',local_origin='tower_ground_center',height_m=828)
    for k,v in metadata.items():GEO[k]=v
    SC.unit_settings.system='METRIC';SC.unit_settings.scale_length=1;SC.unit_settings.length_unit='METERS'
    tex=ROOT/'textures'
    material('Glazing',(1,1,1),.23,0,tex/'glazing-base.png',tex/'glazing-emissive.png',1.5,tex/'glazing-orm.png')
    for n,c,r,met,tx in [('Stainless',(.62,.68,.73),.27,1,None),('Aluminium',(.6,.64,.67),.32,1,None),('Steel',(.23,.27,.30),.36,1,None),('Slab',(.18,.21,.22),.84,0,None),('Louvre_dark',(.055,.075,.09),.6,0,None),('Concrete',(.5,.52,.52),.83,0,'concrete-base.png'),('Travertine',(.7,.65,.55),.74,0,'travertine-base.png'),('Dark_stone',(.055,.065,.07),.4,0,None),('Roof',(.37,.39,.38),.82,0,None),('HVAC',(.46,.49,.49),.55,0,None),('Asphalt',(.16,.18,.2),.95,0,'asphalt-base.png'),('Sand',(.5,.42,.3),.95,0,'sand-base.png'),('Grass',(.25,.33,.15),.94,0,'grass-base.png'),('Bark',(.24,.15,.085),.95,0,None),('Palm_leaf',(.18,.25,.08),.8,0,None),('Water',(.015,.17,.18),.18,0,None),('Wood',(.22,.10,.04),.6,0,None),('Marking',(.7,.67,.52),.9,0,None),('Car_0',(.018,.025,.035),.21,0,None),('Car_1',(.7,.68,.61),.24,0,None),('Car_2',(.2,.025,.012),.24,0,None)]:
        material(n,(1,1,1) if tx else c,r,met,tex/tx if tx else None)
    material('Warm_light',(1,.63,.28),.35,0,strength=2.2)
    for st in ['office','residential','concrete']:material(st+'_facade',(1,1,1),.5,0,tex/'district'/(st+'-base.png'),tex/'district'/(st+'-emissive.png'),1.1,tex/'district'/(st+'-orm.png'))
    tower();site();district();print('GEOMETRY_BUILT',len(PARTS),flush=True)
    SC.render.engine='BLENDER_EEVEE';SC.render.resolution_x=1800;SC.render.resolution_y=1400;SC.render.resolution_percentage=100;SC.render.fps=30;SC.frame_start=0;SC.frame_end=1080;SC.view_settings.view_transform='AgX'
    SC.eevee.taa_render_samples=32;SC.eevee.use_raytracing=True
    SC.world=bpy.data.worlds.new('BK_Atmosphere');SC.world.use_nodes=True;nodes=SC.world.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');bg.inputs[0].default_value=(.16,.22,.32,1);bg.inputs[1].default_value=.35;SC.world.node_tree.links.new(bg.outputs[0],output.inputs[0])
    for name,typ,loc,target,energy,size in [('BK_Sun','SUN',(0,0,1200),(0,0,0),3,0),('BK_Softbox','AREA',(-300,-500,650),(0,0,370),1800000,850),('BK_Rim','AREA',(400,250,800),(0,0,430),2200000,600)]:
        ob=bpy.data.objects.new(name,bpy.data.lights.new(name,typ));PREVIEW.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=energy
        if typ=='AREA':ob.data.shape='DISK';ob.data.size=size
        else:ob.data.angle=math.radians(1)
    m=Mesh()
    # Annular preview horizon: no second surface underneath the context/lakes.
    for i in range(256):
        a=i*math.tau/256;b=(i+1)*math.tau/256
        m.quad((2000*math.cos(a),2000*math.sin(a),-.6),(150000*math.cos(a),150000*math.sin(a),-.6),(150000*math.cos(b),150000*math.sin(b),-.6),(2000*math.cos(b),2000*math.sin(b),-.6),'Sand')
    m.object('PREVIEW_horizon',PREVIEW)
    for args in [('hero',(-220,-600,240),(0,0,385),24),('rear',(680,850,620),(0,0,380),32),('low',(-140,-280,20),(0,0,250),17),('detail',(-97,-125,244),(0,0,260),65),('entry',(-110,-160,26),(0,0,22),45),('aerial',(850,-1120,1400),(0,0,260),40),('district',(3200,-3700,4000),(0,0,200),45,4800),('assembly',(-700,-1900,1700),(0,0,510),48,1800),('explode',(-700,-1900,1700),(0,0,510),48,1700)]:camera('CAM_'+args[0],*args[1:])
    fit_motion_camera('CAM_assembly','BUILD_ASSEMBLY');fit_motion_camera('CAM_explode','BUILD_EXPLODE')
    SC.camera=bpy.data.objects['CAM_hero'];(ROOT/'previews').mkdir(exist_ok=True);(ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'placement.json').write_text(json.dumps(metadata,indent=2));(ROOT/'parts.json').write_text(json.dumps(dict(version=1,standard_id='CS-AM-1',coordinate_frame='gltf-local-y-up',units='meters',parts=PARTS),indent=2))
    export(ASSET,ROOT/'burj-khalifa.glb');export(CONTEXT,OUT/'district.glb');bake();SC.frame_set(1080)
    for im in bpy.data.images:
        if im.filepath and str(ROOT) in bpy.path.abspath(im.filepath):im.pack()
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=1900;area.spaces.active.region_3d.view_location=(0,0,400);area.spaces.active.clip_end=20000;area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'burj-khalifa.blend'),compress=True)
    report=dict(blender=bpy.app.version_string,parts=len(PARTS),triangles_asset=sum(len(p.vertices)-2 for ob in ASSET.objects if ob.type=='MESH' for p in ob.data.polygons),triangles_context=sum(len(p.vertices)-2 for ob in CONTEXT.objects if ob.type=='MESH' for p in ob.data.polygons),materials=len(MAT),source_scene='BURJ_KHALIFA',preview_collection='BK_PREVIEW_ONLY')
    (ROOT/'verification'/'build.json').write_text(json.dumps(report,indent=2));print('BUILD_COMPLETE',report,flush=True)
if __name__=='__main__':main()
