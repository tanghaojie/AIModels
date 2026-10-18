"""Blender 5.2: editable, deterministic Wangjing SOHO + real OSM district.

Run: blender --background --factory-startup --python scripts/build_model.py
Only WANGJING_SOHO and its named scenes/data are replaced on a repeated run.
"""
import bpy, math, json, sys, random, bmesh
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose,gltf
CFG=json.loads((ROOT/'config.json').read_text())
R=json.loads((ROOT/'recipe.json').read_text(encoding='utf-8'))
OUT=ROOT.parents[1]/'model-assets'/'geo-context'/'wangjing-soho-1500-v1'
RNG=random.Random(CFG['seed'])
MAT=[]; MI={}; PARTS=[]; MOVING=[]

def collection(name):
    c=bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(c)
    c=bpy.data.collections.new(name);SC.collection.children.link(c);return c
def empty(name,coll,parent=None,location=(0,0,0)):
    ob=bpy.data.objects.new(name,None);coll.objects.link(ob);ob.parent=parent;ob.location=location;return ob
def material(name,color,rough=.5,metal=0,tex=None,em=None,strength=0):
    old=bpy.data.materials.get('WJ_'+name)
    if old:bpy.data.materials.remove(old,do_unlink=True)
    m=bpy.data.materials.new('WJ_'+name);m.use_nodes=True;m.diffuse_color=(*color,1);m.use_backface_culling=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    bs.inputs['Emission Strength'].default_value=strength
    def img(path,colorspace='sRGB'):
        im=bpy.data.images.load(str(ROOT/'textures'/path),check_existing=True);im.colorspace_settings.name=colorspace
        n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;return n
    if tex:m.node_tree.links.new(img(tex).outputs['Color'],bs.inputs['Base Color'])
    if em:m.node_tree.links.new(img(em).outputs['Color'],bs.inputs['Emission Color'])
    if name=='Glass_lowE':
        orm=img('curtain-orm.png','Non-Color');sep=m.node_tree.nodes.new('ShaderNodeSeparateColor');m.node_tree.links.new(orm.outputs['Color'],sep.inputs[0]);m.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
        bs.inputs['IOR'].default_value=1.5
    if name.endswith('_facade'):
        st=name.split('_')[0]
        orm=img('district/'+st+'-orm.png','Non-Color');sep=m.node_tree.nodes.new('ShaderNodeSeparateColor');m.node_tree.links.new(orm.outputs['Color'],sep.inputs[0]);m.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
    if strength and not em:bs.inputs['Emission Color'].default_value=(*color,1)
    MI[name]=len(MAT);MAT.append(m);return m

class Mesh:
    def __init__(self):self.v=[];self.f=[];self.m=[];self.uv=[];self.sm=[]
    def face(self,pts,mat,uv=None,smooth=False):
        k=len(self.v);self.v.extend(tuple(p) for p in pts);self.f.append(tuple(range(k,k+len(pts))));self.m.append(MI[mat] if isinstance(mat,str) else mat);self.uv.extend(uv or [(p[0]/4,p[1]/4) for p in pts]);self.sm.append(smooth)
    def quad(self,a,b,c,d,mat,uv=None,smooth=False):self.face([a,b,c,d],mat,uv,smooth)
    def box(self,center,size,mat,angle=0):
        x,y,z=center;a,b,c=[s/2 for s in size];co,si=math.cos(angle),math.sin(angle)
        p=[(x+co*i-si*j,y+si*i+co*j,z+k) for i,j,k in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
        for ids in [(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:self.face([p[i] for i in ids],mat)
    def poly(self,p,z,mat):
        v=p['points']
        for a,b,c in p['triangles']:self.face([(v[i][0],v[i][1],z) for i in (a,b,c)],mat)
    def extrude(self,p,z,h,wall,roof,uvscale=12):
        self.poly(p,z+h,roof);v=p['points'];off=0
        for count in p['rings']:
            for j in range(count):
                a,b=v[off+j],v[off+(j+1)%count];w=math.dist(a,b)
                self.quad((*a,z),(*b,z),(*b,z+h),(*a,z+h),wall,[(0,0),(w/uvscale,0),(w/uvscale,h/uvscale),(0,h/uvscale)])
            off+=count
    def object(self,name,coll,parent=None,pivot=(0,0,0)):
        if not self.f:return None
        p=Vector(pivot);me=bpy.data.meshes.new(name);me.from_pydata([Vector(v)-p for v in self.v],[],self.f);me.update()
        for mat in MAT:me.materials.append(mat)
        for poly,ma,sm in zip(me.polygons,self.m,self.sm):poly.material_index=ma;poly.use_smooth=sm
        uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',[c for uv in self.uv for c in uv])
        ob=bpy.data.objects.new(name,me);coll.objects.link(ob);ob.parent=parent;ob.location=p
        return ob

def smooth_contour(points,n):
    p=np.array(points,dtype=float);out=[]
    for j in range(n*4):
        t=j/(n*4)*len(p);i=int(t);t-=i
        a,b,c,d=[p[(i+k)%len(p)] for k in [-1,0,1,2]]
        v=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
        out.append(v)
    out=np.array(out);dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.vstack((out,out[0])),axis=0),axis=1))]
    desired=np.linspace(0,dist[-1],n,endpoint=False)
    return np.array([np.interp(desired,dist,np.r_[out[:,j],out[0,j]]) for j in range(2)]).T

