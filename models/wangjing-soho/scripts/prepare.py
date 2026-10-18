"""Prepare original PBR textures and a clipped, attributed OSM district recipe."""
from pathlib import Path
import json, math, random, sys, hashlib, gzip
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, LineString, Point, mapping, shape
from shapely.ops import transform,unary_union
from shapely.geometry.polygon import orient
import mapbox_earcut

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT.parents[1]/'model-assets'/'geo-context'/'wangjing-soho-1500-v1'
LON,LAT=116.47506,39.99547
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def polydata(poly,z=0):
    poly=orient(poly,sign=1)
    rings=[list(poly.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in poly.interiors]
    pts=np.array([p for ring in rings for p in ring],dtype=np.float64)
    ends=np.cumsum([len(r) for r in rings],dtype=np.uint32)
    tri=mapbox_earcut.triangulate_float64(pts,ends).reshape(-1,3).tolist()
    return dict(points=pts.tolist(),rings=[len(r) for r in rings],triangles=tri)
def eachpoly(g):
    if g.geom_type=='Polygon': yield g
    elif hasattr(g,'geoms'):
        for p in g.geoms: yield from eachpoly(p)
def textures():
    out=ROOT/'textures'; out.mkdir(exist_ok=True)
    rng=np.random.default_rng(7331)
    size=1024
    base=Image.new('RGB',(size,size)); em=Image.new('RGB',(size,size)); orm=Image.new('RGB',(size,size),(255,65,0))
    b,e,o=ImageDraw.Draw(base),ImageDraw.Draw(em),ImageDraw.Draw(orm)
    for row in range(8):
        for col in range(16):
            x,y=col*64,row*128
            tint=rng.uniform(.85,1.12)
            b.rectangle((x,y,x+63,y+127),fill=tuple(int(c*tint) for c in (51,78,91)))
            b.rectangle((x+4,y+5,x+59,y+120),fill=tuple(int(c*tint) for c in (69,96,108)))
            b.rectangle((x+5,y+7,x+58,y+23),fill=(58,81,90))
            if rng.random()<.43:
                c=(255,196,126) if rng.random()<.77 else (174,213,239)
                bright=rng.uniform(.3,.8)
                e.rectangle((x+7,y+11,x+56,y+117),fill=tuple(int(v*bright) for v in c))
                for yy in [34,65,94]: e.line((x+7,y+yy,x+56,y+yy),fill=tuple(int(v*bright*.65) for v in c),width=2)
            o.rectangle((x+4,y+5,x+59,y+120),fill=(255,int(rng.uniform(44,69)),0))
    for n,im in [('curtain-base',base),('curtain-emissive',em),('curtain-orm',orm)]: im.save(out/(n+'.png'))
    for name,c,grid,pitch in [('limestone',(165,160,148),True,128),('asphalt',(48,53,58),False,128),('grass',(71,94,59),False,128),('concrete',(151,151,145),True,256)]:
        a=np.zeros((1024,1024,3),dtype=np.int16); a[:]=c; a+=rng.integers(-5,6,(1024,1024,1),dtype=np.int16)
        if grid:
            a[::pitch,:,:]-=24; a[:,::pitch,:]-=24
        Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(out/(name+'-base.png'))
    sys.path.insert(0,str(ROOT.parents[1]/'tools'/'geo-context'))
    from materials import create_materials
    create_materials(out/'district')
def main():
    raw=ROOT/'references'/'osm-context.json'; doc=json.loads(raw.read_text(encoding='utf-8'))
    to=Transformer.from_crs('EPSG:4326',CRS.from_proj4(f'+proj=aeqd +lat_0={LAT} +lon_0={LON} +datum=WGS84 +units=m'),always_xy=True)
    def xy(p):
        e,n=to.transform(p['lon'],p['lat']); return [n,-e]
    circle=Point(0,0).buffer(1500,quad_segs=96)
    buildings=[]; roads=[]; greens=[]; landmarks=[]; stats={'source_height':0,'floors_estimate':0,'type_estimate':0};coverage=[]
    towerids={327007845:('T1',118,25,93),327007846:('T2',127,26,97),327007847:('T3',200,45,179),461446738:('P2',15,3,13),691614969:('P1',15,3,13)}
    for f in doc['elements']:
        tags=f.get('tags',{}); geo=f.get('geometry',[])
        if len(geo)<2: continue
        pts=[xy(p) for p in geo]
        if 'building' in tags and len(pts)>3:
            p=Polygon(pts).buffer(0)
            coverage.append(p)
            if f['id'] in towerids:
                ident,h,n,top=towerids[f['id']]; landmarks.append(dict(id=ident,osm_id=f['id'],height=h,floors=n,occupied_top=top,**polydata(p)));continue
            if p.distance(Point(0,0))>1500: continue
            try: h=float(tags.get('height','').replace('m','').strip()); method='source_height'
            except ValueError:
                try: h=float(tags['building:levels'])*3.2; method='floors_estimate'
                except (KeyError,ValueError):
                    h={'apartments':30,'residential':21,'commercial':18,'office':36,'school':15,'industrial':9,'house':7,'garage':4}.get(tags['building'],12);method='type_estimate'
            h=max(3,min(350,h));stats[method]+=1
            style='residential' if tags['building'] in ['apartments','residential','house'] else 'office' if tags['building'] in ['office','commercial'] else 'concrete'
            for pl in eachpoly(p.intersection(circle)):
                if pl.area>15:
                    buildings.append(dict(id=f['id'],name=tags.get('name',''),height=h,height_method=method,style=style,tile=[math.floor(pl.centroid.x/500),math.floor(pl.centroid.y/500)],**polydata(pl.simplify(.3,preserve_topology=True))))
        elif 'highway' in tags:
            typ=tags['highway'];w={'motorway':22,'trunk':20,'primary':18,'secondary':15,'tertiary':12,'residential':7,'service':4.5,'unclassified':6,'footway':2.6,'path':2,'pedestrian':6,'cycleway':2.8,'steps':2}.get(typ,5)
            if 'width' in tags:
                try: w=float(tags['width'].replace('m',''))
                except ValueError: pass
            line=LineString(pts); area=line.buffer(w/2,cap_style='flat',join_style='round').intersection(circle)
            for pl in eachpoly(area):
                if pl.area>1: roads.append(dict(id=f['id'],kind=typ,name=tags.get('name',''),width=w,centerline=pts,**polydata(pl.simplify(.18,preserve_topology=True))))
        elif tags.get('leisure')=='park' or tags.get('landuse')=='grass' or tags.get('natural')=='water':
            if len(pts)<4 or pts[0]!=pts[-1]:continue
            for pl in eachpoly(Polygon(pts).buffer(0).intersection(circle)):
                if pl.area>10:greens.append(dict(id=f['id'],kind='water' if tags.get('natural')=='water' else 'grass',**polydata(pl.simplify(.4,preserve_topology=True))))
    # Fill genuinely unmapped footprints with the pinned Overture release; never duplicate current OSM.
    overture=ROOT/'references'/'overture'/'building.geojson';added=0
    if overture.exists():
        known=unary_union(coverage)
        ov=json.loads(overture.read_text(encoding='utf-8'))
        def project(e,n,z=None):
            x,y=to.transform(e,n);return y,-np.asarray(x)
        for feature in ov['features']:
            p=transform(project,shape(feature['geometry'])).buffer(0)
            if p.is_empty or p.area<15 or p.distance(Point(0,0))>1500:continue
            if known.intersection(p).area/p.area>.12:continue
            prop=feature['properties'];cat=prop.get('class') or prop.get('subtype') or 'default'
            if prop.get('height'):h=float(prop['height']);method='source_height'
            elif prop.get('num_floors'):h=float(prop['num_floors'])*3.2;method='floors_estimate'
            else:h={'apartments':30,'residential':21,'office':36,'commercial':18,'house':7}.get(cat,12);method='type_estimate'
            for pl in eachpoly(p.intersection(circle)):
                if pl.area<15:continue
                buildings.append(dict(id=feature['id'],name='',source='Overture 2026-09-23.1',height=min(350,max(3,h)),height_method=method,style='residential' if cat in ['apartments','residential','house'] else 'office' if cat in ['office','commercial'] else 'concrete',tile=[math.floor(pl.centroid.x/500),math.floor(pl.centroid.y/500)],**polydata(pl.simplify(.3,preserve_topology=True))))
                stats[method]+=1;added+=1
    # The 6 m third pavilion is plan-traced; its footprint is explicitly an approximation.
    p=Polygon([(-137,-36),(-137,36),(-126,42),(-123,25),(-123,-35)])
    landmarks.append(dict(id='P3',height=6,floors=1,occupied_top=6,source='ZHA site plan; plan-traced approximate dimensions/location',**polydata(p)))
    write(ROOT/'recipe.json',dict(version=1,seed=7331,anchor=[LON,LAT],radius_m=1500,landmarks=landmarks,buildings=buildings,roads=roads,greens=greens,stats=stats,overture_added=added))
    ASSET.mkdir(parents=True,exist_ok=True)
    write(ASSET/'metadata.json',dict(version=1,date='2026-10-18',source='OpenStreetMap Overpass API + Overture 2026-09-23.1 nonoverlapping infill',endpoint='https://overpass-api.de/api/interpreter',raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),anchor=[LON,LAT],radius_m=1500,area_km2=math.pi*1.5**2,building_count=len(buildings),overture_infill=added,road_polygons=len(roads),greens=len(greens),heights=stats,license='ODbL-1.0 plus East Asian Buildings CC BY 4.0',excluded_ids=list(towerids),limitations=['Missing heights estimated by levels or type; not measured','Building facades and roof equipment are illustrative; source coverage is incomplete','Ground is a flat ellipsoid demonstration at height 0, not surveyed terrain','No fictional district building footprints have been inserted']))
    (ASSET/'sources').mkdir(exist_ok=True)
    with gzip.GzipFile(filename=str(ASSET/'sources'/'osm-context.json.gz'),mode='wb',mtime=0) as stream: stream.write(raw.read_bytes())
    if overture.exists():
        with gzip.GzipFile(filename=str(ASSET/'sources'/'overture-buildings.geojson.gz'),mode='wb',mtime=0) as stream:stream.write(overture.read_bytes())
    textures()
    print(json.dumps(dict(buildings=len(buildings),roads=len(roads),greens=len(greens),landmarks=[dict(id=x['id'],points=len(x['points'])) for x in landmarks],heights=stats)))
if __name__=='__main__': main()
