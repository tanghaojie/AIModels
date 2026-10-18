"""Probe and decode the actual encoded videos, plus image/dependency evidence."""
from pathlib import Path
import subprocess,json,hashlib,importlib.metadata
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
    videos=[]
    for name,duration in [('assembly',30),('explode',12)]:
        path=ROOT/'previews'/(name+'-preview.mp4')
        doc=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
        v=next(x for x in doc['streams'] if x['codec_type']=='video')
        assert (v['width'],v['height'])==(960,660);assert v['avg_frame_rate']=='30/1';assert abs(float(doc['format']['duration'])-duration)<.05
        for t,label in [(0,'start'),(duration/2,'middle'),(duration-.1,'end')]:
            sample=ROOT/'verification'/(name+'-video-'+label+'.png')
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(path),'-frames:v','1',str(sample)],check=True)
            with Image.open(sample) as im:assert im.size==(960,660)
        videos.append(dict(file=path.name,codec=v['codec_name'],pixels=[v['width'],v['height']],fps=v['avg_frame_rate'],duration_s=float(doc['format']['duration']),frames=int(v['nb_frames']),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),decoded_samples=['start','middle','end'],render_sampling_fps=10,container_fps=30))
    images=[]
    for name in ['beauty-day','day','sunset','blue','night','low','rear','aerial','detail','district']:
        path=ROOT/'previews'/(name+'.png')
        with Image.open(path) as im:im.verify()
        with Image.open(path) as im:images.append(dict(file=path.name,pixels=list(im.size),bytes=path.stat().st_size))
    dependencies={n:importlib.metadata.version(n) for n in ['numpy','Pillow','shapely','pyproj','mapbox-earcut','overturemaps']}
    result=dict(videos=videos,images=images,python_dependencies=dependencies,source='Actual saved Blender outputs and actual encoded MP4; no browser execution')
    (ROOT/'verification'/'media.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