def loop(tower,z,inset=0):
    t=max(0,min(1,z/tower['height']));base=tower['contour'];center=tower['center']
    fac=float(np.interp(t,[0,.06,.25,.45,.65,.8,.9,.97,1],[1,1.005,.965,.87,.72,.53,.35,.16,.035]))
    shift=np.array(tower['shift'])*(t**1.5)
    q=center+(base-center)*fac+shift
    if inset:
        delta=q-(center+shift);radius=np.linalg.norm(delta,axis=1);q-=delta/radius[:,None]*np.minimum(inset,radius*.45)[:,None]
    return np.column_stack((q,np.full(len(q),z)))

def band(mesh,tower,z0,z1,mat,start=0,end=None,inset=0):
    a,b=loop(tower,z0,inset),loop(tower,z1,inset);n=len(a);end=end if end is not None else n
    for j in range(start,end):
        k=(j+1)%n;mesh.quad(a[j],a[k],b[k],b[j],mat,smooth=True)

def ribbon(mesh,tower,z,start,end):
    # Closed, rounded aluminium fascia cross section; the back has visible thickness.
    rings=[loop(tower,max(0,z+d),inset) for d,inset in [(0,.5),(.08,.08),(.2,0),(.92,0),(1.02,.12),(1.02,1.15),(.1,1.15)]]
    n=len(rings[0]);
    for r in range(len(rings)):
        for j in range(start,end):
            k=(j+1)%n;mesh.quad(rings[r][j],rings[r][k],rings[(r+1)%len(rings)][k],rings[(r+1)%len(rings)][j],'Aluminium_white' if r<5 else 'Soffit',smooth=True)
    for j in [start,end%n]:mesh.face([r[j] for r in rings][::1 if j==start else -1],'Aluminium_white')

def slab(mesh,tower,z):
    outer=loop(tower,z,.7);inner=loop(tower,z,.7);c=tower['center']+np.array(tower['shift'])*(max(0,z/tower['height'])**1.5);inner[:,:2]=c+(inner[:,:2]-c)*.16
    for j in range(len(outer)):
        k=(j+1)%len(outer);a,b=outer[j],outer[k];i,h=inner[j],inner[k]
        mesh.quad(a,b,h,i,'Slab')
        mesh.quad(i+[0,0,-.28],h+[0,0,-.28],b+[0,0,-.28],a+[0,0,-.28],'Slab')
        mesh.quad(a+[0,0,-.28],b+[0,0,-.28],b,a,'Slab',smooth=True)
        mesh.quad(h+[0,0,-.28],i+[0,0,-.28],i,h,'Slab',smooth=True)

