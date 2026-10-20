"""Original PBR maps and source-bounded, AEQD-clipped Downtown Dubai recipe."""
from common import *
import math,gzip,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from shapely.geometry import Polygon,LineString,Point,shape
from shapely.ops import unary_union,linemerge
from shapely.geometry.polygon import orient
from shapely import affinity
from pyproj import CRS,Transformer
import mapbox_earcut

def polys(g):
    if g.geom_type=='Polygon':yield g
    elif hasattr(g,'geoms'):
        for x in g.geoms:yield from polys(x)
def polydata(poly):
    p=orient(poly,sign=1)
    rings=[list(p.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in p.interiors]
    pts=np.array([p for ring in rings for p in ring],dtype=np.float64)
    tri=mapbox_earcut.triangulate_float64(pts,np.cumsum([len(r) for r in rings],dtype=np.uint32)).reshape(-1,3)
    return dict(points=pts.tolist(),rings=[len(r) for r in rings],triangles=tri.tolist())
def textures():
    out=ROOT/'textures';out.mkdir(exist_ok=True)
    rng=np.random.default_rng(CFG['seed']);size=1024
    base=Image.new('RGB',(size,size));em=Image.new('RGB',(size,size));rough=Image.new('RGB',(size,size),(255,65,0))
    b,e,r=map(ImageDraw.Draw,[base,em,rough])
    # 16 x 8 independent glazing bays. Fixed light occupancy, curtains and blind
    # strips; lighting is never baked into the daytime base map.
    for row in range(8):
        group_on=rng.random()<.68
        for col in range(16):
            x,y=col*64,row*128;t=rng.uniform(.93,1.045)
            b.rectangle((x,y,x+63,y+127),fill=(57,70,78))
            b.rectangle((x+2,y+2,x+61,y+125),fill=tuple(int(c*t) for c in (110,137,151)))
            b.rectangle((x+3,y+3,x+60,y+25),fill=tuple(int(c*t) for c in (94,115,129)))
            if rng.random()<.22:b.rectangle((x+3,y+26,x+60,y+38),fill=(122,135,142))
            r.rectangle((x+2,y+2,x+61,y+125),fill=(255,int(rng.uniform(49,70)),0))
            if group_on and rng.random()<.53:
                tint=(255,194,120) if rng.random()<.8 else (175,210,242);energy=rng.uniform(.24,.82)
                e.rectangle((x+5,y+29,x+58,y+117),fill=tuple(int(c*energy) for c in tint))
                if rng.random()<.35:e.rectangle((x+5,y+29,x+29,y+117),fill=(0,0,0))
                for yy in [44,67,91]:e.line((x+5,y+yy,x+58,y+yy),fill=tuple(int(c*energy*.65) for c in tint),width=2)
    for name,im in [('glazing-base',base),('glazing-emissive',em),('glazing-orm',rough)]:im.save(out/(name+'.png'))
    for name,c,pitch,roughness in [('travertine',(178,168,146),128,190),('concrete',(139,143,143),256,207),('asphalt',(48,52,56),0,236),('sand',(173,151,119),0,245),('grass',(78,100,55),0,230)]:
        a=np.zeros((size,size,3),dtype=np.int16);a[:]=c;a+=rng.integers(-6,7,(size,size,1),dtype=np.int16)
        if pitch:
            a[::pitch]-=18;a[:,::pitch]-=18
            if name=='travertine':a+=np.sin(np.arange(size)[:,None,None]/11)*np.array([3,3,2],dtype=np.int16) if False else 0
        Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(out/(name+'-base.png'))
    sys.path.insert(0,str(REPO/'tools'/'geo-context'))
    from materials import create_materials
    create_materials(out/'district')
    write(out/'library.json',dict(author='AIModels original deterministic procedural textures',seed=CFG['seed'],resolution=[1024,1024],no_baked_lighting=True,glazing_cell_m=[1.5,3.8],uv='TEXCOORD_0',color_space={'baseColor':'sRGB','emissive':'sRGB','ORM':'linear'},license='MIT'))

def tower_geometry(angle=24):
    # Scalloped wing sides traced proportionally from SOM typical floor drawing.
    # Dimensions and setback elevations are photogrammetric approximations, not
    # a reproduction of an unavailable as-built dimensional drawing.
    setbacks=[58,84,111,138,166,195,224,254,284,314,344,374,404,433,461,489,516,542,565,586,606,624,641,658,674,690,706]
    levels=sorted(set([0.,10.,625.6]+[round(10+i*3.8,3) for i in range(162) if 10+i*3.8<625.6]+[float(z) for z in setbacks if z<625.6]))
    def contour(z):
        lengths=[62.,62.,62.]
        for i,h in enumerate(setbacks):
            if z>=h:lengths[i%3]-=5.8
        shrink=1-.15*min(1,z/625)
        r=13.5*shrink
        core=Polygon([(r*math.cos(a),r*math.sin(a)) for a in np.linspace(0,math.tau,7)[:-1]])
        wings=[]
        for k,L in enumerate(lengths):
            L=max(8,L);side=[];stop=max(9,L-11)
            for u in np.linspace(7,stop,max(3,int((stop-7)*1.45))):
                w=(14.5-.046*u)*shrink+(1.25*shrink)*math.sin((u-7)/9*math.pi)**2
                side.append((float(u),w))
            w=side[-1][1]
            cap=[(stop+(L-stop)*math.sin(a),w*math.cos(a)) for a in np.linspace(0,math.pi,25)[1:]]
            wing=Polygon(side+cap+[(u,-v) for u,v in side[::-1]][1:]).buffer(0)
            wing=affinity.rotate(wing,angle+k*120,origin=(0,0))
            wings.append(wing)
        p=unary_union([core,*wings]).buffer(0).simplify(.035)
        assert p.geom_type=='Polygon'
        return p
    floors=[]
    for i in range(len(levels)-1):
        z0,z1=levels[i:i+2];p=contour(z0+.01)
        floors.append(dict(index=i,z0=z0,z1=z1,mechanical=any(a<=z0<b for a,b in [(160,171),(282,294),(410,422),(530,542)]),**polydata(p)))
    return dict(angle_degrees=angle,floors=floors,setbacks_m=setbacks,source='SOM typical floor, elevator section and program axonometric; elevations and plan dimensions approximate',base_width_m=list(contour(0).bounds),cladding_top_m=625.6,spire_top_m=828)

def main():
    raw=ROOT/'references'/'osm-context.json';doc=json.loads(raw.read_text(encoding='utf-8'))
    assert len(doc['elements'])>100,'No usable OSM district data'
    lon,lat=CFG['anchor'];to=Transformer.from_crs('EPSG:4326',CRS.from_proj4(f'+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m'),always_xy=True)
    def xy(p):
        east,north=to.transform(p['lon'],p['lat']);return (north,-east)
    circle=Point(0,0).buffer(CFG['context_radius_m'],quad_segs=96)
    tower_source=next(f for f in doc['elements'] if f.get('tags',{}).get('name:en')=='Burj Khalifa' and 'building' in f.get('tags',{}))
    tower_outline=Polygon([xy(p) for p in tower_source['geometry']]).buffer(0)
    elements=list(doc['elements'])
    relfile=ROOT/'references'/'osm-relations.json'
    fullfile=ROOT/'references'/'osm-mall-full.json'
    if fullfile.exists():
        try:
            full=json.loads(fullfile.read_text(encoding='utf-8'));byid={(f['type'],f['id']):f for f in full['elements']}
            rels=[]
            for f in full['elements']:
                if f['type']!='relation':continue
                members=[]
                for m in f['members']:
                    if m['type']!='way':continue
                    way=byid[('way',m['ref'])];geo=[{k:byid[('node',n)][k] for k in ['lat','lon']} for n in way['nodes']]
                    members.append(dict(type='way',ref=m['ref'],role=m.get('role',''),geometry=geo))
                rels.append(dict(id=f['id'],tags=f.get('tags',{}),members=members))
            if rels:write(relfile,dict(elements=rels,source='OSM official relation full JSON; relation 18195959'))
        except (ValueError,KeyError):pass
    if relfile.exists():
        from shapely.ops import polygonize
        for f in json.loads(relfile.read_text(encoding='utf-8'))['elements']:
            t=f.get('tags',{});outer=[];inner=[]
            for member in f.get('members',[]):
                pts=[xy(p) for p in member.get('geometry',[]) if 'lat' in p]
                if len(pts)>2:(inner if member.get('role')=='inner' else outer).append(LineString(pts))
            if not outer:continue
            area=unary_union(list(polygonize(unary_union(outer))))
            if inner:area=area.difference(unary_union(list(polygonize(unary_union(inner)))))
            for i,p in enumerate(polys(area)):
                elements.append(dict(id=f"r{f['id']}-{i}",type='way',tags=t,projected_polygon=p))
    buildings=[];roads=[];land=[];stats=collections.Counter();excluded=[];parts=[]
    for f in elements:
        t=f.get('tags',{});geo=f.get('geometry',[])
        if f.get('type')=='relation':
            if t.get('natural')=='water':
                outer=[];inner=[]
                for m in f.get('members',[]):
                    pts=[xy(p) for p in m.get('geometry',[]) if 'lat' in p]
                    if len(pts)>2:(inner if m.get('role')=='inner' else outer).append(LineString(pts))
                from shapely.ops import polygonize
                water=unary_union(list(polygonize(unary_union(outer)))) if outer else Polygon()
                holes=unary_union(list(polygonize(unary_union(inner)))) if inner else Polygon()
                for p in polys(water.difference(holes).intersection(circle)):
                    if p.area>10:land.append(dict(id=f['id'],kind='water',name=t.get('name',''),**polydata(p.simplify(.3))))
            continue
        if len(geo)<2 and 'projected_polygon' not in f:continue
        pts=[xy(p) for p in geo]
        if 'building' in t or 'building:part' in t:
            if len(pts)<4 and 'projected_polygon' not in f:continue
            p=f['projected_polygon'] if 'projected_polygon' in f else Polygon(pts).buffer(0)
            if p.is_empty:continue
            if f['id']==tower_source['id'] or (p.area<24000 and tower_outline.buffer(1).intersection(p).area/max(1,p.area)>.55):
                excluded.append(dict(id=f['id'],tags=t,**polydata(p)));continue
            method='height'
            try:h=float(t.get('height','').replace('m','').strip())
            except ValueError:
                try:h=float(t['building:levels'])*3.4;method='levels_estimate'
                except (KeyError,ValueError):h={'apartments':42,'residential':30,'hotel':65,'office':55,'commercial':22,'retail':16,'house':8,'garage':6,'parking':8}.get(t.get('building'),15);method='type_estimate'
            try:minh=float(t.get('min_height',0))
            except ValueError:minh=0
            h=max(minh+1,min(450,h));style='office' if t.get('building') in ['office','commercial','hotel'] or h>100 else 'residential' if t.get('building') in ['apartments','residential'] else 'concrete'
            for pl in polys(p.intersection(circle)):
                if pl.area<12:continue
                buildings.append(dict(id=f['id'],name=t.get('name:en',t.get('name','')),height=h,min_height=minh,height_method=method,style=style,is_part='building:part' in t,tile=[math.floor(pl.centroid.x/500),math.floor(pl.centroid.y/500)],**polydata(pl.simplify(.2,preserve_topology=True))))
        elif 'highway' in t:
            typ=t['highway'];w={'motorway':14,'motorway_link':7,'trunk':13,'trunk_link':7,'primary':12,'secondary':11,'tertiary':10,'residential':7,'service':4.5,'unclassified':6,'footway':2.5,'path':2,'pedestrian':7,'steps':2,'cycleway':2.5}.get(typ,5)
            try:w=float(t.get('width',w))
            except ValueError:pass
            line=LineString(pts)
            for pl in polys(line.buffer(w/2,cap_style='flat',join_style='round').intersection(circle)):
                if pl.area>1:roads.append(dict(id=f['id'],kind=typ,width=w,bridge=t.get('bridge')=='yes',centerline=pts,**polydata(pl.simplify(.25,preserve_topology=True))))
        elif t.get('natural')=='water' or t.get('leisure')=='park' or t.get('landuse')=='grass':
            if pts[0]!=pts[-1] or len(pts)<4:continue
            for pl in polys(Polygon(pts).buffer(0).intersection(circle)):
                if pl.area>10:land.append(dict(id=f['id'],kind='water' if t.get('natural')=='water' else 'grass',name=t.get('name',''),**polydata(pl.simplify(.3,preserve_topology=True))))
    # Prefer explicit building parts over a duplicated parent shell. Keep its
    # uncovered region, preserving source coverage without z-fighting.
    part_geoms=[Polygon(b['points'][:b['rings'][0]]) for b in buildings if b['is_part']]
    part_union=unary_union(part_geoms) if part_geoms else Polygon()
    clean=[]
    for b in buildings:
        p=Polygon(b['points'][:b['rings'][0]],[])
        if not b['is_part'] and part_union.intersection(p).area/max(1,p.area)>.75:continue
        clean.append(b);stats[b['height_method']]+=1
    overrides=json.loads((ROOT/'context-overrides.json').read_text(encoding='utf-8'))['features']
    # Only add this explicitly documented reference reconstruction when an actual
    # named OSM mall main shell was not retrieved. Existing OSM detail remains.
    for feature in overrides:
        if any(b['name'] in ['The Dubai Mall','Dubai Mall'] for b in clean):continue
        p=Polygon(feature['points']).buffer(0).intersection(circle)
        for pl in polys(p):
            clean.append(dict(id=feature['id'],name=feature['name'],height=feature['height_m'],min_height=0,height_method=feature['height_method'],style=feature['style'],is_part=False,source='SOM aerial manual trace',tile=[0,-1],**polydata(pl)))
            stats[feature['height_method']]+=1
    def source_poly(data):
        rings=[];offset=0
        for count in data['rings']:rings.append(data['points'][offset:offset+count]);offset+=count
        return Polygon(rings[0],rings[1:])
    water_union=unary_union([source_poly(p) for p in land if p['kind']=='water']).buffer(0)
    ground=[polydata(p) for p in polys(circle.difference(water_union))]
    site_ground=[polydata(p) for p in polys(Point(0,0).buffer(148,quad_segs=48).difference(water_union))]
    angle=24
    # Calibrate one arm's north heading from the farthest OSM tower-boundary point.
    if excluded:
        tower=next(p for p in excluded if p['id']==tower_source['id'])
        far=max(tower['points'],key=lambda p:math.hypot(*p))
        # The perimeter includes the arrival pavilions. Use the upper shaft's
        # outermost low-tier lobes to orient the three wings instead.
        low_parts=[p for p in excluded if p['tags'].get('building:part') and p['tags'].get('height','').replace(' m','').replace('m','') in ['105','200','315','360']]
        if low_parts:
            far=max([v for p in low_parts for v in p['points']],key=lambda p:math.hypot(*p))
        angle=math.degrees(math.atan2(far[1],far[0]))%120
    write_compact(ROOT/'recipe.json',dict(version=1,source_date=doc.get('osm3s',{}).get('timestamp_osm_base'),anchor=CFG['anchor'],radius_m=2000,ground=ground,site_ground=site_ground,tower=tower_geometry(angle),buildings=clean,roads=roads,land=land,excluded_tower=excluded,stats=dict(stats)))
    CONTEXT.mkdir(parents=True,exist_ok=True);(CONTEXT/'sources').mkdir(exist_ok=True)
    with gzip.GzipFile(filename=str(CONTEXT/'sources'/'osm-context.json.gz'),mode='wb',mtime=0) as stream:stream.write(raw.read_bytes())
    if relfile.exists():
        with gzip.GzipFile(filename=str(CONTEXT/'sources'/'osm-relations.json.gz'),mode='wb',mtime=0) as stream:stream.write(relfile.read_bytes())
    write(CONTEXT/'metadata.json',dict(version=1,date=CFG['date'],source='OpenStreetMap Overpass API snapshot plus one explicitly approximate mall aerial reconstruction',source_timestamp=doc.get('osm3s',{}).get('timestamp_osm_base'),anchor=CFG['anchor'],radius_m=2000,area_km2=math.pi*4,source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),buildings=len(clean),road_polygons=len(roads),land_polygons=len(land),heights=dict(stats),reference_overrides=overrides,excluded_ids=[x['id'] for x in excluded],license='ODbL-1.0 for OSM data; original approximate mall reconstruction by AIModels',limitations=['OSM footprints/roads/water geometry; one mall volume is explicitly aerial-traced approximate','Missing heights estimated using floors or building type; not surveyed','Flat ellipsoid demonstration height 0; no terrain elevation data','Street furniture and rooftop equipment illustrative','Historical mall reference does not reproduce current expansions exactly','No invented urban grid']))
    textures();print('PREPARED',dict(buildings=len(clean),roads=len(roads),land=len(land),excluded=[x['id'] for x in excluded],heights=dict(stats)),flush=True)
if __name__=='__main__':main()
