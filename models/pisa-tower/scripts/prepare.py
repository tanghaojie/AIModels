"""Project OSM into north/west metres; preserve courtyard holes, source IDs and heights.
Original tileable images are not photographs or baked lighting. Python 3.12+.
"""
from pathlib import Path
import json, math, hashlib, gzip
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from pyproj import CRS,Transformer
from shapely.geometry import Polygon,Point,LineString
from shapely.geometry.polygon import orient
from shapely.ops import polygonize,unary_union,split
import mapbox_earcut
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
OUT=ROOT.parents[1]/'model-assets'/'geo-context'/'pisa-1000-v1'

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

def polygons(g):
    if g.is_empty:return
    if g.geom_type=='Polygon' and g.area>1e-4:yield g
    elif hasattr(g,'geoms'):
        for a in g.geoms:yield from polygons(a)

def polydata(p):
    p=orient(p,sign=1)
    rings=[list(p.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in p.interiors]
    pts=np.array([v for r in rings for v in r],dtype=np.float64)
    tri=mapbox_earcut.triangulate_float64(pts,np.cumsum([len(r) for r in rings],dtype=np.uint32)).reshape(-1,3)
    return dict(points=pts.tolist(),rings=[len(r) for r in rings],triangles=tri.tolist())

def textures():
    folder=ROOT/'textures';folder.mkdir(exist_ok=True);rng=np.random.default_rng(1173);n=1024
    yy,xx=np.mgrid[0:n,0:n]
    # 4 by 4 metres: lightly coursed San Giuliano marble, offset slab joints.
    grain=rng.normal(0,1.8,(n,n));vein=np.exp(-((np.sin(xx*.018+yy*.011+2*np.sin(yy*.005)))/.085)**2)*4
    row=yy//128;col=(xx+(row%2)*128)//256
    tiles=rng.uniform(-5,5,(8,5));tone=tiles[row,np.minimum(col,4)]
    a=np.array([222,216,198])[None,None,:]+(grain-vein+tone)[:,:,None]
    joint=(yy%128<2)|((xx+(row%2)*128)%256<2)
    a[joint]-=25;Image.fromarray(np.uint8(np.clip(a,0,255))).save(folder/'marble-base.png')
    rough=np.full((n,n,3),(255,177,0),dtype=np.uint8);rough[:,:,1]=np.uint8(np.clip(177+grain*2+tone,0,255));rough[joint,1]=212
    Image.fromarray(rough).save(folder/'marble-orm.png')
    # OpenGL +Y tangent normal from subtle joints / veins; no lighting baked in.
    h=Image.fromarray(np.uint8(np.clip(130+grain*.35-vein-joint*13,0,255))).filter(ImageFilter.GaussianBlur(.8))
    dy,dx=np.gradient(np.asarray(h,dtype=float)/255);v=np.dstack((-dx*3,-dy*3,np.ones((n,n))));v/=np.linalg.norm(v,axis=2)[:,:,None]
    Image.fromarray(np.uint8(np.clip((v*.5+.5)*255,0,255))).save(folder/'marble-normal.png')
    for name,c in [('paving',(169,163,148)),('grass',(83,105,53)),('asphalt',(74,73,69)),('terracotta',(152,77,48)),('water',(60,90,91))]:
        noise=rng.normal(0,3,(n,n));a=np.array(c)[None,None,:]+noise[:,:,None]
        if name=='paving':a[(yy%128<2)|(xx%128<2)]-=18
        if name=='terracotta':a[(yy%28<3)|(xx%64<3)]-=22;a+=np.sin(xx*.12)[:,:,None]*7
        if name=='grass':
            small=Image.fromarray(np.uint8(rng.uniform(115,140,(16,16)))).resize((n,n),Image.Resampling.BICUBIC)
            a+=(np.asarray(small,dtype=float)-128)[:,:,None]*.4
        Image.fromarray(np.uint8(np.clip(a,0,255))).save(folder/(name+'-base.png'))
    # Four restrained Tuscan plaster elevations; 16 m wide by 12 m high repeats.
    for name,c in [('ivory',(208,190,153)),('ochre',(186,149,100)),('rose',(188,146,119)),('cream',(221,210,180))]:
        a=np.array(c)[None,None,:]+rng.normal(0,1.8,(n,n,1));im=Image.fromarray(np.uint8(np.clip(a,0,255)))
        d=ImageDraw.Draw(im);em=Image.new('RGB',(n,n));e=ImageDraw.Draw(em)
        for r in range(4):
            y=r*256+64
            d.line((0,y+145,n,y+145),fill=tuple(v-24 for v in c),width=5)
            for j in range(8):
                x=j*128+41
                d.rectangle((x-4,y-4,x+48,y+106),fill=(186,177,149));d.rectangle((x,y,x+44,y+101),fill=(37,46,41))
                d.rectangle((x+4,y+5,x+40,y+95),fill=(70,78,68));d.line((x+22,y+5,x+22,y+96),fill=(42,49,42),width=3)
                if rng.random()<.28:e.rectangle((x+5,y+5,x+40,y+94),fill=(185,129,62) if rng.random()<.8 else (104,139,160))
                for s in [-1,1]:
                    bx=x-21 if s<0 else x+47;d.rectangle((bx,y,bx+17,y+100),fill=(57,70,53))
                    for v in range(y+8,y+100,7):d.line((bx,v,bx+17,v),fill=(43,57,41),width=2)
        im.save(folder/(name+'-facade.png'));em.save(folder/(name+'-emissive.png'))

def main():
    textures();doc=json.loads((ROOT/'references/osm-context.json').read_text(encoding='utf-8'))
    to=Transformer.from_crs('EPSG:4326',CRS.from_proj4(f'+proj=aeqd +lat_0={CFG["latitude"]} +lon_0={CFG["longitude"]} +datum=WGS84 +units=m'),always_xy=True)
    def xy(a):e,n=to.transform(a['lon'],a['lat']);return (n,-e)
    circle=Point(0,0).buffer(CFG['radius_m'],quad_segs=128)
    relations=[f for f in doc['elements'] if f['type']=='relation'];members={m['ref'] for f in relations for m in f.get('members',[]) if m['type']=='way'}
    def geom(f):
        if f['type']=='way':return Polygon([xy(p) for p in f['geometry']]).buffer(0)
        outs=[];ins=[]
        for m in f.get('members',[]):
            if m.get('geometry'):
                line=LineString([xy(p) for p in m['geometry']]);(ins if m.get('role')=='inner' else outs).append(line)
        p=unary_union(list(polygonize(unary_union(outs))))
        if ins:p=p.difference(unary_union(list(polygonize(unary_union(ins)))))
        return p.buffer(0)
    buildings=[];roads=[];greens=[];water=[];walls=[];trees=[];landmarks=[];stats=Counter()
    for f in sorted(doc['elements'],key=lambda a:(a['type'],a['id'])):
        t=f.get('tags',{});g=f.get('geometry',[])
        if f['type']=='node':
            if t.get('natural')=='tree':
                p=xy(f)
                if Point(p).within(circle):trees.append(p)
            continue
        if t.get('building') and not(f['type']=='way' and f['id'] in members):
            try:p=geom(f)
            except Exception:continue
            if p.is_empty or p.distance(Point(0,0))>1000:continue
            if f['id'] in [22945162,22945163,154289,12982355]:
                landmarks.append(dict(osm_id=f['id'],name=t.get('name'),center=list(p.centroid.coords)[0],bounds=list(p.bounds),**polydata(max(polygons(p),key=lambda p:p.area))));continue
            try:h=float(t.get('height','').replace('m',''));method='source_height'
            except ValueError:
                try:h=float(t['building:levels'])*3.2;method='floors_estimate'
                except (KeyError,ValueError):h={'church':19,'chapel':14,'garage':3.5,'shed':3,'house':8,'apartments':13,'school':12,'industrial':8}.get(t['building'],11);method='type_estimate'
            h=max(3,min(40,h))
            for pl in polygons(p.intersection(circle)):
                if pl.area<10:continue
                pl=pl.simplify(.18,preserve_topology=True)
                style=['ivory','ochre','rose','cream'][f['id']%4]
                # Roof slope within real outline; split at ridge so concavities/holes survive.
                rect=list(pl.minimum_rotated_rectangle.exterior.coords);edges=[np.subtract(rect[i+1],rect[i]) for i in range(4)];short=min(edges,key=np.linalg.norm);u=short/np.linalg.norm(short);center=np.array(pl.centroid.coords[0]);half=np.linalg.norm(short)/2
                long=np.array([-u[1],u[0]]);line=LineString([center-long*2000,center+long*2000]);roof=[]
                for q in polygons(split(pl,line)):
                    pd=polydata(q);pd['z']=[h+max(0,1-abs(np.dot(np.array(v)-center,u))/max(half,.5))*min(3,half*.38) for v in pd['points']];roof.append(pd)
                buildings.append(dict(osm_id=f['id'],name=t.get('name',''),height=h,height_method=method,style=style,center=list(pl.centroid.coords)[0],roof=roof,**polydata(pl)));stats[method]+=1
        elif len(g)>1:
            pts=[xy(p) for p in g]
            if 'highway' in t:
                typ=t['highway'];w={'primary':12,'secondary':10,'tertiary':8,'residential':5.5,'service':3.6,'footway':2,'pedestrian':5,'path':1.6,'cycleway':2,'steps':2,'unclassified':5}.get(typ,4)
                try:w=float(t.get('width',w))
                except ValueError:pass
                ar=LineString(pts).buffer(w/2,cap_style='flat',join_style='round').intersection(circle)
                for p in polygons(ar):roads.append(dict(osm_id=f['id'],type=typ,style='paving' if typ in ['footway','path','pedestrian','steps'] else 'asphalt',**polydata(p)))
            elif t.get('barrier')=='city_wall':walls.append(dict(osm_id=f['id'],points=pts))
            elif len(pts)>3:
                p=Polygon(pts).buffer(0).intersection(circle)
                if t.get('natural')=='water':dest=water
                elif t.get('landuse') in ['grass','meadow','forest','recreation_ground'] or t.get('leisure') in ['park','garden']:dest=greens
                else:continue
                for q in polygons(p):
                    if q.area>10:dest.append(dict(osm_id=f['id'],**polydata(q)))
    # The subject is never duplicated in context. Landmark replacements are separate.
    source_road_count=len(roads);source_green_count=len(greens)
    def reconstructed(p):
        pts=p['points'];off=0;rings=[]
        for count in p['rings']:rings.append(pts[off:off+count]);off+=count
        return Polygon(rings[0],rings[1:])
    def merged(items):
        if not items:return []
        return [polydata(p) for p in polygons(unary_union([reconstructed(p) for p in items]))]
    # Union coplanar overlaps to prevent z-fighting at road junctions and nested lawns.
    roads=[dict(style=style,**p) for style in ['asphalt','paving'] for p in merged([p for p in roads if p['style']==style])]
    greens=merged(greens);water=merged(water)
    result=dict(version=1,anchor=dict(longitude=CFG['longitude'],latitude=CFG['latitude']),radius_m=1000,buildings=buildings,roads=roads,greens=greens,water=water,walls=walls,trees=trees,landmarks=landmarks)
    write(ROOT/'recipe.json',result)
    metadata=dict(id='pisa-1000-v1',source='OpenStreetMap via Overpass',timestamp=doc.get('osm3s',{}).get('timestamp_osm_base'),radius_m=1000,building_count=len(buildings),road_sections=source_road_count,rendered_road_polygons=len(roads),green_polygons=source_green_count,rendered_green_polygons=len(greens),source_tree_positions=len(trees),height_methods=dict(stats),excluded_subject='relation/12982355',landmark_replacements=[x['osm_id'] for x in landmarks],axis='Blender +X north, +Y west, +Z up',terrain='Ellipsoid demonstration, height=0; no measured terrain',notice='Real geographic building/street outlines; missing heights, roof profiles, facade windows and planting forms are visualization estimates, not photogrammetry.',attribution=[dict(text='© OpenStreetMap contributors · ODbL-1.0',url='https://www.openstreetmap.org/copyright')])
    write(OUT/'metadata.json',metadata)
    (OUT/'sources').mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/'sources/osm-context.json.gz','wb') as f:f.write((ROOT/'references/osm-context.json').read_bytes())
    print(json.dumps(metadata,ensure_ascii=False,indent=2));print('LANDMARKS',[(p['name'],p['center'],p['bounds']) for p in landmarks])

if __name__=='__main__':main()
