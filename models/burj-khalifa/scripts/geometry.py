"""Small explicit-mesh toolkit: metre UVs, outward normals, solid components."""
import bpy,math
from mathutils import Vector
MAT=[];MI={}
def material(name,color,rough=.5,metal=0,texture=None,emission=None,strength=0,orm=None):
    m=bpy.data.materials.new('BK_'+name);m.use_nodes=True;m.use_backface_culling=True
    m.diffuse_color=(*color,1);bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    def img(path,space):
        im=bpy.data.images.load(str(path),check_existing=True);im.colorspace_settings.name=space
        node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;return node
    if texture:m.node_tree.links.new(img(texture,'sRGB').outputs['Color'],bs.inputs['Base Color'])
    if emission:m.node_tree.links.new(img(emission,'sRGB').outputs['Color'],bs.inputs['Emission Color'])
    if strength:
        bs.inputs['Emission Strength'].default_value=strength
        if not emission:bs.inputs['Emission Color'].default_value=(*color,1)
    if orm:
        node=img(orm,'Non-Color');sep=m.node_tree.nodes.new('ShaderNodeSeparateColor')
        m.node_tree.links.new(node.outputs['Color'],sep.inputs[0]);m.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness']);m.node_tree.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    MI[name]=len(MAT);MAT.append(m);return m
class Mesh:
    def __init__(self):self.v=[];self.f=[];self.m=[];self.uv=[];self.sm=[]
    def face(self,pts,mat,uv=None,smooth=False):
        k=len(self.v);self.v.extend(tuple(p) for p in pts);self.f.append(tuple(range(k,k+len(pts))));self.m.append(MI[mat] if isinstance(mat,str) else mat);self.sm.append(smooth)
        self.uv.extend(uv or [(p[0]/4,p[1]/4) for p in pts])
    def quad(self,a,b,c,d,mat,uv=None,smooth=False):self.face([a,b,c,d],mat,uv,smooth)
    def box(self,center,size,mat,angle=0):
        x,y,z=center;a,b,c=[s/2 for s in size];co,si=math.cos(angle),math.sin(angle)
        p=[(x+co*i-si*j,y+si*i+co*j,z+k) for i,j,k in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
        for ids in [(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:self.face([p[i] for i in ids],mat)
    def poly(self,p,z,mat,flip=False):
        v=p['points']
        for tri in p['triangles']:self.face([(v[i][0],v[i][1],z) for i in (tri[::-1] if flip else tri)],mat)
    def extrude(self,p,z,h,wall,roof,uvscale=12,bottom=False):
        self.poly(p,z+h,roof)
        if bottom:self.poly(p,z,roof,True)
        v=p['points'];off=0
        for count in p['rings']:
            for j in range(count):
                a,b=v[off+j],v[off+(j+1)%count];w=math.dist(a,b)
                self.quad((*a,z),(*b,z),(*b,z+h),(*a,z+h),wall,[(0,0),(w/uvscale,0),(w/uvscale,h/uvscale),(0,h/uvscale)])
            off+=count
    def object(self,name,coll,parent=None,pivot=(0,0,0)):
        if not self.f:return None
        p=Vector(pivot);me=bpy.data.meshes.new(name);me.from_pydata([Vector(v)-p for v in self.v],[],self.f);me.update()
        used=sorted(set(self.m));remap={n:i for i,n in enumerate(used)}
        for n in used:me.materials.append(MAT[n])
        for poly,ma,sm in zip(me.polygons,self.m,self.sm):poly.material_index=remap[ma];poly.use_smooth=sm
        uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',[c for pair in self.uv for c in pair])
        ob=bpy.data.objects.new(name,me);coll.objects.link(ob);ob.parent=parent;ob.location=p;return ob
def tube(mesh,pts,r,mat,sides=6):
    for a,b in zip(pts[:-1],pts[1:]):
        a,b=Vector(a),Vector(b)
        if (b-a).length<1e-5:continue
        axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.01:u=axis.cross(Vector((0,1,0)))
        u.normalize();v=axis.cross(u);A=[];B=[]
        for j in range(sides):
            d=(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides))*r;A.append(a+d);B.append(b+d)
        for j in range(sides):k=(j+1)%sides;mesh.quad(A[j],A[k],B[k],B[j],mat,smooth=True)
        mesh.face(A[::-1],mat);mesh.face(B,mat)
def disk(mesh,c,r,z,h,mat,n=48):
    p=dict(points=[(c[0]+r*math.cos(j*math.tau/n),c[1]+r*math.sin(j*math.tau/n)) for j in range(n)],rings=[n],triangles=[[0,j,j+1] for j in range(1,n-1)])
    mesh.extrude(p,z,h,mat,mat,bottom=True)
def palm(mesh,x,y,h=9,angle=0):
    tube(mesh,[(x,y,.15),(x+.2,y-.1,h*.65),(x+.5,y,h)],.22,'Bark',7)
    for j in range(9):
        a=angle+j*math.tau/9;d=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0));c=Vector((x+.5,y,h));prev=c
        for k in range(1,5):
            t=k/4;mid=c+d*(3.4*t)+Vector((0,0,1.1*math.sin(t*math.pi)-t*.8));w=.7*math.sin(t*math.pi)*.65+.04
            mesh.quad(prev-side*w,mid-side*w,mid+side*w,prev+side*w,'Palm_leaf',smooth=True)
            # The leaf mesh is a solid narrow wedge, not global double-sided.
            mesh.quad(prev+side*w-Vector((0,0,.035)),mid+side*w-Vector((0,0,.035)),mid-side*w-Vector((0,0,.035)),prev-side*w-Vector((0,0,.035)),'Palm_leaf',smooth=True)
            prev=mid
