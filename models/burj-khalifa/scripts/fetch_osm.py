"""Bounding-box query fallback when Overpass around queries time out."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,urllib.parse,json,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
REL='--relations' in sys.argv
q='[out:json][timeout:90][bbox:25.1789,55.2543,25.2155,55.2945];'+('(relation[building];relation["building:part"];);out tags geom;' if REL else '(way[building];way["building:part"];way[highway];way[natural=water];way[leisure=park];way[landuse=grass];relation[natural=water];);out tags geom;')
(ROOT/'references'/('overpass-relations-query.txt' if REL else 'overpass-query.txt')).write_text(q)
def run(host):
    try:
        req=urllib.request.Request(host+'?'+urllib.parse.urlencode({'data':q}),headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
        d=json.loads(raw)
        if len(d.get('elements',[]))<(2 if REL else 100):raise ValueError('Insufficient map coverage')
        dest=ROOT/'references'/('osm-'+host.split('/')[2]+'.json');dest.write_bytes(raw)
        (ROOT/'references'/('osm-relations.json' if REL else 'osm-context.json')).write_bytes(raw)
        print('SAVED',host,len(d['elements']),len(raw),flush=True)
    except Exception as e:print('FAILED',host,str(e),flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass.private.coffee/api/interpreter']))
