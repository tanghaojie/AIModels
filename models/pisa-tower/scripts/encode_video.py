"""Encode actual Blender 10-fps preview frames as a 30-fps silent H.264 film.
Geometry animation source and GLB are sampled at 30 fps; preview repeats frames.
"""
from pathlib import Path
import subprocess,json
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'previews'
def main():
    ff=imageio_ffmpeg.get_ffmpeg_exe();reports=[]
    for mode,duration in [('video',28),('explode',12)]:
        frames=PRE/'frames'/mode
        if not frames.exists():continue
        expected=round(duration*10)+1;files=sorted(frames.glob('*.png'))
        if len(files)<expected:print('RENDER_PENDING',mode,len(files),'of',expected,flush=True);continue
        assert len(files)==expected,(mode,len(files),expected)
        out=PRE/('assembly-film.mp4' if mode=='video' else 'explode-film.mp4')
        subprocess.run([ff,'-y','-framerate','10','-i',str(frames/'%04d.png'),'-t',str(duration),'-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        # Decode the complete file after encoding to catch corrupt/truncated frames.
        subprocess.run([ff,'-v','error','-i',str(out),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        probe=subprocess.run([ff,'-i',str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        reports.append(dict(file=out.name,duration_s=duration,width=960,height=720,container_fps=30,rendered_fps=10,decoded='complete file decoded without errors',probe=probe.stderr))
    (ROOT/'verification/video.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');print(json.dumps([{k:v for k,v in p.items() if k!='probe'} for p in reports],indent=2))
if __name__=='__main__':main()
