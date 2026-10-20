"""Deterministic UV-derived tangents: avoid threaded exporter accumulation drift.
All positions, normals, UVs, indices, images and materials remain untouched.
"""
from pathlib import Path
import json,struct
import numpy as np

def canonicalize(path):
    path=Path(path);raw=bytearray(path.read_bytes());size=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+size]);base=28+size
    def view(index):
        a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],n),dtype=dtype,buffer=raw,offset=base+v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*item),item))
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            a=p['attributes']
            if not all(k in a for k in ['POSITION','NORMAL','TEXCOORD_0','TANGENT']):continue
            xyz=view(a['POSITION']).astype(np.float64);normal=view(a['NORMAL']).astype(np.float64);uv=view(a['TEXCOORD_0']).astype(np.float64);idx=view(p['indices']).ravel().astype(np.int64).reshape(-1,3)
            e1=xyz[idx[:,1]]-xyz[idx[:,0]];e2=xyz[idx[:,2]]-xyz[idx[:,0]];d1=uv[idx[:,1]]-uv[idx[:,0]];d2=uv[idx[:,2]]-uv[idx[:,0]];det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0];good=np.abs(det)>1e-15;inv=np.zeros_like(det);inv[good]=1/det[good]
            t=(e1*d2[:,1,None]-e2*d1[:,1,None])*inv[:,None];bt=(e2*d1[:,0,None]-e1*d2[:,0,None])*inv[:,None]
            tan=np.zeros_like(xyz);bitan=np.zeros_like(xyz)
            for corner in range(3):np.add.at(tan,idx[:,corner],t);np.add.at(bitan,idx[:,corner],bt)
            normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-30)
            tan-=normal*np.sum(tan*normal,axis=1)[:,None];length=np.linalg.norm(tan,axis=1);bad=length<1e-12
            if np.any(bad):
                ref=np.tile([0.,0.,1.],(bad.sum(),1));n=normal[bad];ref[np.abs(n[:,2])>.9]=[0,1,0];tan[bad]=np.cross(ref,n);length=np.linalg.norm(tan,axis=1)
            tan/=np.maximum(length[:,None],1e-30);sign=np.where(np.sum(np.cross(normal,tan)*bitan,axis=1)<0,-1.,1.)
            view(a['TANGENT'])[:]=np.column_stack((tan,sign)).astype('<f4')
    path.write_bytes(raw)

if __name__=='__main__':
    import sys
    for p in sys.argv[1:]:canonicalize(p);print('Canonical tangents:',p)
