"""Blender 5.2 architectural asset; reruns replace only PISA_* project data.
Run from any directory: blender --background --factory-startup --python <this file>.
"""
from pathlib import Path
import bpy,math,json,sys,random
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from geometry import Mesh,TAU
from motion import pose,gltf
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
R=json.loads((ROOT/'recipe.json').read_text(encoding='utf-8'))
OUT=ROOT.parents[1]/'model-assets'/'geo-context'/'pisa-1000-v1'
MAT={};PARTS=[];RNG=random.Random(CFG['seed'])

def coll(name):
    c=bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(c)
    c=bpy.data.collections.new(name);SC.collection.children.link(c);return c

def empty(name,c,parent=None,loc=(0,0,0)):
    ob=bpy.data.objects.new(name,None);c.objects.link(ob);ob.parent=parent;ob.location=loc;return ob

def material(name,color,rough=.7,metal=0,tex=None,em=None,strength=0,stone=False):
    old=bpy.data.materials.get('PISA_'+name)
    if old:bpy.data.materials.remove(old,do_unlink=True)
    m=bpy.data.materials.new('PISA_'+name);m.use_nodes=True;m.diffuse_color=(*color,1);m.use_backface_culling=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;bs.inputs['Emission Strength'].default_value=strength
    def image(name,cs='sRGB'):
        im=bpy.data.images.load(str(ROOT/'textures'/name),check_existing=True);im.colorspace_settings.name=cs;n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;return n
    if tex:m.node_tree.links.new(image(tex).outputs['Color'],bs.inputs['Base Color'])
    if stone:
        orm=image('marble-orm.png','Non-Color');sep=m.node_tree.nodes.new('ShaderNodeSeparateColor');m.node_tree.links.new(orm.outputs['Color'],sep.inputs[0]);m.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
        normal=image('marble-normal.png','Non-Color');n=m.node_tree.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.32;m.node_tree.links.new(normal.outputs['Color'],n.inputs['Color']);m.node_tree.links.new(n.outputs[0],bs.inputs['Normal'])
    if em:m.node_tree.links.new(image(em).outputs['Color'],bs.inputs['Emission Color'])
    elif strength:bs.inputs['Emission Color'].default_value=(*color,1)
    MAT[name]=m;return m

def warp(v):
    x,y,z=v
    return (x-math.tan(math.radians(CFG['tilt_degrees']))*z+.00012*max(0,z-22)**2,y,z)

def part(ident,me,level,category,start,end,angle=None,deps=None):
    if not me.f:return
    vs=np.array([warp(v) for v in me.v]);pivot=(vs.min(0)+vs.max(0))/2
    if angle is None:angle=math.atan2(pivot[1],pivot[0])
    # Outward hemispheric flight avoids cutting through the already assembled core.
    distance=36+(len(PARTS)%5)*7;up=12+(len(PARTS)%4)*4
    spawn=pivot+np.array([math.cos(angle)*distance,math.sin(angle)*distance,up])
    clearance=ident in CFG.get('clearance_part_ids',[])
    if clearance:spawn[2]=CFG['clearance_height_m'];start=max(1,start-.5)
    ex=np.array([math.cos(angle)*(8 if category=='core' else 13),math.sin(angle)*(8 if category=='core' else 13),level*5.2+(0 if category=='foundation' else 2)])
    ob=empty('PART_'+ident,ASSET,GEO,pivot);ob['part_id']=ident
    me.object('MESH_'+ident,ASSET,ob,pivot=pivot,warp=warp).location=(0,0,0)
    p=dict(part_id=ident,node_name=ob.name,parent_node_name='GEO_ROOT',category=category,level='L%02d'%level,zone='tower',animated=True,pivot_note='component bounding-box center after southern lean, fixed parent local metres',assembled=dict(translation_m=gltf(pivot.tolist()),rotation_xyzw=[0,0,0,1],scale=[1,1,1]),explode_offset_m=gltf(ex.tolist()),assembly=dict(phase=category,order=len(PARTS),start_s=start,end_s=end,spawn_translation_m=gltf(spawn.tolist()),waypoints_m=[],depends_on=deps or []),assembled_blender=pivot.tolist(),spawn_blender=spawn.tolist(),explode_blender=ex.tolist(),start_s=start,end_s=end,yaw=math.radians((len(PARTS)%5-2)*5),arc_height_m=4)
    PARTS.append(p)
    if clearance:
        p['clearance_height_m']=CFG['clearance_height_m'];p['assembly']['waypoints_m']=[gltf([pivot[0],pivot[1],float(spawn[2])])]

