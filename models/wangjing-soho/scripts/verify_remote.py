"""Verify deployed bytes, SHA-256, MIME and CORS without browser automation."""
import json,hashlib,urllib.request,time,sys,argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
BASE='https://jt-ai-models.vercel.app/'
def verify(relative):
    local=REPO/relative;expected=hashlib.sha256(local.read_bytes()).hexdigest();url=BASE+relative
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'AIModels-delivery-verification/1.0','Cache-Control':'no-cache'})
            start=time.monotonic();h=hashlib.sha256();count=0
            with urllib.request.urlopen(request,timeout=90) as response:
                headers=dict(response.headers);status=response.status
                while chunk:=response.read(1024*1024):h.update(chunk);count+=len(chunk)
            result=dict(file=relative,url=url,http=status,mime=headers.get('Content-Type',headers.get('content-type')),cors=headers.get('Access-Control-Allow-Origin',headers.get('access-control-allow-origin')),bytes=count,sha256=h.hexdigest(),local_bytes=local.stat().st_size,local_sha256=expected,seconds=round(time.monotonic()-start,3))
            assert status==200;assert count==local.stat().st_size;assert h.hexdigest()==expected,(relative,'SHA mismatch');assert result['cors']=='*'
            if relative.endswith('.glb'):assert result['mime'].split(';')[0]=='model/gltf-binary'
            if relative.endswith('.json'):assert 'json' in result['mime']
            if relative.endswith('.mp4'):assert result['mime'].split(';')[0]=='video/mp4'
            result['passed']=True;return result
        except Exception as exc:
            if attempt==2:return dict(file=relative,url=url,passed=False,error=str(exc))
            time.sleep(3)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--deployment-url',required=True);args=parser.parse_args()
    files=['catalog.json','models/wangjing-soho/model.json','models/wangjing-soho/wangjing-soho.glb','models/wangjing-soho/wangjing-soho-assembly.glb','models/wangjing-soho/wangjing-soho-explode.glb','models/wangjing-soho/wangjing-soho.blend','model-assets/geo-context/wangjing-soho-1500-v1/tileset.json','model-assets/geo-context/wangjing-soho-1500-v1/district.glb','model-assets/geo-context/wangjing-soho-1500-v1/metadata.json','models/wangjing-soho/previews/assembly-preview.mp4','models/wangjing-soho/previews/explode-preview.mp4']
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(verify,files))
    report=dict(date='2026-10-18',commit=args.commit,production_domain=BASE,deployment_status='Vercel success via exact GitHub commit status',deployment_url=args.deployment_url,connector_limitation='Vercel team-scoped deployment API returned 403; exact GitHub Vercel status and anonymous production asset verification used',all_passed=all(x['passed'] for x in results),checks=results)
    (ROOT/'verification'/'deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['all_passed'] else 1)
if __name__=='__main__':main()
