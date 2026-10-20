"""Core glTF TRS sampled from the same motion as the editable Blender source."""
from common import *
from motion import pose,gltf
import numpy as np
import struct,math
def read(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]),bytearray(raw[28+n:])
def write_glb(path,j,b):
    b+=b'\0'*((-len(b))%4);j['buffers']=[dict(byteLength=len(b))]
    js=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
def export(clip,end,suffix):
    j,b=read(ROOT/'burj-khalifa.glb');nodes={x.get('name'):i for i,x in enumerate(j['nodes'])}
    def acc(a,typ):
        a=np.asarray(a,dtype='<f4');b.extend(b'\0'*((-len(b))%4));offset=len(b);b.extend(a.tobytes());vi=len(j['bufferViews']);j['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=a.nbytes));ai=len(j['accessors']);a0=dict(bufferView=vi,componentType=5126,count=len(a),type=typ)
        if typ=='SCALAR':a0.update(min=[float(a.min())],max=[float(a.max())])
        j['accessors'].append(a0);return ai
    times=np.arange(int(end*30)+1,dtype=np.float32)/30;ti=acc(times,'SCALAR');samplers=[];channels=[]
    parts=json.loads((ROOT/'parts.json').read_text())['parts']
    for p in parts:
        poses=[pose(p,float(t),clip) for t in times]
        outputs=[(np.array([gltf(x[0]) for x in poses]),'translation','VEC3'),(np.array([x[1] for x in poses]),'scale','VEC3'),(np.array([[0,math.sin(x[2]/2),0,math.cos(x[2]/2)] for x in poses]),'rotation','VEC4')]
        ni=nodes[p['node_name']];assert 'matrix' not in j['nodes'][ni]
        for values,target,typ in outputs:
            ai=acc(values,typ);si=len(samplers);samplers.append(dict(input=ti,output=ai,interpolation='LINEAR'));channels.append(dict(sampler=si,target=dict(node=ni,path=target)))
    j['animations']=[dict(name=clip,samplers=samplers,channels=channels)]
    name='burj-khalifa-'+suffix+'.glb';write_glb(ROOT/name,j,b)
    return dict(file=name,name=clip,frame_start=0,frame_end=int(end*30),duration_s=end,hold_start_s=32 if suffix=='assembly' else 10,initial_state='empty_building' if suffix=='assembly' else 'assembled',final_state='assembled' if suffix=='assembly' else 'exploded',default_node_pose='assembled',loop=False,channels=len(channels),samples_per_channel=len(times))
def tileset():
    lon,lat=CFG['anchor'];l,p=math.radians(lon),math.radians(lat);a=6378137;e2=.00669437999014;N=a/math.sqrt(1-e2*math.sin(p)**2)
    origin=[N*math.cos(p)*math.cos(l),N*math.cos(p)*math.sin(l),N*(1-e2)*math.sin(p)]
    north=[-math.sin(p)*math.cos(l),-math.sin(p)*math.sin(l),math.cos(p)];west=[math.sin(l),-math.cos(l),0];up=[math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p)]
    write(CONTEXT/'tileset.json',dict(asset=dict(version='1.1',copyright='© OpenStreetMap contributors · ODbL-1.0; original surface materials AIModels'),geometricError=4000,root=dict(boundingVolume=dict(box=[0,0,240,2002,0,0,0,2002,0,0,0,242]),transform=[*north,0,*west,0,*up,0,*origin,1],geometricError=0,refine='REPLACE',content=dict(uri='district.glb'))))
    write(CONTEXT/'scene.json',dict(version=1,id='burj-khalifa-2000-v1',label='Burj Khalifa · Downtown Dubai 2000 m',anchor=dict(longitude_wgs84=lon,latitude_wgs84=lat),model=dict(url='https://jt-ai-models.vercel.app/models/burj-khalifa/burj-khalifa.glb'),context=dict(url='tileset.json',terrain='ellipsoid',maximum_anchor_distance_m=5),attribution=[dict(text='© OpenStreetMap contributors · ODbL',url='https://www.openstreetmap.org/copyright')],notice='Actual OSM outlines and roads; missing heights estimated. Ellipsoid height 0 is for display, not surveyed ground.'))
def main():
    clips=[export('BUILD_ASSEMBLY',36,'assembly'),export('BUILD_EXPLODE',14,'explode')]
    write(ROOT/'animation.json',dict(version=1,standard_id='CS-AM-1',fps=30,time_origin='clip_start_seconds',clips=clips,parts_file='parts.json',seed=CFG['seed'],hover_height_m=120,descent_interval_s=[27,32],note='Production appendix; modes are declared in model.source.json'))
    tileset();print('EXPORTED_ANIMATIONS',clips,flush=True)
if __name__=='__main__':main()