def cornice(me,z,ri=5.72,ro=7.74,start=0,end=TAU,n=48):
    # Multiple real silhouette mouldings instead of a single torus.
    profile=[(ri,0),(ro-.3,0),(ro-.3,.12),(ro-.05,.2),(ro,.33),(ro,.44),(ro-.18,.5),(ro-.18,.63),(ri,.63),(ri,0)]
    me.lathe((0,0,z),profile,'Marble',n,start,end,closed=end-start<TAU-.001)
    count=max(1,round((end-start)*ro/.34))
    for i in range(count):
        a=start+(end-start)*(i+.5)/count;me.box(((ro-.3)*math.cos(a),(ro-.3)*math.sin(a),z+.07),(.18,.24,.17),'Carving',a)

def tower():
    print('BUILD tower',flush=True)
    me=Mesh(MAT);me.ring(3.5,7.9,-.36,.5,'Marble',n=160);part('foundation_ring',me,0,'foundation',1,2.3,angle=-math.pi/2)
    # Thick hollow masonry; basal doorway opens on the southern side.
    for level,(z0,z1,ro) in enumerate([(0,10.78,7.25)]+[(10.78+i*5.82,10.78+(i+1)*5.82,5.92) for i in range(6)]):
        for s in range(8):
            a,b=s*TAU/8,(s+1)*TAU/8;me=Mesh(MAT)
            if level==0 and s in [3,4]:
                # Split geometry around the opening instead of painting a black doorway.
                aa,bb=(a,math.pi-.135) if s==3 else (math.pi+.135,b)
                me.ring(3.68,ro,z0,z1-z0,'Marble',aa,bb,20)
                me.ring(3.68,ro,3.5,z1-3.5,'Marble',math.pi-.135,math.pi,6) if s==3 else me.ring(3.68,ro,3.5,z1-3.5,'Marble',math.pi,math.pi+.135,6)
            else:me.ring(3.68,ro,z0,z1-z0,'Marble',a,b,24)
            # Restrained dark masonry bands, geometry sits proud by 8 mm.
            for zz in np.arange(z0+1.12,z1,.9):me.ring(ro+.008,ro+.022,float(zz),.055,'StoneGrey',a,b,24)
            start=2+level*2.7+s*.045;part('core_%02d_%02d'%(level,s),me,level,'core',start,start+1.1,angle=(a+b)/2,deps=['foundation_ring'])
    # Fifteen engaged columns and blind arches, diamond inlays and concentric archivolts.
    for j in range(15):
        a=j*TAU/15;mid=a+math.pi/15;me=Mesh(MAT)
        me.column((7.23*math.cos(a),7.23*math.sin(a),.5),7.0,'Carving',r=.30)
        c=(7.29*math.cos(mid),7.29*math.sin(mid),.5)
        me.arch(c,2.55,7.0,.33,.22,'Marble',mid+math.pi/2,n=20)
        me.arch((c[0]*1.004,c[1]*1.004,c[2]),2.23,7.0,.35,.12,'StoneGrey',mid+math.pi/2,n=20,spandrel=False)
        # Rhombic marble intarsia below each blind arch.
        rr=7.29;d=.55;z=8.5;rad=Vector((math.cos(mid),math.sin(mid),0));tan=Vector((-math.sin(mid),math.cos(mid),0));o=rad*rr+Vector((0,0,z))
        me.face([o+tan*d,o+Vector((0,0,d)),o-tan*d,o-Vector((0,0,d))],'StoneGrey')
        me.face([o+rad*.014+tan*d*.68,o+rad*.014+Vector((0,0,d*.68)),o+rad*.014-tan*d*.68,o+rad*.014-Vector((0,0,d*.68))],'Carving')
        part('blind_arcade_%02d'%j,me,0,'blind_arcade',3.2+j*.085,4.4+j*.085,angle=mid)
    # Six loggias: thirty columns each, grouped three bays per animated module.
    for level in range(7):
        z=10.78+level*5.82
        for s in range(8):
            me=Mesh(MAT);a,b=s*TAU/8,(s+1)*TAU/8;cornice(me,z,start=a,end=b,n=24)
            st=4.7+level*2.65+s*.035;part('cornice_%02d_%02d'%(level,s),me,level+1,'cornice',st,st+1.2,angle=(a+b)/2)
        if level==6:break
        for group in range(10):
            me=Mesh(MAT)
            for j in range(group*3,group*3+3):
                a=j*TAU/30;b=(j+1)*TAU/30;mid=(a+b)/2
                me.column((7.13*math.cos(a),7.13*math.sin(a),z+.63),3.95,'Carving',r=.205)
                c=(7.13*math.cos(mid),7.13*math.sin(mid),z+.63)
                me.arch(c,1.085,3.95,.5,.19,'Marble',mid+math.pi/2,n=14)
                me.arch((c[0]*1.013,c[1]*1.013,c[2]),1.36,3.95,.14,.065,'Carving',mid+math.pi/2,n=14,spandrel=False)
            st=6.0+level*2.65+group*.06;part('loggia_%02d_%02d'%(level+1,group),me,level+1,'loggia',st,st+1.35,angle=(group*3+1.5)*TAU/30,deps=['core_%02d_00'%(level+1)])
    # A short open terrace supports the smaller bell chamber.
    me=Mesh(MAT);me.ring(3.68,6.05,46.3,1.5,'Marble',n=128);cornice(me,47.8,ri=3.68,ro=6.32,n=128);part('bell_terrace',me,7,'crown',21.0,22.0,angle=-math.pi/2)
    for j in range(12):
        a=j*TAU/12;b=(j+1)*TAU/12;mid=(a+b)/2;me=Mesh(MAT)
        me.column((5.72*math.cos(a),5.72*math.sin(a),48.43),5.15,'Carving',r=.26)
        me.box((5.35*math.cos(a),5.35*math.sin(a),50.95),(.92,.85,5.04),'Marble',a)
        c=(5.72*math.cos(mid),5.72*math.sin(mid),48.43)
        me.arch(c,2.0,5.15,.8,.28,'Marble',mid+math.pi/2,n=20)
        st=21.2+j*.055;part('belfry_bay_%02d'%j,me,8,'belfry',st,st+1.1,angle=mid)
    me=Mesh(MAT);cornice(me,55.25,ri=3.65,ro=6.45,n=144);me.ring(3.65,6.12,55.88,.42,'Marble',n=144)
    for i in range(60):
        a=i*TAU/60;me.box((6.12*math.cos(a),6.12*math.sin(a),56.03),(.15,.23,.42),'Carving',a)
        if i%2==0:me.box((6.2*math.cos(a),6.2*math.sin(a),56.08),(.025,.025,.42),'Iron')
    me.ring(6.18,6.215,56.27,.03,'Iron',n=144);me.ring(6.18,6.205,56.08,.025,'Iron',n=144)
    part('belfry_crown',me,8,'crown',22.7,23.9,angle=math.pi/2)
    # Seven bronze bells have shaped lips, crowns, clappers and iron yokes.
    for j in range(7):
        a=(j+.5)*TAU/7;x,y=4.95*math.cos(a),4.95*math.sin(a);r=.55+.16*(j%3);me=Mesh(MAT)
        profile=[(0,0),(r,0),(r*1.06,.09),(r,.18),(r*.72,.4),(r*.55,.85),(r*.49,1.2),(r*.2,1.32),(0,1.32)]
        me.lathe((x,y,49.9),profile,'Bronze',40);me.lathe((x,y,49.8),[(0,0),(.08,0),(.08,1.1),(0,1.1)],'Iron',12)
        me.box((x,y,51.4),(r*2.2,.26,.32),'Wood',a);me.box((x,y,52),(.15,.18,1),'Iron')
        st=22.2+j*.06;part('bell_%02d'%j,me,8,'bells',st,st+.95,angle=a)
    # Source-informed but schematic circulation within the annular masonry.
    for group in range(14):
        me=Mesh(MAT)
        for i in range(group*20,min(273,(group+1)*20)):
            a=i*TAU/54;z=.35+i*48/273;me.ring(4.25,5.43,z,.17,'Marble',a,a+TAU/54,3)
        st=3+group*1.35;part('stair_%02d'%group,me,group//2,'stairs',st,st+.9,angle=group*TAU/8)
    me=Mesh(MAT);me.box((-7.27,0,1.6),(.16,1.46,2.8),'Wood');me.box((-7.45,0,3.12),(.3,2.1,.28),'Carving')
    for y in [-.92,.92]:me.box((-7.46,y,1.7),(.34,.26,3.1),'Carving')
    for y in np.arange(-.6,.7,.16):me.box((-7.38,float(y),1.6),(.02,.025,2.65),'Iron')
    part('south_portal',me,0,'portal',5,6.3,angle=math.pi)
    me=Mesh(MAT);me.ring(8.8,12.8,-.24,.22,'Paving',n=192);me.ring(12.7,13.0,-.2,.35,'Marble',n=192)
    for j in range(72):
        a=j*TAU/72;me.box((12.1*math.cos(a),12.1*math.sin(a),.32),(.06,.06,.7),'Iron',a)
    me.ring(12.08,12.12,.63,.035,'Iron',n=192)
    me.object('STATIC_SITE_catino',ASSET,GEO)

def roof(me,x,y,z,sx,sy,rise,mat,along='y'):
    if along=='y':
        p=[(x-sx/2,y-sy/2,z),(x+sx/2,y-sy/2,z),(x+sx/2,y+sy/2,z),(x-sx/2,y+sy/2,z),(x,y-sy/2,z+rise),(x,y+sy/2,z+rise)]
        for f in [(0,3,5,4),(4,5,2,1),(0,4,1),(3,2,5)]:me.face([p[i] for i in f],mat)
    else:
        roof2=Mesh(MAT);roof(roof2,y,x,z,sy,sx,rise,mat,'y')
        for ids,ma,sm in zip(roof2.f,roof2.ma,roof2.sm):me.face([(roof2.v[i][1],roof2.v[i][0],roof2.v[i][2]) for i in ids][::-1],ma)

def landmarks():
    print('BUILD landmarks',flush=True)
    by={f['osm_id']:f for f in R['landmarks']}
    # Cathedral: actual OSM cross footprint, basilican nave, transept, apses and dome.
    p=by[22945163];me=Mesh(MAT);me.extrude(p,.02,13,'Marble','Tile',uvscale=4)
    x,y=29.5,72.5
    me.box((x,y,20),(21,88,14),'Marble');roof(me,x,y,27,22.2,90,6,'Tile')
    me.box((x,53,19),(65,21,12),'Marble');roof(me,x,53,25,66,22,6,'Tile','x')
    roof(me,x-16.5,y,13.1,12,88,3,'Tile');roof(me,x+16.5,y,13.1,12,88,3,'Tile')
    me.lathe((x,53,27),[(10,0),(10,4),(9.5,5),(9,7),(8,11),(6,15),(3,18),(0,19)],'DomeLead',64)
    for i in range(16):
        a=i*TAU/16;xx,yy=x+10*math.cos(a),53+10*math.sin(a);me.column((xx,yy,27),4.2,'Carving',detail=False,r=.25)
    # Horizontal marble courses and tall nave windows.
    for side in [-1,1]:
        xx=x+side*10.52
        for yy in np.arange(32,115,5.7):
            me.box((xx,yy,22.6),(.055,1.3,4.3),'DarkGlass')
            me.arch((xx,yy,20.5),1.3,4.3,.12,.2,'Carving',math.pi/2)
        for zz in np.arange(14,27,1.2):me.box((xx,y,float(zz)),(.06,88,.11),'StoneGrey')
    # West facade: four open gallery orders beneath the gable.
    fy=117.65
    for tier,width,z in [(0,39,13.8),(1,34,18.1),(2,25,22.5),(3,16,26.8)]:
        n=max(5,int(width/2.7));w=width/n
        me.box((x,fy,z-.2),(width+.8,1.1,.48),'Carving')
        for j in range(n+1):me.column((x-width/2+j*w,fy+.15,z),2.3,'Carving',detail=False,r=.15)
        for j in range(n):me.arch((x-width/2+(j+.5)*w,fy+.15,z),w-.38,2.3,.48,.18,'Marble',0,n=12)
    for xx in [x-12,x,x+12]:
        me.box((xx,118,3.5),(3.6,.15,6.9),'Bronze');me.arch((xx,118.2,0),3.8,7,.5,.45,'Carving',n=20)
    me.box((x,117.8,34.1),(.3,.3,2.5),'Carving');me.box((x,117.8,34.5),(1.6,.3,.25),'Carving')
    # Eastern semicircular apse, the face most visible behind the leaning tower.
    me.lathe((x,31,0),[(0,0),(11,0),(11,17),(0,17)],'Marble',64,math.pi,TAU,closed=True)
    me.lathe((x,31,17),[(11.5,0),(0,6)],'Tile',64,math.pi,TAU,closed=True)
    for i in range(10):
        a=math.pi+(i+.5)*math.pi/10;xx,yy=x+11.08*math.cos(a),31+11.08*math.sin(a)
        me.column((xx,yy,.5),7.2,'Carving',detail=False,r=.25)
        me.arch((xx,yy,.5),2.7,7.2,.4,.25,'Carving',a+math.pi/2,n=14)
        me.column((xx,yy,10.2),3.2,'Carving',detail=False,r=.17)
        me.arch((xx,yy,10.2),2.4,3.2,.3,.2,'Carving',a+math.pi/2,n=14)
    for zz in np.arange(.9,17,1.2):me.ring(11.015,11.06,float(zz),.1,'StoneGrey',math.pi,TAU,64,c=(x,31))
    for side in [-1,1]:
        xx=x+side*32.55
        for zz in np.arange(.7,25,1.15):me.box((xx,53,float(zz)),(.06,21,.1),'StoneGrey')
        for yy in np.arange(44,64,4.2):
            me.column((xx,yy,.5),8.3,'Carving',detail=False,r=.3)
            me.arch((xx,yy+2.1,.5),3.35,8.3,.38,.25,'Carving',math.pi/2,n=14)
        for yy in [46.5,53,59.5]:
            me.box((xx,yy,18.8),(.07,1.4,4.5),'DarkGlass');me.arch((xx,yy,16.5),1.5,4.5,.3,.2,'Carving',math.pi/2,n=14)
    # Northern and southern aisles use articulated blind arcade bays.
    for side in [-1,1]:
        xx=x+side*22
        for yy in np.arange(33,113,4.9):
            me.column((xx,yy,1),7,'Carving',detail=False,r=.27);me.arch((xx,yy+2.45,1),3.8,7,.26,.25,'Marble',math.pi/2,n=12)
    me.object('PISA_LANDMARK_Cathedral',CONTEXT,CTX)
    # Baptistery at its actual mapped centre. Double-shell dome and Gothic crowns.
    p=by[22945162];x,y=p['center'];me=Mesh(MAT)
    me.lathe((x,y,0),[(0,0),(17.6,0),(17.6,2),(17.1,2),(17.1,15),(16.5,16),(16.5,24),(14,28),(12,32),(10,36),(7,40),(3,43),(0,44)],'Marble',96)
    # Two material half-domes (historic tile/lead contrast).
    me.lathe((x,y,25),[(16,0),(14,4),(11.5,8),(8,13),(4,17),(0,19)],'Tile',64,0,math.pi)
    me.lathe((x,y,25),[(16,0),(14,4),(11.5,8),(8,13),(4,17),(0,19)],'DomeLead',64,math.pi,TAU)
    for j in range(20):
        a=j*TAU/20;mid=a+math.pi/20
        me.column((x+17.2*math.cos(a),y+17.2*math.sin(a),1.1),10.5,'Carving',detail=False,r=.38)
        me.arch((x+17.2*math.cos(mid),y+17.2*math.sin(mid),1.1),4.5,10.5,.45,.45,'Carving',mid+math.pi/2,n=16)
        for k in [0,1]:
            aa=a+k*TAU/40;xx,yy=x+16.9*math.cos(aa),y+16.9*math.sin(aa)
            me.column((xx,yy,17),5.5,'Carving',detail=False,r=.18)
            me.lathe((xx,yy,24),[(.7,0),(.7,1),(.25,4),(0,4.8)],'Carving',8)
    me.lathe((x,y,44),[(0,0),(.9,0),(.6,1),(0,2)],'Bronze',16)
    me.object('PISA_LANDMARK_Baptistery',CONTEXT,CTX)
    # Camposanto actual courtyard ring with pitched corridor roofs and traceried arcades.
    p=by[154289];me=Mesh(MAT);me.extrude(p,0,10,'Marble','Tile',uvscale=4)
    xmin,ymin,xmax,ymax=p['bounds'];cx,cy=p['center']
    roof(me,cx,ymin+5.5,10,xmax-xmin,11,2.8,'Tile','x');roof(me,cx,ymax-5.5,10,xmax-xmin,11,2.8,'Tile','x')
    roof(me,xmin+5.5,cy,10,11,ymax-ymin,2.8,'Tile');roof(me,xmax-5.5,cy,10,11,ymax-ymin,2.8,'Tile')
    for yy in np.arange(ymin+10,ymax-8,5):
        for xx in [xmin-.03,xmax+.03]:
            me.column((xx,yy,.5),6.6,'Carving',detail=False,r=.22);me.arch((xx,yy+2.5,.5),4.2,6.6,.35,.24,'Carving',math.pi/2,n=12)
    me.object('PISA_LANDMARK_Camposanto',CONTEXT,CTX)

def tree(me,x,y,h,i):
    me.lathe((x,y,0),[(0,0),(.16,0),(.11,h*.7),(0,h*.7)],'Bark',7)
    if i%4==0:
        # Slender Tuscan cypress; lobed taper rather than identical balls.
        me.lathe((x,y,h*.23),[(0,0),(.55,.2),(1.05,h*.25),(.8,h*.53),(.3,h*.73),(0,h*.81)],'LeavesDark',12)
    else:
        for j in range(3):
            a=j*TAU/3+i;me.sphere((x+math.cos(a)*.75,y+math.sin(a)*.75,h*.7+j*.28),h*.24,'Leaves' if i%3 else 'LeavesDark',n=10,m=6,scale=(1.1,1,.8))

def district():
    print('BUILD district',len(R['buildings']),flush=True)
    tiles={}
    def tile(x,y):
        key=(math.floor(x/400),math.floor(y/400))
        if key not in tiles:tiles[key]=Mesh(MAT)
        return tiles[key]
    # Source footprints and roof ridges are clipped at the circular 1000 m boundary.
    for b in R['buildings']:
        me=tile(*b['center']);me.extrude(b,0,b['height'],b['style'],'Tile')
        for p in b['roof']:me.poly(p,p['z'],'Tile')
        if math.hypot(*b['center'])<220:
            x,y=b['center'];me.box((x,y,b['height']+1),(.65,.6,2),'Brick')
    for key,me in sorted(tiles.items()):me.object('PISA_DISTRICT_buildings_%d_%d'%key,CONTEXT,CTX)
    for name,items,z,mat in [('greens',R['greens'],.012,'Grass'),('roads',R['roads'],.04,None),('water',R['water'],.02,'Water')]:
        me=Mesh(MAT)
        for i,p in enumerate(items):me.poly(p,z+(.005 if p.get('style')=='paving' else 0),mat or ('Paving' if p['style']=='paving' else 'Asphalt'))
        me.object('PISA_DISTRICT_'+name,CONTEXT,CTX)
    me=Mesh(MAT)
    for i,(x,y) in enumerate(R['trees']):tree(me,x,y,5+(i%7)*.5,i)
    me.object('PISA_DISTRICT_trees_source_positions',CONTEXT,CTX)
    me=Mesh(MAT)
    for w in R['walls']:
        for a,b in zip(w['points'],w['points'][1:]):
            length=math.dist(a,b);angle=math.atan2(b[1]-a[1],b[0]-a[0]);mid=((a[0]+b[0])/2,(a[1]+b[1])/2,4.1);me.box(mid,(length,1.6,8.2),'Brick',angle)
            for i in range(max(1,int(length/1.6))):
                t=(i+.5)/max(1,int(length/1.6));me.box((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),8.6),(.75,1.6,.8),'Brick',angle)
    me.object('PISA_DISTRICT_medieval_walls',CONTEXT,CTX)
    # Real asset terrain disc: no studio rectangle exported. Small negative offset.
    me=Mesh(MAT);me.lathe((0,0,-.18),[(0,0),(1000,0),(1000,.14),(0,.14)],'Ground',256);me.object('PISA_DISTRICT_ground_disc',CONTEXT,CTX)
    landmarks()

