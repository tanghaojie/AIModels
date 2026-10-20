"""Small deterministic mesh builder with explicit per-loop metric UVs."""
import math
import bpy
from mathutils import Vector
TAU=math.tau

class Mesh:
    def __init__(self,materials):self.v=[];self.f=[];self.ma=[];self.uv=[];self.sm=[];self.materials=materials
    def face(self,pts,mat,uv=None,smooth=False):
        if len(pts)<3:return
        k=len(self.v);self.v.extend(tuple(v) for v in pts);self.f.append(tuple(range(k,k+len(pts))));self.ma.append(mat);self.sm.append(smooth)
        if uv is None:
            n=(Vector(pts[1])-Vector(pts[0])).cross(Vector(pts[2])-Vector(pts[0]));axis=max(range(3),key=lambda i:abs(n[i]));axes=[i for i in range(3) if i!=axis];uv=[(p[axes[0]]/4,p[axes[1]]/4) for p in pts]
        self.uv.extend(uv)
    def box(self,c,size,mat,angle=0):
        x,y,z=c;a,b,d=[s/2 for s in size];co,si=math.cos(angle),math.sin(angle)
        p=[(x+co*i-si*j,y+si*i+co*j,z+k) for i,j,k in [(-a,-b,-d),(a,-b,-d),(a,b,-d),(-a,b,-d),(-a,-b,d),(a,-b,d),(a,b,d),(-a,b,d)]]
        for q in [(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:self.face([p[i] for i in q],mat)
    def lathe(self,c,profile,mat,n=24,start=0,end=TAU,closed=False):
        x,y,z=c
        for j in range(n):
            a,b=start+(end-start)*j/n,start+(end-start)*(j+1)/n
            for k in range(len(profile)-1):
                r0,z0=profile[k];r1,z1=profile[k+1]
                self.face([(x+r0*math.cos(a),y+r0*math.sin(a),z+z0),(x+r0*math.cos(b),y+r0*math.sin(b),z+z0),(x+r1*math.cos(b),y+r1*math.sin(b),z+z1),(x+r1*math.cos(a),y+r1*math.sin(a),z+z1)],mat,[(a*r0/4,(z+z0)/4),(b*r0/4,(z+z0)/4),(b*r1/4,(z+z1)/4),(a*r1/4,(z+z1)/4)],smooth=True)
        if closed:
            for a,rev in [(start,True),(end,False)]:
                p=[(x+r*math.cos(a),y+r*math.sin(a),z+h) for r,h in profile]
                self.face(list(reversed(p)) if rev else p,mat)
    def ring(self,ri,ro,z,h,mat,start=0,end=TAU,n=96,c=(0,0)):
        profile=[(ri,0),(ro,0),(ro,h),(ri,h),(ri,0)]
        self.lathe((*c,z),profile,mat,n,start,end,closed=end-start<TAU-.001)
    def column(self,c,h,mat,detail=True,r=.23):
        x,y,z=c
        prof=[(0,0),(r*1.5,0),(r*1.5,.11),(r*1.2,.11),(r*1.2,.19),(r,.25),(r*.95,.4),(r*.99,h*.35),(r*.88,h-.55),(r*1.05,h-.5),(r*1.05,h-.43),(r*1.4,h-.38),(r*1.5,h-.12),(r*1.5,h),(0,h)]
        self.lathe(c,prof,mat,16 if detail else 12)
        self.box((x,y,z+h-.08),(r*3.3,r*3.3,.16),mat)
        if detail:
            # Visible layered foliage and paired volutes; interpretation, not sculptural scan.
            for j in range(8):
                a=j*TAU/8
                p=[(x+r*.85*math.cos(a-.2),y+r*.85*math.sin(a-.2),z+h-.48),(x+r*1.45*math.cos(a),y+r*1.45*math.sin(a),z+h-.2),(x+r*.85*math.cos(a+.2),y+r*.85*math.sin(a+.2),z+h-.48),(x+r*.72*math.cos(a),y+r*.72*math.sin(a),z+h-.52)]
                self.face(p,mat);self.face(list(reversed(p)),mat)
                self.lathe((x+r*1.16*math.cos(a),y+r*1.16*math.sin(a),z+h-.22),[(0,0),(.075,0),(.085,.07),(.055,.13),(0,.13)],mat,8)
    def arch(self,c,width,spring,depth,band,mat,angle=0,n=16,spandrel=True):
        # Extruded voussoir wedges in a vertical plane; local horizontal axis is tangent.
        x,y,z=c;r=width/2;co,si=math.cos(angle),math.sin(angle)
        def p(u,v,w):return (x+co*u-si*v,y+si*u+co*v,z+w)
        for i in range(n):
            a,b=math.pi*i/n,math.pi*(i+1)/n
            r1=r+band
            coords=[(r*math.cos(a),spring+r*math.sin(a)),(r*math.cos(b),spring+r*math.sin(b)),(r1*math.cos(b),spring+r1*math.sin(b)),(r1*math.cos(a),spring+r1*math.sin(a))]
            front=[p(u,-depth/2,w) for u,w in coords];back=[p(u,depth/2,w) for u,w in coords]
            self.face(front[::-1],mat);self.face(back,mat)
            for j in range(4):k=(j+1)%4;self.face([front[j],front[k],back[k],back[j]],mat)
            if spandrel:
                u0,u1=r1*math.cos(a),r1*math.cos(b);w0,w1=spring+r1*math.sin(a),spring+r1*math.sin(b);top=spring+r1+.16
                if abs(u1-u0)>1e-6:
                    self.face([p(u0,-depth/2,top),p(u1,-depth/2,top),p(u1,-depth/2,w1),p(u0,-depth/2,w0)],mat)
                    self.face([p(u0,depth/2,w0),p(u1,depth/2,w1),p(u1,depth/2,top),p(u0,depth/2,top)],mat)
    def sphere(self,c,r,mat,n=12,m=8,scale=(1,1,1)):
        x,y,z=c
        for k in range(m):
            a=-math.pi/2+math.pi*k/m;b=-math.pi/2+math.pi*(k+1)/m
            for j in range(n):
                p=[]
                for h,t in [(a,j*TAU/n),(a,(j+1)*TAU/n),(b,(j+1)*TAU/n),(b,j*TAU/n)]:p.append((x+r*math.cos(h)*math.cos(t)*scale[0],y+r*math.cos(h)*math.sin(t)*scale[1],z+r*math.sin(h)*scale[2]))
                self.face(p,mat,smooth=True)
    def poly(self,p,z,mat):
        v=p['points']
        for tri in p['triangles']:self.face([(*v[i],z if isinstance(z,(int,float)) else z[i]) for i in tri],mat)
    def extrude(self,p,z,h,wall,roof,uvscale=16):
        self.poly(p,z+h,roof);v=p['points'];off=0
        for count in p['rings']:
            dist=0
            for j in range(count):
                a,b=v[off+j],v[off+(j+1)%count];w=math.dist(a,b)
                vs=4 if wall=='Marble' else 12
                self.face([(*a,z),(*b,z),(*b,z+h),(*a,z+h)],wall,[(dist/uvscale,z/vs),((dist+w)/uvscale,z/vs),((dist+w)/uvscale,(z+h)/vs),(dist/uvscale,(z+h)/vs)])
                dist+=w
            off+=count
    def object(self,name,collection,parent=None,pivot=(0,0,0),warp=None):
        if not self.f:return None
        p=Vector(pivot);vv=[tuple(Vector(warp(v) if warp else v)-p) for v in self.v]
        # Weld shared positions, retaining UV seams as loop data.
        unique={};verts=[];lookup=[]
        for v in vv:
            key=tuple(round(x,7) for x in v)
            if key not in unique:unique[key]=len(verts);verts.append(v)
            lookup.append(unique[key])
        faces=[];mats=[];sm=[];uvs=[];off=0
        for ids,ma,s in zip(self.f,self.ma,self.sm):
            uv=self.uv[off:off+len(ids)];off+=len(ids);ii=tuple(lookup[i] for i in ids)
            clean=[];clean_uv=[]
            for index,u in zip(ii,uv):
                if index not in clean:clean.append(index);clean_uv.append(u)
            if len(clean)<3:continue
            faces.append(tuple(clean));mats.append(ma);sm.append(s);uvs.extend(clean_uv)
        me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
        used=list(dict.fromkeys(mats));indices={a:i for i,a in enumerate(used)}
        for a in used:me.materials.append(self.materials[a])
        for f,ma,s in zip(me.polygons,mats,sm):f.material_index=indices[ma];f.use_smooth=s
        uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',[v for u in uvs for v in u])
        me.validate(verbose=False,clean_customdata=False);me.update()
        ob=bpy.data.objects.new(name,me);collection.objects.link(ob);ob.parent=parent;ob.location=p
        return ob
