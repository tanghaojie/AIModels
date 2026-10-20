"""Verify a Git-push Vercel release by its exact commit and complete public bytes.
No Vercel account secrets, browser automation or deployment mutation.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,subprocess,json,hashlib,time,sys
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
BASE='https://jt-ai-models.vercel.app/'
SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()

def release_status():
    url=f'https://api.github.com/repos/tanghaojie/AIModels/commits/{SHA}/status'
    for attempt in range(40):
        r=requests.get(url,timeout=30);r.raise_for_status();d=r.json()
        states=[s for s in d.get('statuses',[]) if s['context'].lower()=='vercel' and '/tanghaojies-projects/ai-models/' in (s.get('target_url') or '')]
        if states:
            s=states[0]
            if s['state']=='success':return dict(commit=SHA,state=s['state'],description=s.get('description'),url=s.get('target_url'),updated_at=s.get('updated_at'),source='GitHub Vercel commit status; Vercel API access unavailable')
            if s['state'] in ['failure','error']:raise RuntimeError(s)
        if attempt%4==0:print('WAITING_VERCEL',SHA[:10],states[0]['state'] if states else 'status not yet posted',flush=True)
        time.sleep(15)
    raise TimeoutError('Vercel did not report success within the bounded wait')

def verify_file(path):
    rel=path.relative_to(REPO).as_posix();url=BASE+rel
    expected=hashlib.sha256(path.read_bytes()).hexdigest();last=None
    for attempt in range(5):
        try:
            with requests.get(url,stream=True,timeout=(20,100),headers={'Cache-Control':'no-cache'}) as r:
                r.raise_for_status();h=hashlib.sha256();size=0
                for chunk in r.iter_content(1024*1024):h.update(chunk);size+=len(chunk)
                assert h.hexdigest()==expected,(rel,'hash mismatch')
                assert size==path.stat().st_size
                cors=r.headers.get('Access-Control-Allow-Origin');assert cors=='*',(rel,cors)
                mime=r.headers.get('Content-Type','').split(';')[0]
                if path.suffix=='.glb':assert mime=='model/gltf-binary',(rel,mime)
                if path.suffix=='.json':assert mime=='application/json',(rel,mime)
                return dict(file=rel,url=url,status=r.status_code,mime=mime,cors=cors,bytes=size,sha256=expected)
        except Exception as e:last=e;time.sleep(3*(attempt+1))
    raise last

def main():
    status=release_status();print('VERCEL_SUCCESS',json.dumps(status),flush=True)
    files=[REPO/'catalog.json',ROOT/'model.json',ROOT/'pisa-tower.glb',ROOT/'pisa-tower-assembly.glb',ROOT/'pisa-tower-explode.glb',ROOT/'pisa-tower.blend',REPO/'model-assets/geo-context/pisa-1000-v1/tileset.json',REPO/'model-assets/geo-context/pisa-1000-v1/scene.json',REPO/'model-assets/geo-context/pisa-1000-v1/district.glb',ROOT/'previews/day.png',ROOT/'previews/portfolio-board.jpg',ROOT/'previews/assembly-film.mp4',ROOT/'previews/explode-film.mp4']
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(verify_file,files))
    result=dict(verified_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),asset_commit=SHA,vercel=status,files=results,frontend_acceptance='Not performed; maintainer manual acceptance required')
    if '--no-write' not in sys.argv:(ROOT/'verification/deployment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(commit=SHA,vercel='success',files=len(results),full_bytes_sha256='all matched',mime_cors='all matched'),indent=2))
if __name__=='__main__':main()
