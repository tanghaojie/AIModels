"""Broad-phase clearance against saved neighbour footprints and approximate heights.
This is stricter than visual spot checks but not an exact mesh collision solver.
"""
from pathlib import Path
import json,sys,itertools,math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from export import read
from motion import pose,gltf
def main():
    r=json.loads((ROOT/'recipe.json').read_text(encoding='utf-8'));parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))['parts'];j,b=read(ROOT/'pisa-tower.glb');by={n.get('name'):n for n in j['nodes']}
    neighbors=r['buildings']+[p for p in r['landmarks'] if p['osm_id']!=12982355]
    polys=[Polygon(p['points'][:p['rings'][0]]) for p in neighbors];heights=[p.get('height',47 if p['osm_id']==22945163 else 44 if p['osm_id']==22945162 else 13)+3 for p in neighbors];tree=STRtree(polys);hits=[]
    for p in parts:
        n=by[p['node_name']];child=j['nodes'][n['children'][0]];prims=j['meshes'][child['mesh']]['primitives'];lo=np.min([j['accessors'][a['attributes']['POSITION']]['min'] for a in prims],axis=0);hi=np.max([j['accessors'][a['attributes']['POSITION']]['max'] for a in prims],axis=0);corn=np.array(list(itertools.product(*zip(lo,hi))));found=[]
        for t in np.arange(p['start_s'],p['end_s'],.05):
            loc,s,ang=pose(p,float(t));c,ss=math.cos(ang),math.sin(ang);rot=np.array([[c,0,ss],[0,1,0],[-ss,0,c]]);vv=(corn*np.array(s))@rot.T+gltf(loc);xy=box(vv[:,0].min(),-vv[:,2].max(),vv[:,0].max(),-vv[:,2].min());ids=tree.query(xy,predicate='intersects');found.extend(int(i) for i in ids if vv[:,1].min()<heights[i] and vv[:,1].max()>0)
        if found:hits.append(dict(part_id=p['part_id'],conservative_aabb_neighbor_hits=len(set(found))))
    result=dict(method='Conservative part AABB vs approximate neighbor footprint/height, 20 Hz during active flight',clearance_repaired_parts=sum(bool(p.get('clearance_height_m')) for p in parts),clearance_height_m=85,parts_with_possible_overlap=hits,physical_collision_free_claim=False,note='No broad-phase neighbour overlap after clearance repair; not exact part-vs-part or physical construction validation.' if not hits else 'Broad-phase candidate overlaps remain; inspect before acceptance.')
    (ROOT/'verification/path-clearance.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2));assert not hits
if __name__=='__main__':main()