def camera(name,loc,target,lens=50,ortho=None):
    d=bpy.data.cameras.new('PISA_CAM_'+name);ob=bpy.data.objects.new(d.name,d);PRE.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=10000
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return ob

def export(c,path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in c.objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT')
    from canonical import canonicalize
    canonicalize(path)

def bake(clip,duration):
    frames=np.arange(round(duration*30)+1,dtype=np.float32)
    for p in PARTS:
        ob=bpy.data.objects[p['node_name']];ob.animation_data_clear()
        ob.keyframe_insert('location',frame=0);ob.keyframe_insert('scale',frame=0);ob.keyframe_insert('rotation_euler',frame=0)
        action=ob.animation_data.action;action.name=clip+'_'+p['part_id']
        poses=[pose(p,float(f/30),clip) for f in frames]
        channels={'location':np.array([a[0] for a in poses]),'scale':np.array([a[1] for a in poses]),'rotation_euler':np.array([[0,0,a[2]] for a in poses])}
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        curve.keyframe_points.clear();curve.keyframe_points.add(len(frames));curve.keyframe_points.foreach_set('co',np.column_stack((frames,channels[curve.data_path][:,curve.array_index])).astype(np.float32).ravel())
                        enum=curve.keyframe_points[0].bl_rna.properties['interpolation'].enum_items['LINEAR'].value;curve.keyframe_points.foreach_set('interpolation',np.full(len(frames),enum,dtype=np.int32));curve.update()

def main():
    global SC,ASSET,CONTEXT,PRE,GEO,CTX
    old=bpy.data.scenes.get('PISA_TOWER')
    if old:bpy.data.scenes.remove(old)
    SC=bpy.data.scenes.new('PISA_TOWER');bpy.context.window.scene=SC
    SC.unit_settings.system='METRIC';SC.unit_settings.scale_length=1;SC.unit_settings.length_unit='METERS';SC.render.fps=30;SC.frame_start=0;SC.frame_end=840
    ASSET=coll('PISA_ASSET');CONTEXT=coll('PISA_CONTEXT');PRE=coll('PISA_PREVIEW_ONLY')
    GEO=empty('GEO_ROOT',ASSET);CTX=empty('PISA_CONTEXT_ROOT',CONTEXT)
    metadata=dict(geo_metadata_version=1,longitude_wgs84=CFG['longitude'],latitude_wgs84=CFG['latitude'],horizontal_crs='EPSG:4326',vertical_reference='WGS84_ELLIPSOID',coordinate_source='OSM relation/12982355 footprint centroid, snapshot 2026-10-20T15:50:57Z',coordinate_accuracy='reference',height_source='terrain_at_load',units='meters',local_origin='ground_at_tower_footprint_centroid',height_m=56.3)
    for k,v in metadata.items():GEO[k]=v
    material('Marble',(.86,.83,.75),tex='marble-base.png',stone=True);material('Carving',(.79,.76,.67),.64);material('StoneGrey',(.31,.33,.29),.78)
    material('Bronze',(.21,.27,.17),.43,1);material('Iron',(.07,.08,.075),.6,.8);material('Wood',(.12,.075,.038),.8)
    material('Paving',(.6,.57,.5),.85,tex='paving-base.png');material('Grass',(.3,.4,.2),.95,tex='grass-base.png');material('Asphalt',(.2,.2,.19),.93,tex='asphalt-base.png')
    material('Tile',(.5,.23,.13),.87,tex='terracotta-base.png');material('DomeLead',(.33,.35,.33),.64,.5);material('DarkGlass',(.08,.12,.13),.25)
    material('Leaves',(.17,.24,.08),.92);material('LeavesDark',(.07,.14,.065),.96);material('Bark',(.16,.11,.065),.95);material('Brick',(.33,.23,.15),.9)
    material('Water',(.15,.27,.28),.19,tex='water-base.png');material('Ground',(.3,.32,.23),.95);material('WarmLight',(1,.55,.18),.6,strength=2.8)
    for name in ['ivory','ochre','rose','cream']:material(name,(.6,.5,.4),.85,tex=name+'-facade.png',em=name+'-emissive.png',strength=1.6)
    tower();district()
    # Night accent is sparse and static, independent of the flight clock.
    me=Mesh(MAT)
    for i in range(12):
        a=i*TAU/12;me.box((11.6*math.cos(a),11.6*math.sin(a),.03),(.16,.3,.05),'WarmLight',a)
    me.object('STATIC_SITE_luminaires',ASSET,GEO)
    SC.world=bpy.data.worlds.new('PISA_Atmosphere');SC.world.use_nodes=True;bg=next(n for n in SC.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.32,.43,.6,1);bg.inputs[1].default_value=.35
    SC.render.engine='BLENDER_EEVEE';SC.view_settings.view_transform='AgX';SC.render.resolution_x=1800;SC.render.resolution_y=1350;SC.render.resolution_percentage=100
    try:SC.eevee.taa_render_samples=48;SC.eevee.use_raytracing=True
    except Exception:pass
    sun=bpy.data.objects.new('PISA_Sun',bpy.data.lights.new('PISA_Sun','SUN'));PRE.objects.link(sun);sun.data.energy=2.8;sun.rotation_euler=(.5,-.35,-.6);sun.data.angle=.055
    for name,loc,energy,size,color in [('Fill',(-20,-70,70),45000,90,(.77,.86,1)),('TowerFlood',(-25,-18,8),16000,18,(1,.76,.48)),('Rim',(40,28,54),45000,40,(1,.88,.65))]:
        d=bpy.data.lights.new('PISA_'+name,'AREA');o=bpy.data.objects.new(d.name,d);PRE.objects.link(o);o.location=loc;o.rotation_euler=(Vector((-2,0,29))-o.location).to_track_quat('-Z','Y').to_euler();d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    horizon=Mesh(MAT);horizon.face([(-15000,-15000,-.35),(15000,-15000,-.35),(15000,15000,-.35),(-15000,15000,-.35)],'Ground');horizon.object('PISA_PREVIEW_horizon',PRE)
    camera('hero',(-78,-119,44),(-1,0,28),48)
    camera('low',(-42,-72,7),(-2,0,28),30)
    camera('rear',(75,-110,45),(-2,0,28),48)
    camera('detail',(-14,-19,31),(-2,0,29),62)
    camera('aerial',(-170,-220,200),(20,70,13),48)
    camera('district',(-2000,-2200,2450),(-40,0,0),48,2250)
    camera('assembly',(-120,-170,82),(-1,0,30),48)
    camera('explode',(-155,-210,110),(0,0,48),42)
    SC.camera=bpy.data.objects['PISA_CAM_hero']
    ROOT.joinpath('previews').mkdir(exist_ok=True);ROOT.joinpath('verification').mkdir(exist_ok=True)
    (ROOT/'placement.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'parts.json').write_text(json.dumps(dict(version=1,standard_id='CS-AM-1',coordinate_frame='gltf-local-y-up',units='meters',parts=PARTS),ensure_ascii=False,indent=2),encoding='utf-8')
    export(ASSET,ROOT/'pisa-tower.glb');export(CONTEXT,OUT/'district.glb')
    bake('BUILD_ASSEMBLY',28);SC.frame_set(840)
    for im in bpy.data.images:
        if im.filepath and str(ROOT) in bpy.path.abspath(im.filepath):im.pack()
    for ar in bpy.context.screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_distance=110;ar.spaces.active.region_3d.view_location=(-2,0,28);ar.spaces.active.clip_end=10000;ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.shading.color_type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'pisa-tower.blend'),compress=True)
    stats=dict(blender=bpy.app.version_string,parts=len(PARTS),asset_triangles=sum(len(p.vertices)-2 for o in ASSET.objects if o.type=='MESH' for p in o.data.polygons),context_triangles=sum(len(p.vertices)-2 for o in CONTEXT.objects if o.type=='MESH' for p in o.data.polygons),asset_objects=len(ASSET.objects),context_objects=len(CONTEXT.objects),materials=len(MAT))
    (ROOT/'verification/build.json').write_text(json.dumps(stats,indent=2));print('BUILD_COMPLETE',stats,flush=True)

if __name__=='__main__':main()