def part(name,mesh,pivot,category,level,tower,start,end,offset,depends=None):
    node=empty('PART_'+name,ASSET,GEO,pivot);node['part_id']=name
    obj=mesh.object('MESH_'+name,ASSET,node,pivot);obj.location=(0,0,0)
    # The mesh was translated to pivot locally, while its PART carries assembled translation.
    yaw=RNG.uniform(-.12,.12);angle=math.atan2(pivot[1],pivot[0])
    spawn=[pivot[0]+math.cos(angle)*RNG.uniform(14,35),pivot[1]+math.sin(angle)*RNG.uniform(14,35),pivot[2]+85+RNG.uniform(140,215)]
    record=dict(part_id=name,node_name=node.name,parent_node_name='GEO_ROOT',category=category,level=level,zone=tower,animated=True,pivot_note='local component center; mesh vertices relative to pivot',assembled_blender=list(pivot),explode_blender=list(offset),assembled=dict(translation_m=gltf(pivot),rotation_xyzw=[0,0,0,1],scale=[1,1,1]),explode_offset_m=gltf(offset),start_s=start,end_s=end,spawn_blender=spawn,yaw=yaw,assembly=dict(phase=category,order=len(PARTS),start_s=start,end_s=end,spawn_translation_m=gltf(spawn),waypoints_m=[gltf([pivot[0],pivot[1],pivot[2]+85+40])],depends_on=depends or []))
    record['assembly']['waypoints_m']=[]  # Direct smoothstep descent; no unexecuted waypoint contract.
    PARTS.append(record);MOVING.append(node);return name

