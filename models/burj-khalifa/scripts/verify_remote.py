"""Stream production resources and compare full bytes against the Git revision."""
from common import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
import urllib.request,hashlib,subprocess,time,argparse,tempfile
RESOLVE_IP=None
BASE='https://jt-ai-models.vercel.app/'
FILES=['catalog.json','models/burj-khalifa/model.json','models/burj-khalifa/burj-khalifa.glb','models/burj-khalifa/burj-khalifa-assembly.glb','models/burj-khalifa/burj-khalifa-explode.glb','models/burj-khalifa/burj-khalifa.blend','model-assets/geo-context/burj-khalifa-2000-v1/tileset.json','model-assets/geo-context/burj-khalifa-2000-v1/district.glb','models/burj-khalifa/previews/assembly.mp4','models/burj-khalifa/previews/explode.mp4','models/burj-khalifa/previews/portfolio.jpg']

def download(path):
    h=hashlib.sha256();count=0;raw=bytearray() if path.endswith('.json') else None
    def consume(stream):
        nonlocal count
        while True:
            chunk=stream.read(1024*1024)
            if not chunk:break
            h.update(chunk);count+=len(chunk)
            if raw is not None:raw.extend(chunk)
    if RESOLVE_IP:
        # Optional per-request DNS override, using a freshly resolved address.
        # The original HTTPS hostname and certificate verification stay intact.
        cache=ROOT/'local'/'remote-check';cache.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            headers=Path(tmp)/'headers.txt'
            with (Path(tmp)/'stderr.txt').open('wb+') as err:
                cmd=['curl','--silent','--show-error','--fail','--location','--connect-timeout','30','--max-time','300','--resolve','jt-ai-models.vercel.app:443:'+RESOLVE_IP,'--dump-header',str(headers),'--output','-',BASE+path]
                with subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=err) as proc:
                    consume(proc.stdout);code=proc.wait()
                err.seek(0);message=err.read().decode('utf-8',errors='replace')
                assert code==0,(path,'curl',code,message)
            blocks=headers.read_text(encoding='utf-8').replace('\r\n','\n').strip().split('\n\n')
            lines=blocks[-1].splitlines();assert int(lines[0].split()[1])==200,(path,lines[0])
            fields={k.lower():v.strip() for k,v in (line.split(':',1) for line in lines[1:] if ':' in line)}
            mime=fields.get('content-type','').split(';')[0];cors=fields.get('access-control-allow-origin')
    else:
        req=urllib.request.Request(BASE+path,headers={'User-Agent':'AIModels full-byte deployment verification/1.0','Cache-Control':'no-cache'})
        with urllib.request.urlopen(req,timeout=120) as response:
            assert response.status==200;consume(response)
            mime=response.headers.get('Content-Type','').split(';')[0];cors=response.headers.get('Access-Control-Allow-Origin')
    return h.hexdigest(),count,raw,mime,cors
def verify(path):
    local=(REPO/path).read_bytes();expected=subprocess.check_output(['git','show','HEAD:'+path],cwd=REPO)
    if local!=expected:
        assert path.endswith('.json') and json.loads(local)==json.loads(expected),'Unexpected local/Git difference'
    sha=hashlib.sha256(expected).hexdigest()
    for attempt in range(3):
        try:
            start=time.monotonic()
            remote_sha,count,raw,mime,cors=download(path)
            assert cors=='*',(path,'CORS',cors)
            assert remote_sha==sha and count==len(expected),(path,'Byte mismatch',count,len(expected))
            if path.endswith('.glb'):assert mime=='model/gltf-binary',(path,mime)
            elif path.endswith('.json'):assert mime=='application/json',(path,mime)
            elif path.endswith('.mp4'):assert mime=='video/mp4',(path,mime)
            if path=='catalog.json':assert any(x['id']=='burj-khalifa' for x in json.loads(raw)['models'])
            if path.endswith('/model.json'):
                model=json.loads(raw);assert model['defaultMode']=='assembly';assert {x['id'] for x in model['modes']}=={'assembly','explode'}
            out=dict(path=path,url=BASE+path,http=200,mime=mime,cors=cors,bytes=count,sha256=sha,full_byte_match=True,comparison='Git HEAD bytes; local JSON line endings may be normalized',download_elapsed_s=round(time.monotonic()-start,3))
            print('VERIFIED',path,count,sha[:12],flush=True);return out
        except Exception:
            if attempt==2:raise
            time.sleep(5)
def main():
    global RESOLVE_IP
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolve-ip',help='Optional freshly resolved address; curl keeps normal HTTPS certificate checks.')
    RESOLVE_IP=parser.parse_args().resolve_ip
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(verify,FILES))
    write(ROOT/'verification'/'remote.json',dict(status='passed',verified_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),git_commit=commit,production_base=BASE,transport='curl with per-request DNS override' if RESOLVE_IP else 'urllib',resolved_ip=RESOLVE_IP,https_certificate_verification=True,files=results,frontend_browser_tested=False))
    print('REMOTE_VERIFICATION_PASSED',len(results),'resources',flush=True)
if __name__=='__main__':main()
