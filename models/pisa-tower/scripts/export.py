"""Create independent single-clip animations from the Blender rest-pose GLB.
Preserve assembled default node transforms. Python + NumPy; no Blender required.
"""
from pathlib import Path
import json,struct,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose,gltf
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
OUT=ROOT.parents[1]/'model-assets'/'geo-context'/'pisa-1000-v1'

def read(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);size=struct.unpack_from('<I',raw,20+n)[0];return j,bytearray(raw[28+n:28+n+size])
def write(path,j,b):
    b+=b'\0'*((-len(b))%4);j['buffers']=[{'byteLength':len(b)}];js=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)

def animation(clip,duration,suffix):
    j,b=read(ROOT/'pisa-tower.glb');nodes={n.get('name'):i for i,n in enumerate(j['nodes'])}
    def accessor(a,typ):
        a=np.asarray(a,dtype='<f4');b.extend(b'\0'*((-len(b))%4));offset=len(b);b.extend(a.tobytes());vi=len(j['bufferViews']);j['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=a.nbytes));idx=len(j['accessors']);v=dict(bufferView=vi,componentType=5126,count=len(a),type=typ)
        if typ=='SCALAR':v.update(min=[float(a.min())],max=[float(a.max())])
        j['accessors'].append(v);return idx
    times=np.arange(round(duration*30)+1,dtype=np.float32)/30;time=accessor(times,'SCALAR');samplers=[];channels=[]
    parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts']
    for p in parts:
        idx=nodes[p['node_name']];node=j['nodes'][idx]
        if 'matrix' in node:
            expected=np.eye(4);expected[:3,3]=p['assembled']['translation_m']
            assert np.allclose(np.array(node['matrix']).reshape(4,4).T,expected,atol=.0001)
            del node['matrix'];node['translation']=p['assembled']['translation_m']
        poses=[pose(p,float(t),clip) for t in times]
        positions=np.array([gltf(a[0]) for a in poses]);scales=np.array([a[1] for a in poses]);rotations=np.array([[0,math.sin(a[2]/2),0,math.cos(a[2]/2)] for a in poses])
        for values,path,typ in [(positions,'translation','VEC3'),(scales,'scale','VEC3'),(rotations,'rotation','VEC4')]:
            si=len(samplers);samplers.append(dict(input=time,output=accessor(values,typ),interpolation='LINEAR'));channels.append(dict(sampler=si,target=dict(node=idx,path=path)))
    j['animations']=[dict(name=clip,samplers=samplers,channels=channels)];filename='pisa-tower-'+suffix+'.glb';write(ROOT/filename,j,b)
    return dict(file=filename,name=clip,frame_start=0,frame_end=round(duration*30),duration_s=duration,hold_start_s=24 if suffix=='assembly' else 9,initial_state='empty_building' if suffix=='assembly' else 'assembled',final_state='assembled' if suffix=='assembly' else 'exploded',default_node_pose='assembled',loop=False,channels=len(channels),samples_per_channel=len(times))

def tileset():
    lon,lat=CFG['longitude'],CFG['latitude'];l,p=math.radians(lon),math.radians(lat);a=6378137.;e2=.00669437999014;N=a/math.sqrt(1-e2*math.sin(p)**2)
    origin=[N*math.cos(p)*math.cos(l),N*math.cos(p)*math.sin(l),N*(1-e2)*math.sin(p)]
    north=[-math.sin(p)*math.cos(l),-math.sin(p)*math.sin(l),math.cos(p)];west=[math.sin(l),-math.cos(l),0];up=[math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p)]
    # glTF Y-up->3D Tiles Z-up is performed by the standard tile content transform.
    transform=[*north,0,*west,0,*up,0,*origin,1]
    d=dict(asset=dict(version='1.1',copyright='© OpenStreetMap contributors / ODbL-1.0; AIModels architectural reconstruction'),geometricError=2000,root=dict(boundingVolume=dict(box=[0,0,25,1002,0,0,0,1002,0,0,0,26]),transform=transform,geometricError=0,refine='REPLACE',content=dict(uri='district.glb')))
    (OUT/'tileset.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8',newline='\n')
    scene=dict(version=1,id='pisa-1000-v1',label='比萨 · 半径1000米真实轮廓街区',anchor=dict(longitude_wgs84=lon,latitude_wgs84=lat),model=dict(url='https://jt-ai-models.vercel.app/models/pisa-tower/pisa-tower.glb'),context=dict(url='tileset.json',terrain='ellipsoid',maximum_anchor_distance_m=5),attribution=[dict(text='© OpenStreetMap contributors · ODbL-1.0',url='https://www.openstreetmap.org/copyright')],notice='真实建筑/路网轮廓；多数高度、屋面、立面为展示估算；椭球高0为演示值。')
    (OUT/'scene.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

def main():
    clips=[animation('BUILD_ASSEMBLY',28,'assembly'),animation('BUILD_EXPLODE',12,'explode')]
    (ROOT/'animation.json').write_text(json.dumps(dict(version=1,standard_id='CS-AM-1',fps=30,time_origin='clip_start_seconds',clips=clips,parts_file='parts.json',seed=1173),ensure_ascii=False,indent=2),encoding='utf-8')
    tileset();print(json.dumps(clips,indent=2))
if __name__=='__main__':main()
