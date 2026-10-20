"""Asset, determinism, dependency, material and motion audits (no browser)."""
from common import *
from motion import pose,gltf
from export_animation import read
import numpy as np,math,hashlib,collections
from shapely.geometry import Polygon
from shapely.ops import unary_union
recipe=json.loads((ROOT/'recipe.json').read_text(encoding='utf-8'))
def poly(data):
    rings=[];offset=0
    for count in data['rings']:rings.append(data['points'][offset:offset+count]);offset+=count
    return Polygon(rings[0],rings[1:])
water=unary_union([poly(p) for p in recipe['land'] if p['kind']=='water'])
ground=unary_union([poly(p) for p in recipe['ground']])
assert ground.intersection(water).area<1e-5,'Ground overlaps the lakes'
tri_area=0
for data in recipe['ground']:
    pts=data['points']
    for tri in data['triangles']:
        triangle=Polygon([pts[i] for i in tri]);tri_area+=triangle.area
        assert triangle.intersection(water).area<1e-4,'Ground triangulation crosses a water hole'
assert abs(tri_area-ground.area)<.01
write(ROOT/'verification'/'ground-audit.json',dict(status='passed',ground_area_m2=ground.area,water_area_m2=water.area,overlap_area_m2=ground.intersection(water).area,triangulated_ground_area_m2=tri_area,preview_horizon='annular; no plane under the district',camera_near_m=5))
parts=json.loads((ROOT/'parts.json').read_text())['parts'];ids={p['part_id']:p for p in parts}
assert len(ids)==len(parts)
for p in parts:
    for dep in p['assembly']['depends_on']:assert dep in ids
    assert p['end_s']<=25
    assert p['parent_node_name']=='GEO_ROOT'
    # Dependency must complete before the dependent's completion, allowing
    # staggered parallel travel on separate approach corridors.
    for dep in p['assembly']['depends_on']:assert ids[dep]['end_s']<=p['end_s']
    assert np.allclose(pose(p,36)[0],p['assembled_blender'],atol=1e-9)
    assert pose(p,0)[1]==[.0001]*3
    assert pose(p,32)==pose(p,36)
    flight=[pose(p,t)[0][2] for t in np.linspace(p['start_s'],p['end_s'],60)]
    assert all(a>=b-1e-6 for a,b in zip(flight,flight[1:]))
    assert np.allclose(np.array(pose(p,27)[0])-pose(p,32)[0],[0,0,120])
    assert pose(p,0,'BUILD_EXPLODE')[0]==p['assembled_blender']
    for t in [0,.5,1,5,9,13,20,24,27,29.3,32,36]:
        # Same-time sampling after arbitrary seeks must not depend on history.
        first=pose(p,t);pose(p,36-t);assert first==pose(p,t)
j,b=read(ROOT/'burj-khalifa.glb');nodes={n['name']:n for n in j['nodes']}
assert len([n for n in j['nodes'] if 'longitude_wgs84' in n.get('extras',{})])==1
assert nodes['GEO_ROOT'].get('translation',[0,0,0])==[0,0,0]
assert not any('PREVIEW' in n.get('name','') or n.get('camera') is not None for n in j['nodes'])
nodebounds={}
for p in parts:
    n=nodes[p['node_name']];children=[j['nodes'][i] for i in n.get('children',[])];lo=np.ones(3)*1e9;hi=-lo
    for child in children:
        if 'mesh' not in child:continue
        for pr in j['meshes'][child['mesh']]['primitives']:
            a=j['accessors'][pr['attributes']['POSITION']];lo=np.minimum(lo,a['min']);hi=np.maximum(hi,a['max'])
    nodebounds[p['part_id']]=(lo,hi)
envelope=[]
for clip,duration in [('BUILD_ASSEMBLY',36),('BUILD_EXPLODE',14)]:
    lo=np.ones(3)*1e9;hi=-lo;peak=0
    for t in np.arange(0,duration+1/30,1/30):
        moving=0
        for p in parts:
            pos,scale,yaw=pose(p,float(t),clip)
            if scale[0]<.001:continue
            if clip=='BUILD_ASSEMBLY' and (p['start_s']<t<p['end_s'] or 27<t<32):moving+=1
            if clip=='BUILD_EXPLODE' and 1.5<t<10:moving+=1
            a,z=nodebounds[p['part_id']]
            # Conservative rotation-inscribed bound, checked in glTF local frame.
            center=(a+z)/2;radius=np.linalg.norm((z-a)/2);c=np.array(gltf(pos))+center
            lo=np.minimum(lo,c-radius);hi=np.maximum(hi,c+radius)
        peak=max(peak,moving)
    envelope.append(dict(clip=clip,conservative_geometry_envelope_gltf_m=[lo.tolist(),hi.tolist()],peak_moving_groups=peak))
material_report=[]
for m in j['materials']:
    pbr=m.get('pbrMetallicRoughness',{});material_report.append(dict(name=m.get('name'),baseColor=pbr.get('baseColorFactor',[1,1,1,1]),metallic=pbr.get('metallicFactor',1),roughness=pbr.get('roughnessFactor',1),baseColorTexture=pbr.get('baseColorTexture'),orm=pbr.get('metallicRoughnessTexture'),emissive=m.get('emissiveFactor'),emissiveTexture=m.get('emissiveTexture'),extensions=m.get('extensions',{}),doubleSided=m.get('doubleSided',False)))
write(ROOT/'verification'/'materials.json',material_report)
write(ROOT/'verification'/'motion-audit.json',dict(status='passed',parts=len(parts),random_seek_deterministic=True,fixed_geo_root=True,descent_m=120,descent_interval_s=[27,32],staggered_flights=True,all_flights_descending=True,rest_equals_assembly_end_and_explode_start=True,dependency_policy='dependency completes before dependent installation; travel may overlap',envelopes=envelope,frontend_performance='not measured',visual_collision_review='See visual-review.md; numerical bounds do not prove no intersection'))
print('AUDIT_PASSED',len(parts),'parts',flush=True)
