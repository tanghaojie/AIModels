"""Download reference originals and attributed OSM source; no credentials required."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request, urllib.parse, json, hashlib, re, html, time,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'references'; ORIG=REF/'originals'; PAGES=REF/'pages'
for p in [REF,ORIG,PAGES]:p.mkdir(parents=True,exist_ok=True)
AGENT='Mozilla/5.0 (AIModels architectural reference archive)'
def get(url,path,data=None):
    if path.exists() and path.stat().st_size>200:return path.read_bytes()
    req=urllib.request.Request(url,data=data,headers={'User-Agent':AGENT})
    with urllib.request.urlopen(req,timeout=150) as r:raw=r.read()
    path.write_bytes(raw);return raw
def save(item):
    name,url,credit,use=item;path=ORIG/name
    try:
        raw=get(url,path); size=None
        if not name.endswith('.pdf'):
            from PIL import Image
            with Image.open(path) as im:size=list(im.size)
        return dict(file='originals/'+name,url=url,credit=credit,use=use,pixels=size,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),status='saved',license='Copyright retained by source; local modeling reference/acceptance only; originals excluded from Git')
    except Exception as e:return dict(file=name,url=url,status='failed',error=str(e))
def main():
    refs=[('ctbuh-engineering.pdf','https://global.ctbuh.org/resources/papers/download/1326-engineering-the-worlds-tallest-burj-bubai.pdf','William F. Baker, D. Stanton Korista, Lawrence C. Novak / SOM / CTBUH','Primary engineering drawings: core plan, elevations, setbacks; design-stage drawing cross-checked against built photos'),('ctbuh-case-study.pdf','https://global.ctbuh.org/resources/papers/download/2828-burj-khalifa-dubai-uae.pdf','SOM / CTBUH','Built tower case study, elevations and floor plans')]
    page='https://www.som.com/projects/burj-khalifa/'
    text=''
    for url,name in [('https://r.jina.ai/'+page,'som-reader.txt'),(page,'som.html')]:
        try:
            raw=get(url,PAGES/name);s=raw.decode('utf-8');text+='\n'+s;print('PAGE',name,len(raw),flush=True)
        except Exception as e:print('PAGE_FAILED',name,str(e),flush=True)
    # Archive actual source photography, not generated reference imagery.
    text=text.replace('\\/','/')
    urls=list(dict.fromkeys(html.unescape(u) for u in re.findall(r'https?://[^\s<>"\)\\]+\.(?:jpg|jpeg|webp|png)',text)))
    urls=[u for u in urls if '/uploads/20' in u and '203188' in u and not re.search(r'-\d+x\d+\.',u)]
    for i,url in enumerate(urls[:24]):refs.append((f'original-{i:02d}.'+url.rsplit('.',1)[-1],url,'Nick Merrick / Hedrich Blessing / SOM (satellite: Go Eye Satellite); individual credits in source page','Built exterior / ground / crown / aerial / detail; see source page caption'))
    with ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(save,refs))
    (REF/'download-manifest.json').write_text(json.dumps(dict(collected='2026-10-20',official=page,files=result),ensure_ascii=False,indent=2),encoding='utf-8')
    print('REFERENCES',[(x['file'],x['status'],x.get('pixels')) for x in result],flush=True)
    # Drawings supplied by the architect to ArchDaily; retain original attribution.
    ad=PAGES/'archdaily.html'
    if ad.exists():
        doc=ad.read_text(encoding='utf-8')
        urls=list(dict.fromkeys(re.findall(r'https://images.adsttc.com/[^\s\x22<>]+',doc)))
        drawings=[]
        for u in urls:
            if '/medium_jpg/' not in u or not any(s in u.lower() for s in ['typical_plan','elevator_section','program_axonometric']):continue
            u=u.rstrip("'").replace('/medium_jpg/','/large_jpg/')
            name='som-'+('plan' if 'typical' in u else 'section' if 'section' in u else 'axonometric')+'.jpg'
            drawings.append(save((name,u,'© SOM, architect-supplied drawings published by ArchDaily 2017-10-23','Primary architect drawing: plan / section / program axonometric')))
        result+=drawings
        (REF/'download-manifest.json').write_text(json.dumps(dict(collected='2026-10-20',official=page,drawings_page='https://www.archdaily.com/882100/burj-khalifa-som',files=result),ensure_ascii=False,indent=2),encoding='utf-8')
    osm=REF/'osm-context.json'
    if osm.exists() and len(json.loads(osm.read_text(encoding='utf-8')).get('elements',[]))<100:osm.unlink()
    if not osm.exists():
        q='[out:json][timeout:180];(way[building](around:2050,25.197197,55.274375);way["building:part"](around:2050,25.197197,55.274375);way[highway](around:2050,25.197197,55.274375);way[leisure=park](around:2050,25.197197,55.274375);way[landuse=grass](around:2050,25.197197,55.274375);way[natural=water](around:2050,25.197197,55.274375);relation[natural=water](around:2050,25.197197,55.274375););out tags geom;'
        (REF/'overpass-query.txt').write_text(q)
        for host in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass.private.coffee/api/interpreter']:
            try:
                raw=get(host,osm,urllib.parse.urlencode({'data':q}).encode());doc=json.loads(raw)
                if len(doc.get('elements',[]))<100:raise ValueError('Incomplete district response')
                print('OSM',len(doc['elements']),flush=True);break
            except Exception as e:
                if osm.exists():osm.unlink()
                print('OSM_FAILED',host,str(e),flush=True)
    if osm.exists():
        doc=json.loads(osm.read_text(encoding='utf-8'))
        print('LANDMARKS',[(x['id'],x.get('tags')) for x in doc['elements'] if any(k in x.get('tags',{}).get('name','').lower() for k in ['khalifa','dubai mall','opera','address','fountain','burj park'])],flush=True)
if __name__=='__main__':main()
