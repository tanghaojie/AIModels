"""Audit exported binaries, exact endpoints, common time and full motion envelope."""
from pathlib import Path
import json,struct,hashlib,sys,itertools,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from export import read
from motion import pose,gltf
OUT=ROOT.parents[1]/'model-assets/geo-context'/'pisa-1000-v1'

def acc(j,b,i):
    a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];size=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],c),dtype=dtype,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*size),size)).copy()

def main():
    results=[];parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts'];static,sb=read(ROOT/'pisa-tower.glb');sn={n.get('name'):n for n in static['nodes']}
    assert len({p['part_id'] for p in parts})==len(parts)
    for path in [ROOT/'pisa-tower.glb',ROOT/'pisa-tower-assembly.glb',ROOT/'pisa-tower-explode.glb',OUT/'district.glb']:
        j,b=read(path);raw=path.read_bytes();assert struct.unpack_from('<I',raw,8)[0]==len(raw)
        assert all('uri' not in v for v in j.get('buffers',[])+j.get('images',[]))
        assert not j.get('cameras') and 'KHR_lights_punctual' not in j.get('extensionsUsed',[])
        triangles=0;primitives=0
        for m in j['meshes']:
            for p in m['primitives']:
                primitives+=1;attrs=p['attributes'];assert 'NORMAL' in attrs
                triangles+=j['accessors'][p['indices']]['count']//3
                mat=j['materials'][p['material']];pbr=mat.get('pbrMetallicRoughness',{})
                if 'baseColorTexture' in pbr:assert 'TEXCOORD_0' in attrs
                assert np.isfinite(acc(j,b,attrs['POSITION'])).all()
        metadata=[n for n in j['nodes'] if 'longitude_wgs84' in n.get('extras',{})]
        if path.parent==ROOT:
            assert len(metadata)==1 and metadata[0]['name']=='GEO_ROOT';assert 'ellipsoid_height_m' not in metadata[0]['extras']
        endpoint={};rootchannels=0
        if j.get('animations'):
            assert len(j['animations'])==1;animation=j['animations'][0];expected='BUILD_ASSEMBLY' if 'assembly' in path.name else 'BUILD_EXPLODE';assert animation['name']==expected
            duration=28 if expected=='BUILD_ASSEMBLY' else 12;nodes={n.get('name'):n for n in j['nodes']}
            for p in parts:
                n=nodes[p['node_name']];assert 'matrix' not in n;assert np.allclose(n.get('translation',[0,0,0]),sn[p['node_name']].get('translation',[0,0,0]),atol=.00001)
            maxerr=0;maxhold=0
            for c in animation['channels']:
                target=j['nodes'][c['target']['node']];rootchannels+=target['name']=='GEO_ROOT';sam=animation['samplers'][c['sampler']];times=acc(j,b,sam['input']).ravel();values=acc(j,b,sam['output']);assert times[0]==0 and np.all(np.diff(times)>0) and abs(times[-1]-duration)<1e-5
                assert np.isfinite(values).all();pathkey=c['target']['path']
                rest=sn[target['name']].get(pathkey,{'translation':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}[pathkey])
                ref=values[-1] if expected=='BUILD_ASSEMBLY' else values[0];maxerr=max(maxerr,float(np.max(np.abs(ref-rest))))
                hold=values[times>=(24 if expected=='BUILD_ASSEMBLY' else 9)];maxhold=max(maxhold,float(np.max(np.abs(hold-hold[0]))))
            assert rootchannels==0 and maxerr<.001 and maxhold<1e-5
            endpoint=dict(maximum_component_error=maxerr,hold_drift=maxhold,root_channels=rootchannels,duration_s=duration,channels=len(animation['channels']))
        else:assert path.name in ['pisa-tower.glb','district.glb']
        report=json.loads((ROOT/'verification'/(path.name+'.validator.json')).read_text())
        assert report['issues']['numErrors']==0 and report['issues']['numWarnings']==0
        results.append(dict(file=path.relative_to(ROOT.parents[1]).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),triangles=triangles,nodes=len(j['nodes']),meshes=len(j['meshes']),primitives=primitives,materials=len(j['materials']),images=len(j.get('images',[])),extensions=j.get('extensionsUsed',[]),validator_errors=0,validator_warnings=0,animation=endpoint))
    # Conservative per-part mesh AABBs, transformed at every exported frame.
    byname={n.get('name'):i for i,n in enumerate(static['nodes'])}
    def bounds(idx):
        n=static['nodes'][idx];v=[]
        if 'mesh' in n:
            for p in static['meshes'][n['mesh']]['primitives']:
                a=static['accessors'][p['attributes']['POSITION']];v.extend(itertools.product(*zip(a['min'],a['max'])))
        for i in n.get('children',[]):v.extend(bounds(i))
        return v
    motion={};partlookup={p['part_id']:p for p in parts}
    for p in parts:
        for dep in p['assembly']['depends_on']:assert partlookup[dep]['end_s']<=p['end_s']
    for clip,dur in [('BUILD_ASSEMBLY',28),('BUILD_EXPLODE',12)]:
        lo=np.full(3,np.inf);hi=-lo
        for p in parts:
            v=np.array(bounds(byname[p['node_name']]));box=np.array(list(itertools.product(*zip(v.min(0),v.max(0)))))
            for frame in range(dur*30+1):
                loc,scale,ang=pose(p,frame/30,clip);c,s=math.cos(ang),math.sin(ang);rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
                points=(box*np.array(scale))@rot.T+gltf(loc);lo=np.minimum(lo,points.min(0));hi=np.maximum(hi,points.max(0))
            for t in [0,dur*.25,dur*.5,dur*.75,dur]:
                before=pose(p,t,clip)
                for other in [dur,0,dur*.17]:pose(p,other,clip)
                assert before==pose(p,t,clip)
        motion[clip]=dict(envelope_gltf_m=[lo.tolist(),hi.tolist()],sampled_fps=30,random_sampling_pause_replay='deterministic pure function')
    active=max(sum(p['start_s']<=t<p['end_s'] for p in parts) for t in np.arange(0,28,1/30))
    sectors=sorted({int(((math.atan2(p['spawn_blender'][1]-p['assembled_blender'][1],p['spawn_blender'][0]-p['assembled_blender'][0])+math.pi)*8/math.tau))%8 for p in parts})
    assert len(sectors)==8 and all(pose(p,0)[1]==[.0001]*3 for p in parts)
    total=dict(files=results,parts=len(parts),peak_moving_parts=int(active),flight_octants=sectors,root_fixed=True,motion=motion,limitations=['Conservative AABBs do not prove collision-free physical assembly; artistic paths and schematic interior.','No target-engine browser/GPU acceptance performed.','Terrain height is ellipsoid demonstration zero, not surveyed.'])
    (ROOT/'verification/asset-audit.json').write_text(json.dumps(total,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(parts=len(parts),peak_moving_parts=int(active),flight_octants=sectors,files=[dict(file=p['file'],triangles=p['triangles'],bytes=p['bytes'],animation=p['animation']) for p in results],motion=motion),indent=2))
if __name__=='__main__':main()
