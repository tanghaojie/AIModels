"""Save original research images, an archival drawing and dated OSM geometry."""
from pathlib import Path
import requests, re, json, hashlib, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'references';REF.mkdir(parents=True,exist_ok=True)
SESSION=requests.Session()
SESSION.headers['User-Agent']='AIModels architectural research (https://github.com/tanghaojie/AIModels)'

def get(url,path,data=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size>200:return path.read_bytes()
    r=SESSION.post(url,data=data,timeout=160) if data else SESSION.get(url,timeout=70)
    r.raise_for_status();path.write_bytes(r.content);return r.content

def main():
    manifest=[]
    pages={
      'tower':'https://www.opapisa.it/en/square-of-miracles/tower/',
      'tower-details':'https://www.opapisa.it/visita/torre-pendente/',
      'cathedral':'https://www.opapisa.it/en/square-of-miracles/cathedral/',
      'baptistery':'https://www.opapisa.it/en/square-of-miracles/baptistery/',
      'cemetery':'https://www.opapisa.it/en/square-of-miracles/camposanto/',
    }
    for key,url in pages.items():
        try:
            raw=get(url,REF/'restricted'/(key+'.html')).decode('utf-8',errors='replace')
            urls=list(dict.fromkeys(re.findall(r'https?[^\s\"<>]+?\.(?:jpg|jpeg|png)',raw)))
            urls=[u for u in urls if '/uploads/' in u and not any(v in u.lower() for v in ['logo','icon','banner','sprite'])]
            print(key,'photo candidates',urls[:12],flush=True)
            for i,u in enumerate(urls[:12 if 'tower' in key else 3]):
                path=REF/'restricted'/(key+'-%02d'%i+Path(urllib.parse.urlparse(u).path).suffix)
                try:
                    data=get(u,path)
                    from PIL import Image
                    with Image.open(path) as im:wh=list(im.size)
                    if min(wh)<200:continue
                    manifest.append(dict(file=path.relative_to(REF).as_posix(),url=u,source_page=url,author='Opera della Primaziale Pisana / credited photographer on source page',license='Copyright retained; local research and user acceptance only; excluded from Git',use=key+' photographic reference',pixels=wh,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
                except Exception as e: print('PHOTO ERROR',str(e)[:160],flush=True)
        except Exception as e:print('PAGE ERROR',url,str(e),flush=True)
    for filename,url,credit,license,use in [
      ('overall-terredipisa.jpg','https://www.terredipisa.it/wp-content/uploads/2022/11/torre-di-pisa.jpg','Terre di Pisa','Local research only; excluded from Git','Arcade and capital close-up'),
      ('full-tower-municipal.jpg','https://www.turismo.pisa.it/sites/default/files/immagini/schede-luogo/Torre%20di%20Pisa%20PRIMAZIALE.PISA_.01.20.044.jpg','Opera Primaziale Pisana via Comune di Pisa','Local research only; excluded from Git','Full tower from eastern side and adjacent cathedral'),
      ('tower-cathedral-municipal.jpg','https://www.turismo.pisa.it/sites/default/files/immagini/schede-luogo/torre-cattedrale.jpg','Comune di Pisa','Local research only; excluded from Git','Tower and cathedral composition'),
      ('square-panorama-municipal.jpg','https://www.turismo.pisa.it/sites/default/files/immagini/schede-luogo/Veduta%20piazza%20del%20Duomo_0.jpg','Comune di Pisa','Local research only; excluded from Git','Square panorama'),
      ('grassi-elevation-section.jpg','https://cdn.loc.gov/service/pnp/pga/10800/10824v.jpg','Raniero Grassi / Library of Congress, LCCN 2003688771','Public domain / no known restrictions on publication','Historical elevation and cutaway; historic lean is not current survey'),
      ('isprs-survey-2003.pdf','https://www.isprs.org/proceedings/xxxiv/5-W12/proceedings/04.pdf','ISPRS 2003 proceedings, paper 04','Local research copy only; excluded from Git','Photogrammetric north-south section, curvature, survey method')]:
        path=REF/filename if filename=='grassi-elevation-section.jpg' else REF/'restricted'/filename
        try:
            data=get(url,path);manifest.append(dict(file=path.relative_to(REF).as_posix(),url=url,author=credit,license=license,use=use,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        except Exception as e:print('REF ERROR',str(e),flush=True)
    (REF/'download-manifest.json').write_text(json.dumps(dict(collected='2026-10-20',files=manifest),ensure_ascii=False,indent=2),encoding='utf-8')
    osm=REF/'osm-context.json'
    if not osm.exists():
        q='[out:json][timeout:140];(way[building](around:1080,43.722952,10.396595);relation[building](around:1080,43.722952,10.396595);way[highway](around:1080,43.722952,10.396595);way[landuse](around:1080,43.722952,10.396595);way[leisure](around:1080,43.722952,10.396595);way[natural](around:1080,43.722952,10.396595);way[barrier=city_wall](around:1080,43.722952,10.396595);node[natural=tree](around:1080,43.722952,10.396595););out body geom;'
        (REF/'overpass-query.txt').write_text(q,encoding='utf-8')
        for host in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
            try:
                raw=get(host,osm,data={'data':q});doc=json.loads(raw);print('OSM',len(doc['elements']),doc.get('osm3s'),flush=True);break
            except Exception as e:print('OSM ERROR',str(e),flush=True)
    if osm.exists():
        doc=json.loads(osm.read_text(encoding='utf-8'))
        for f in doc['elements']:
            t=f.get('tags',{})
            if t.get('building') and any(k in t.get('name','').lower() for k in ['torre','cattedrale','battister','camposanto','duomo']):print('LANDMARK',f['type'],f['id'],t.get('name'),flush=True)
    print('SAVED REFERENCES',len(manifest),flush=True)

if __name__=='__main__':main()
