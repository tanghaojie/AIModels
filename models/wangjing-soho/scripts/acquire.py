"""Archive attributed reference originals and raw OSM geometry. Python 3.12+."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request, urllib.parse, json, hashlib, shutil, time

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references'
REF.mkdir(parents=True, exist_ok=True)
AGENT = 'AIModels architectural reference research/1.0'
def get(url, path, data=None):
    req=urllib.request.Request(url, data=data, headers={'User-Agent':AGENT})
    with urllib.request.urlopen(req, timeout=100) as r:
        raw=r.read()
        path.write_bytes(raw)
    return raw

def reference(item):
    name,url,credit,use=item
    path=REF/name
    try:
        raw=path.read_bytes() if path.exists() else get(url,path)
        from PIL import Image
        with Image.open(path) as im: size=list(im.size)
        return dict(file=name,url=url,credit=credit,use=use,pixels=size,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),status='saved',license='Copyright retained by author; local research/acceptance only; excluded from Git redistribution')
    except Exception as e:
        return dict(file=name,url=url,status='failed',error=str(e))

def main():
    refs=[]
    for file,use in [('sectiona-a','BB section'),('sectionb-b','AA section')]:
        refs.append((file+'.jpg','https://www.theplan.it/images/stories/gallery43264/'+file+'.jpg','Zaha Hadid Architects',use))
    for file,use in [('1_siteplan','north/site composition'),('2_floorplan','ground floor/entries'),('3_floorplan2','typical floor')]:
        refs.append((file+'.jpg','https://www.theplan.it/images/stories/gallery43265/'+file+'.jpg','Zaha Hadid Architects',use))
    for file in ['eastelevation','southelevation','westelevation']:
        refs.append((file+'.jpg','https://www.theplan.it/images/stories/gallery43266/'+file+'.jpg','Zaha Hadid Architects',file))
    for file in ['02-jl','03-jl','04-vsb','05-vsb','06-vsb','07-vsb','08-vsb','09-vsb']:
        refs.append((file+'.jpg','https://www.theplan.it/images/stories/gallery43251/'+file+'.jpg','Jerry Yin' if 'jl' in file else 'Virgile Simon Bertrand / Alphaville.hk','built photography'))
    refs += [('zha-aerial.webp','https://media-prod.zha.com/zhweb-prod-media/media/jpymqbqp/01618_cp_jy_sep14_n211992.jpg?fm=webp&w=2560','Jerry Yin / SOHO China / ZHA','built aerial composition'),('zha-ground.webp','https://media-prod.zha.com/zhweb-prod-media/media/pa0cblfi/01618_cp_xl_oct23_n303765.jpg?fm=webp&w=2560','Xue Liang / ZHA','2023 ground/skin'),('zha-detail.webp','https://media-prod.zha.com/zhweb-prod-media/media/morpo3gl/01618_cp_vsb_sep14_n100491.jpg?fm=webp&w=2560','Virgile Simon Bertrand / ZHA','facade detail')]
    with ThreadPoolExecutor(max_workers=5) as pool: result=list(pool.map(reference,refs))
    (REF/'download-manifest.json').write_text(json.dumps(dict(collected='2026-10-18',page='https://www.theplan.it/eng/architecture/wangjing-soho-zaha-hadid',official='https://www.zha.com/projects/architecture/wangjing-soho',files=result),ensure_ascii=False,indent=2),encoding='utf-8')
    print('REFERENCES',[(x['file'],x['status'],x.get('pixels')) for x in result],flush=True)
    temp=Path(__import__('tempfile').gettempdir())/'wangjing-theplan.txt'
    if temp.exists(): shutil.copyfile(temp,REF/'theplan-jina.txt')
    osm=REF/'osm-context.json'
    if not osm.exists():
        q='[out:json][timeout:120];(way[building](around:1550,39.99547,116.47506);way[highway](around:1550,39.99547,116.47506);way[leisure=park](around:1550,39.99547,116.47506);way[landuse=grass](around:1550,39.99547,116.47506);way[natural=water](around:1550,39.99547,116.47506););out tags geom;'
        for host in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
            try:
                raw=get(host,osm,urllib.parse.urlencode({'data':q}).encode())
                doc=json.loads(raw); print('OSM',len(doc['elements']),flush=True); break
            except Exception as e: print(host,str(e),flush=True)
    if osm.exists():
        doc=json.loads(osm.read_text(encoding='utf-8'))
        print('LANDMARKS',[(x['id'],x.get('tags')) for x in doc['elements'] if 'SOHO' in x.get('tags',{}).get('name','')],flush=True)

if __name__=='__main__': main()
