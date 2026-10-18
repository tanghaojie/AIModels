"""Add sampled core glTF TRS tracks to the verified Blender rest export.

All parts share t=0. Rest transforms are preserved as assembled. No runtime plugin.
"""
from pathlib import Path
import json,struct,math,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose,gltf
OUT=ROOT.parents[1]/'model-assets'/'geo-context'/'wangjing-soho-1500-v1'
def read(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);b=bytearray(raw[28+n:]);return j,b
def write(path,j,b):
    b+=b'\0'*((-len(b))%4);j['buffers']=[{'byteLength':len(b)}]
    js=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
    temporary=path.with_suffix('.glb.tmp')
    temporary.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
    temporary.replace(path)
def export(clip,end,suffix):
    j,b=read(ROOT/'wangjing-soho.glb');nodes={x.get('name'):i for i,x in enumerate(j['nodes'])}
    def accessor(a,typ):
        a=np.asarray(a,dtype='<f4');b.extend(b'\0'*((-len(b))%4));offset=len(b);b.extend(a.tobytes());vi=len(j['bufferViews']);j['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=a.nbytes));ai=len(j['accessors']);acc=dict(bufferView=vi,componentType=5126,count=len(a),type=typ)
        if typ=='SCALAR':acc.update(min=[float(a.min())],max=[float(a.max())])
        j['accessors'].append(acc);return ai
    times=np.arange(int(end*30)+1,dtype=np.float32)/30;time=accessor(times,'SCALAR');samplers=[];channels=[]
    parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts'];lo=np.full(3,1e9);hi=-lo
    for p in parts:
        poses=[pose(p,float(t),clip) for t in times];position=np.array([gltf(x[0]) for x in poses]);scale=np.array([x[1] for x in poses]);rotation=np.array([[0,math.sin(x[2]/2),0,math.cos(x[2]/2)] for x in poses])
        lo=np.minimum(lo,position.min(axis=0));hi=np.maximum(hi,position.max(axis=0));idx=nodes[p['node_name']]
        if 'matrix' in j['nodes'][idx]:raise ValueError('Animated node has matrix')
        for values,path,typ in [(position,'translation','VEC3'),(scale,'scale','VEC3'),(rotation,'rotation','VEC4')]:
            a=accessor(values,typ);si=len(samplers);samplers.append(dict(input=time,output=a,interpolation='LINEAR'));channels.append(dict(sampler=si,target=dict(node=idx,path=path)))
    j['animations']=[dict(name=clip,samplers=samplers,channels=channels)]
    filename='wangjing-soho-'+suffix+'.glb';write(ROOT/filename,j,b)
    return dict(name=clip,file=filename,frame_start=0,frame_end=int(end*30),duration_s=end,hold_start_s=27 if suffix=='assembly' else 8,initial_state='empty_building' if suffix=='assembly' else 'assembled',final_state='assembled' if suffix=='assembly' else 'exploded',default_node_pose='assembled',loop=False,channels=len(channels),samples_per_channel=len(times),pivot_envelope_gltf_m=[lo.tolist(),hi.tolist()])
def tileset():
    lon,lat=116.47506,39.99547;l,p=math.radians(lon),math.radians(lat);a=6378137.;e2=.00669437999014;N=a/math.sqrt(1-e2*math.sin(p)**2)
    origin=[N*math.cos(p)*math.cos(l),N*math.cos(p)*math.sin(l),N*(1-e2)*math.sin(p)]
    north=[-math.sin(p)*math.cos(l),-math.sin(p)*math.sin(l),math.cos(p)];west=[math.sin(l),-math.cos(l),0];up=[math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p)]
    transform=[*north,0,*west,0,*up,0,*origin,1]
    d=dict(asset=dict(version='1.1',copyright='© OpenStreetMap contributors / ODbL-1.0. Facades and landscape by AIModels.'),geometricError=0,root=dict(boundingVolume=dict(box=[0,0,175,1501,0,0,0,1501,0,0,0,176]),transform=transform,geometricError=0,refine='REPLACE',content=dict(uri='district.glb')))
    (OUT/'tileset.json').write_text(json.dumps(d,indent=2))
    scene=dict(version=1,id='wangjing-soho-1500-v1',label='望京 SOHO · 半径 1500 米街区',anchor=dict(longitude_wgs84=lon,latitude_wgs84=lat),model=dict(url='https://jt-ai-models.vercel.app/models/wangjing-soho/wangjing-soho.glb'),context=dict(url='tileset.json',terrain='ellipsoid',maximum_anchor_distance_m=5),attribution=[dict(text='© OpenStreetMap contributors · ODbL',url='https://www.openstreetmap.org/copyright'),dict(text='Overture Maps Foundation · 2026-09-23.1',url='https://docs.overturemaps.org/attribution/'),dict(text='Qian Shi et al. East Asian Buildings · CC BY 4.0',url='https://doi.org/10.5281/zenodo.8174931')],notice='真实 OSM / Overture 轮廓及道路；缺失高度估算，立面为程序化近似。椭球高 0 是演示值，非实测地形。')
    (OUT/'scene.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    clips=[export('BUILD_ASSEMBLY',30,'assembly'),export('BUILD_EXPLODE',12,'explode')]
    (ROOT/'animation.json').write_text(json.dumps(dict(version=1,standard_id='CS-AM-1',fps=30,time_origin='clip_start_seconds',clips=clips,parts_file='parts.json',seed=7331,hover_height_m=85,descent_interval_s=[22,27],note='Production appendix; catalog v1 does not control animations'),indent=2))
    tileset();print(json.dumps(clips,indent=2))
if __name__=='__main__':main()