def build_tower(t):
    name=t['id'];n=CFG['facade_segments'];t['contour']=smooth_contour(t['points'],n);t['center']=np.mean(t['contour'],axis=0)
    t['shift']={'T1':[8,30],'T2':[-35,-9],'T3':[9,-10],'P1':[0,0],'P2':[0,0],'P3':[0,0]}[name]
    h=t['height'];floors=t['floors'];top=t['occupied_top']
    levels=np.r_[np.linspace(0,top,floors+1),np.linspace(top,h,8)[1:]] if name[0]=='T' else np.linspace(0,h,floors+1)
    c=t['center'];core=[]
    if name[0]=='T':
        for i in range(0,floors,5):
            z0=levels[i];z1=levels[min(i+5,floors)];zm=(z0+z1)/2;cm=c+np.array(t['shift'])*(zm/h)**1.5;rim=loop(t,z1);c1=c+np.array(t['shift'])*(z1/h)**1.5;radius=float(np.min(np.linalg.norm(rim[:,:2]-c1,axis=1)));width=min(10,radius*.7);m=Mesh();m.box((*cm,zm),(width,width*.8,z1-z0),'Concrete')
            core.append(part(f'{name}_core_{i:02}',m,(*cm,zm),'core',i,name,1+i/floors*3,2+i/floors*3,[0,0,15+i*2],core[-1:]));
    for i in range(len(levels)-1):
        z0,z1=levels[i],levels[i+1];frac=i/(len(levels)-1);iscrown=i>=floors
        s=3.5+frac*8+(int(name[-1])*.2 if name[0]=='T' else 10)
        m=Mesh();slab(m,t,z0+.32)
        slabid=part(f'{name}_floor_{i:02}',m,(*c,z0),'floor',i,name,s,s+.8,[0,0,5+i*2.6],[core[min(i//5,len(core)-1)]] if core else [])
        for sector in range(2):
            start,end=sector*n//2,(sector+1)*n//2;m=Mesh();ribbon(m,t,z0,start,end)
            a,b=loop(t,z0+.97,1.25),loop(t,z1-.08,1.25)
            for j in range(start,end):
                k=(j+1)%n;cell=(j*7+i*13+int(name[-1])*17)%128;u=(cell%16)/16;v=(cell//16)/8
                uv=[(u+.002,v+.004),(u+1/16-.002,v+.004),(u+1/16-.002,v+1/8-.004),(u+.002,v+1/8-.004)]
                m.quad(a[j],a[k],b[k],b[j],'Glass_lowE',uv,smooth=True)
                # Geometric mullion with a credible 70 mm visible face.
                tube(m,[a[j],b[j]],.0375,'Frame',sides=4)
            install=8+frac*11+(int(name[-1])*.2 if name[0]=='T' else .1)
            if name[0]=='P':install=18+frac*1.5
            ang=(sector+.5)*math.pi;ex=[math.cos(ang)*32,math.sin(ang)*32,12+i*2.6]
            part(f'{name}_skin_{i:02}_{sector}',m,(*c,(z0+z1)/2),'crown' if iscrown else 'facade',i,name,install,install+1.1,ex,[slabid])
    m=Mesh();p=loop(t,h)
    m.face(list(p),'Aluminium_white')
    part(name+'_cap',m,(*c,h),'roof',floors,name,20,21,[0,0,30],[])
    # Ground lobby entrances and canopies, gathered into one coherent moving component.
    m=Mesh()
    for j in [n//8,5*n//8]:
        q=loop(t,0,0)[j];prev=loop(t,0,0)[(j+1)%n];ang=math.atan2(prev[1]-q[1],prev[0]-q[0]);m.box((q[0],q[1],3.7),(12,6,.25),'Aluminium_white',ang)
        for u in [-3,0,3]:
            m.box((q[0]+math.cos(ang)*u,q[1]+math.sin(ang)*u,1.8),(.12,.12,3.6),'Frame')
    part(name+'_entries',m,(*c,2),'entrance',0,name,20,21.3,[20,12,3],[])
    if name=='T3':
        # Physical signage on the curtain wall, attached to that moving floor sector.
        level=38;z=levels[level]+1.05;q=loop(t,z,0)
        direction=np.array([-.65,-.76]);idx=int(np.argmax((q[:,:2]-c)@direction));normal=Vector((*((q[idx,:2]-c)/np.linalg.norm(q[idx,:2]-c)),0));up=Vector((0,0,1));right=up.cross(normal)
        txt=bpy.data.curves.new('WJ_SOHO_wordmark','FONT');txt.body='SOHO';txt.size=4.2;txt.extrude=.055;txt.bevel_depth=.015;txt.align_x='CENTER';txt.shear=.18
        ob=bpy.data.objects.new('SOHO_sign',txt);ASSET.objects.link(ob);txt.materials.append(MAT[MI['Aluminium_white']]);ob.location=Vector(q[idx])+normal*.35;ob.rotation_euler=Matrix((right,up,normal)).transposed().to_euler()
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
        parent=bpy.data.objects[f'PART_T3_skin_{level:02}_{idx//(n//2)}'];world=ob.matrix_world.copy();ob.parent=parent;ob.matrix_world=world;ob['signage']='Interpretive SOHO wordmark, not official vector artwork'
    return t

def tube(mesh,pts,r,mat,sides=6):
    for a,b in zip(pts[:-1],pts[1:]):
        a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.01:u=axis.cross(Vector((0,1,0)))
        u.normalize();v=axis.cross(u);A=[];B=[]
        for j in range(sides):
            d=(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides))*r;A.append(a+d);B.append(b+d)
        for j in range(sides):k=(j+1)%sides;mesh.quad(A[j],A[k],B[k],B[j],mat,smooth=True)
        mesh.face(A[::-1],mat);mesh.face(B,mat)
def tree(mesh,x,y,height=7,style=0):
    tube(mesh,[(x,y,.4),(x,y,height*.65)],.17,'Bark')
    for k in range(4):
        angle=k*2.4+RNG.random();r=height*.18;xx=x+math.cos(angle)*r;yy=y+math.sin(angle)*r;zz=height*(.65+.09*(k%2));tube(mesh,[(x,y,height*.45),(xx,yy,zz)],.07,'Bark')
        # Irregular, layered branching crowns with distinct forms, rather than identical spheres.
        count=9;ring=[]
        for j in range(count):
            a=j*math.tau/count;radius=height*RNG.uniform(.18,.31);ring.append((xx+radius*math.cos(a),yy+radius*math.sin(a),zz+RNG.uniform(-.4,.3)))
        top=(xx+.3,yy-.2,zz+height*.25);bot=(xx,yy,zz-height*.2)
        for j in range(count):
            nxt=(j+1)%count;mat='Leaves_'+str((j+k+style)%3);mesh.face([ring[j],ring[nxt],top],mat,smooth=True);mesh.face([ring[nxt],ring[j],bot],mat,smooth=True)

def site(towers):
    m=Mesh();ground={'points':[[-175,-175],[175,-175],[175,165],[-175,165]],'rings':[4],'triangles':[[0,1,2],[0,2,3]]}
    # A restrained, fan-shaped landscape: paths and tapered planters follow reference circulation.
    boundary=[(-128,-192),(-166,-108),(-162,62),(-104,147),(68,174),(170,118),(200,-2),(132,-146)]
    points=smooth_contour(boundary,160);g={'points':points.tolist(),'rings':[160],'triangles':[[0,i,i+1] for i in range(1,159)]}
    m.extrude(g,-.3,.55,'Concrete','Limestone')
    m.object('SITE_plaza',ASSET,GEO)
    plants=Mesh();fixtures=Mesh();water=Mesh()
    for k,(x,y,l,w,a) in enumerate([(-128,25,65,17,.1),(-87,122,64,21,1.3),(78,100,78,17,-.7),(134,30,70,18,-.9),(115,-94,58,18,-.6),(-10,-134,85,20,.1),(45,55,50,11,-.4),(-85,-115,44,14,.8),(-40,100,35,12,.1)]):
        pts=[]
        for j in range(64):
            ph=j*math.tau/64;xx=l*.5*math.cos(ph);yy=w*.5*math.sin(ph)*(1+.2*math.cos(ph));pts.append((x+xx*math.cos(a)-yy*math.sin(a),y+xx*math.sin(a)+yy*math.cos(a)))
        p={'points':pts,'rings':[64],'triangles':[[0,i,i+1] for i in range(1,63)]};plants.extrude(p,.25,.45,'Limestone','Grass')
        tube(fixtures,[(*p,.79) for p in pts+[pts[0]]],.07,'Landscape_light')
        for j in range(max(3,int(l/11))):
            t=(j/(max(3,int(l/11))-1)-.5)*l*.8;tx=x+math.cos(a)*t;ty=y+math.sin(a)*t
            if all(np.min(np.linalg.norm(tw['contour']-np.array((tx,ty)),axis=1))>8 for tw in towers):tree(plants,tx,ty,RNG.uniform(4.5,8),k)
    # Reflecting pools and the darker central water street.
    for x,y,l,w,a in [(-10,35,55,7,.45),(-80,25,38,5,1.2),(80,-95,33,5,-.3)]:
        pts=[(x+math.cos(j*math.tau/60)*l/2*math.cos(a)-math.sin(j*math.tau/60)*w/2*math.sin(a),y+math.cos(j*math.tau/60)*l/2*math.sin(a)+math.sin(j*math.tau/60)*w/2*math.cos(a)) for j in range(60)]
        p={'points':pts,'rings':[60],'triangles':[[0,i,i+1] for i in range(1,59)]};water.extrude(p,.27,.08,'Stone_dark','Water')
        tube(fixtures,[(*p,.38) for p in pts+[pts[0]]],.17,'Limestone')
    for i in range(42):
        a=i*math.tau/42;x=157*math.cos(a);y=141*math.sin(a);tree(plants,x,y,RNG.uniform(6,9),i)
        if i%2==0:
            tube(fixtures,[(x,y,.3),(x,y,4.6)],.08,'Frame');fixtures.box((x,y,4.65),(1.6,.18,.12),'Landscape_light',a)
            fixtures.box((x*.96,y*.96,.65),(3,.75,.24),'Bench',a+math.pi/2)
    plants.object('SITE_trees_planters',ASSET,GEO);fixtures.object('SITE_lighting_benches',ASSET,GEO);water.object('SITE_reflecting_pools',ASSET,GEO)

def district():
    meshes={}
    def tile(key):
        key=tuple(key)
        if key not in meshes:meshes[key]=Mesh()
        return meshes[key]
    # Meter-based circular area; no fictional city grid is introduced.
    m=Mesh();n=256;pts=[(1500*math.cos(i*math.tau/n),1500*math.sin(i*math.tau/n)) for i in range(n)]
    p={'points':pts,'rings':[n],'triangles':[[0,i,i+1] for i in range(1,n-1)]};m.poly(p,-.38,'District_ground');m.object('CONTEXT_ground',CONTEXT,CTXROOT)
    for p in R['greens']:tile((90,90)).poly(p,-.2,'Grass' if p['kind']=='grass' else 'Water')
    for p in R['roads']:
        tile((91,91)).poly(p,-.09 if p['kind'] not in ['footway','path','steps','pedestrian'] else -.06,'Asphalt' if p['kind'] not in ['footway','path','steps','pedestrian'] else 'Limestone')
    markings=Mesh();cars=Mesh()
    for road in R['roads']:
        if road['kind'] not in ['primary','secondary','tertiary','residential']:continue
        pts=road.get('centerline',[])
        if not pts or math.hypot(*pts[0])>800:continue
        for a,b in zip(pts[:-1],pts[1:]):
            dist=math.dist(a,b)
            if dist<1:continue
            tangent=(np.array(b)-np.array(a))/dist;angle=math.atan2(tangent[1],tangent[0])
            for x in np.arange(2,dist,9):
                mid=np.array(a)+tangent*x
                if np.linalg.norm(mid)>800:continue
                markings.box((*mid,-.025),(3,.12,.012),'Road_marking',angle)
            if dist>30 and RNG.random()<.33:
                mid=(np.array(a)+np.array(b))/2+np.array([-tangent[1],tangent[0]])*road['width']*.22
                cars.box((*mid,.65),(4.3,1.9,1.15),'Car_'+str(RNG.randrange(3)),angle);cars.box((*mid,1.38),(2.1,1.68,.5),'Glass_lowE',angle)
    markings.object('CONTEXT_lane_markings',CONTEXT,CTXROOT);cars.object('CONTEXT_road_vehicles',CONTEXT,CTXROOT)
    for p in R['buildings']:
        tile(p['tile']).extrude(p,-.01,p['height'],p['style']+'_facade','Concrete')
    for key,m in sorted(meshes.items()):m.object('CONTEXT_%s_%s'%key,CONTEXT,CTXROOT)
    # Street furniture follows actual OSM road segments near the landmark.
    m=Mesh()
    for p in R['roads']:
        if p['kind'] not in ['primary','secondary','tertiary','residential']:continue
        v=p['points'];center=np.mean(v,axis=0)
        if np.linalg.norm(center)>650:continue
        for x,y in v[::max(3,len(v)//4)]:
            if math.hypot(x,y)<175:continue
            if RNG.random()<.4:tree(m,x,y,RNG.uniform(5,8),int(p['id'])%3)
    m.object('CONTEXT_avenue_trees',CONTEXT,CTXROOT)

def camera(name,loc,target,lens=46,ortho=None):
    d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);PREVIEW.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=7000
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return ob
def lighting(mode='day'):
    settings={'day':(math.radians(35),math.radians(300),2.5,.12,-.2),'sunset':(math.radians(6),math.radians(310),2.2,.065,.1),'blue':(math.radians(-4),math.radians(220),.08,.25,1),'night':(math.radians(-15),math.radians(240),0,.12,1.4)}
    elev,rot,energy,strength,exp=settings[mode]
    SC.world.use_nodes=True;nodes=SC.world.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');sky=nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=elev;sky.sun_rotation=rot;sky.sun_disc=False
    bg.inputs[1].default_value=strength
    if mode in ['blue','night']:bg.inputs[0].default_value=(.06,.105,.22,1)
    else:SC.world.node_tree.links.new(sky.outputs[0],bg.inputs[0])
    SC.world.node_tree.links.new(bg.outputs[0],output.inputs[0]);SUN.rotation_euler=(math.pi/2-elev,0,rot);SUN.data.energy=energy;SUN.data.angle=math.radians(1)
    SUN.data.color=(1,.66,.38) if mode=='sunset' else (1,.95,.88)
    FILL.data.energy=320000 if mode in ['night','blue'] else 18000
    for ma in MAT:
        bs=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        if 'Glass_lowE' in ma.name or ma.name.endswith('_facade'):bs.inputs['Emission Strength'].default_value=0 if mode=='day' else .5 if mode=='sunset' else 2.3
        elif 'Landscape_light' in ma.name:bs.inputs['Emission Strength'].default_value=.1 if mode=='day' else 3
    SC.view_settings.exposure=exp
def bake(clip='BUILD_ASSEMBLY'):
    end=900 if clip=='BUILD_ASSEMBLY' else 360
    frames=np.arange(end+1,dtype=np.float32)
    for node,p in zip(MOVING,PARTS):
        node.animation_data_clear()
        # Allocate each curve once: per-frame keyframe_insert is quadratic for a large building.
        node.keyframe_insert('location',frame=0,group='Flight');node.keyframe_insert('scale',frame=0,group='Flight');node.keyframe_insert('rotation_euler',frame=0,group='Flight')
        node.animation_data.action.name=clip+'_'+p['part_id']
        slot=node.animation_data.action_slot;poses=[pose(p,float(f)/30,clip) for f in frames]
        channels={'location':np.array([v[0] for v in poses]),'scale':np.array([v[1] for v in poses]),'rotation_euler':np.array([[0,0,v[2]] for v in poses])}
        for layer in node.animation_data.action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        curve.keyframe_points.clear();curve.keyframe_points.add(len(frames));curve.keyframe_points.foreach_set('co',np.column_stack((frames,channels[curve.data_path][:,curve.array_index])).astype(np.float32).ravel())
                        linear=curve.keyframe_points[0].bl_rna.properties['interpolation'].enum_items['LINEAR'].value
                        curve.keyframe_points.foreach_set('interpolation',np.full(len(frames),linear,dtype=np.int32));curve.update()
def select_collection(coll):
    bpy.ops.object.select_all(action='DESELECT')
    for o in coll.all_objects:o.select_set(True)
def export(coll,path):
    for ob in bpy.data.objects:ob.select_set(False)
    select_collection(coll);bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_texcoords=True,export_normals=True,export_materials='EXPORT')

def main():
    global SC,ASSET,CONTEXT,PREVIEW,GEO,CTXROOT,SUN,FILL,CAMERAS
    SC=bpy.data.scenes.get('WANGJING_SOHO')
    if SC:bpy.data.scenes.remove(SC)
    SC=bpy.data.scenes.new('WANGJING_SOHO');bpy.context.window.scene=SC
    ASSET=collection('WJ_ASSET');CONTEXT=collection('WJ_CONTEXT');PREVIEW=collection('WJ_PREVIEW_ONLY')
    GEO=empty('GEO_ROOT',ASSET);CTXROOT=empty('DISTRICT_ROOT',CONTEXT)
    metadata=dict(geo_metadata_version=1,longitude_wgs84=R['anchor'][0],latitude_wgs84=R['anchor'][1],horizontal_crs='EPSG:4326',vertical_reference='WGS84_ELLIPSOID',coordinate_source='OSM site and tower footprints, Overpass snapshot 2026-10-18; origin near site centre',coordinate_accuracy='approximate',height_source='terrain_at_load',units='meters',local_origin='site_ground_center',height_m=200.)
    for k,v in metadata.items():GEO[k]=v
    SC.unit_settings.system='METRIC';SC.unit_settings.scale_length=1;SC.unit_settings.length_unit='METERS'
    for n,c,rough,metal,tx,em,st in [
        ('Aluminium_white',(.78,.79,.77),.28,0,None,None,0),('Soffit',(.23,.27,.28),.4,0,None,None,0),('Frame',(.07,.09,.10),.28,.75,None,None,0),('Glass_lowE',(.12,.2,.24),.22,0,'curtain-base.png','curtain-emissive.png',1.5),('Slab',(.32,.34,.34),.82,0,None,None,0),('Concrete',(.55,.56,.54),.8,0,'concrete-base.png',None,0),('Limestone',(.6,.58,.53),.73,0,'limestone-base.png',None,0),('Stone_dark',(.11,.13,.14),.55,0,None,None,0),('Asphalt',(.17,.18,.2),.92,0,'asphalt-base.png',None,0),('Grass',(.23,.3,.17),.9,0,'grass-base.png',None,0),('Bark',(.17,.11,.065),.96,0,None,None,0),('Leaves_0',(.16,.23,.08),.9,0,None,None,0),('Leaves_1',(.21,.29,.10),.9,0,None,None,0),('Leaves_2',(.10,.19,.075),.95,0,None,None,0),('Bench',(.24,.12,.055),.7,0,None,None,0),('Water',(.025,.105,.12),.13,0,None,None,0),('Landscape_light',(1,.67,.34),.35,0,None,None,2),('District_ground',(.42,.45,.41),.95,0,None,None,0)]:material(n,c,rough,metal,tx,em,st)
    for st in ['office','residential','concrete']:material(st+'_facade',(.6,.6,.6),.5,0,'district/'+st+'-base.png','district/'+st+'-emissive.png',1.2)
    material('Road_marking',(.7,.68,.58),.85);material('Car_0',(.07,.09,.105),.2);material('Car_1',(.6,.61,.58),.2);material('Car_2',(.16,.025,.015),.25)
    towers=[build_tower(t) for t in sorted(R['landmarks'],key=lambda x:x['id'])];site(towers);district()
    SC.world=bpy.data.worlds.new('WJ_Atmosphere');SC.render.engine='BLENDER_EEVEE';SC.render.resolution_x=1600;SC.render.resolution_y=1100;SC.render.resolution_percentage=100
    SC.render.image_settings.file_format='PNG';SC.render.fps=30;SC.frame_start=0;SC.frame_end=900;SC.view_settings.view_transform='AgX'
    try:SC.eevee.taa_render_samples=32;SC.eevee.use_raytracing=True
    except Exception:pass
    SUN=bpy.data.objects.new('WJ_Sun',bpy.data.lights.new('WJ_Sun','SUN'));PREVIEW.objects.link(SUN)
    FILL=bpy.data.objects.new('WJ_Softbox',bpy.data.lights.new('WJ_Softbox','AREA'));PREVIEW.objects.link(FILL);FILL.location=(-160,-100,300);FILL.data.shape='DISK';FILL.data.size=250;FILL.rotation_euler=(Vector((0,0,70))-FILL.location).to_track_quat('-Z','Y').to_euler()
    horizon=Mesh();horizon.face([(-15000,-15000,-.45),(15000,-15000,-.45),(15000,15000,-.45),(-15000,15000,-.45)],'District_ground');horizon.object('PREVIEW_horizon_ground',PREVIEW)
    CAMERAS={
        'hero':camera('CAM_hero',(-400,-520,180),(0,0,82),48),
        'low':camera('CAM_low',(-225,-320,34),(-10,0,85),32),
        'rear':camera('CAM_rear',(300,330,205),(0,0,75),45),
        'aerial':camera('CAM_aerial',(430,-380,470),(0,0,45),52),
        'district':camera('CAM_district',(2100,-2400,2600),(0,0,0),45,3400),
        'assembly':camera('CAM_assembly',(-610,-760,420),(0,0,185),43),
        'detail':camera('CAM_detail',(-72,-190,48),(-55,-50,54),55)}
    SC.camera=CAMERAS['hero'];lighting('blue')
    ROOT.joinpath('verification').mkdir(exist_ok=True);ROOT.joinpath('previews').mkdir(exist_ok=True)
    (ROOT/'placement.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'parts.json').write_text(json.dumps(dict(version=1,standard_id='CS-AM-1',coordinate_frame='gltf-local-y-up',units='meters',parts=PARTS),ensure_ascii=False,indent=2),encoding='utf-8')
    # Export the rest state before adding choreography. No preview lights/cameras.
    export(ASSET,ROOT/'wangjing-soho.glb');export(CONTEXT,OUT/'district.glb')
    bake('BUILD_ASSEMBLY');SC.frame_set(900);lighting('blue');SC.camera=CAMERAS['hero']
    bpy.ops.object.select_all(action='DESELECT')
    for im in bpy.data.images:
        if im.filepath and str(ROOT) in bpy.path.abspath(im.filepath):im.pack()
    for ar in bpy.context.screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_distance=650;ar.spaces.active.region_3d.view_location=(0,0,85);ar.spaces.active.clip_end=10000;ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.shading.color_type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wangjing-soho.blend'),compress=True)
    summary=dict(blender=bpy.app.version_string,parts=len(PARTS),asset_objects=len(ASSET.objects),context_objects=len(CONTEXT.objects),asset_triangles=sum(len(p.vertices)-2 for o in ASSET.objects if o.type=='MESH' for p in o.data.polygons),context_triangles=sum(len(p.vertices)-2 for o in CONTEXT.objects if o.type=='MESH' for p in o.data.polygons),materials=len(MAT))
    (ROOT/'verification'/'build.json').write_text(json.dumps(summary,indent=2));print('BUILD_COMPLETE',json.dumps(summary),flush=True)
if __name__=='__main__':main()
