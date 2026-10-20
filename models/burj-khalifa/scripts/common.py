from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
# Optional local dependency location used in this recorded build. A normal venv
# with requirements.txt works without this path.
for local in [REPO/'tmp'/'burj-libs',ROOT/'local'/'python']:
    if local.exists():sys.path.insert(0,str(local))
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
CONTEXT=REPO/'model-assets'/'geo-context'/'burj-khalifa-2000-v1'
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_compact(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8')+b'\n')
