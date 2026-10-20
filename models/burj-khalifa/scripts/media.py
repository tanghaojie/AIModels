"""Encode deterministic review movies and assemble an original portfolio board."""
from common import *
import subprocess,shutil,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageOps
PRE=ROOT/'previews'
def font(size,bold=False):
    p=Path('C:/Windows/Fonts')/('seguisb.ttf' if bold else 'segoeui.ttf')
    return ImageFont.truetype(str(p),size) if p.exists() else ImageFont.load_default(size=size)
def fit(path,size):
    return ImageOps.fit(Image.open(path).convert('RGB'),size,method=Image.Resampling.LANCZOS,centering=(.5,.45))
def movies():
    exe=shutil.which('ffmpeg');assert exe,'FFmpeg is required'
    result=[]
    for name,count,duration in [('assembly',540,36),('explode',210,14)]:
        folder=PRE/'frames'/name;frames=sorted(folder.glob('*.png'));assert len(frames)==count,(name,len(frames))
        output=PRE/(name+'.mp4')
        subprocess.run([exe,'-hide_banner','-loglevel','error','-y','-framerate','15','-i',str(folder/'%04d.png'),'-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
        probe=shutil.which('ffprobe');metadata=json.loads(subprocess.check_output([probe,'-v','error','-show_format','-show_streams','-of','json',str(output)]))
        assert abs(float(metadata['format']['duration'])-duration)<.05
        result.append(dict(file=output.name,bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),probe=metadata))
    return result
def board():
    bg='#f1f0eb';ink='#182c35';muted='#586a70';accent='#a7895d'
    im=Image.new('RGB',(3000,2080),bg);d=ImageDraw.Draw(im)
    d.text((75,46),'BURJ KHALIFA',font=font(102,True),fill=ink)
    d.text((82,171),'ARCHITECTURAL RECONSTRUCTION  /  DUBAI  /  BLENDER 5.2',font=font(27),fill=muted)
    d.line((80,235,2920,235),fill=accent,width=3)
    hero=Image.open(PRE/'beauty-sunset.png').convert('RGB');hero=ImageOps.contain(hero,(1120,1570),Image.Resampling.LANCZOS)
    im.paste(hero,(80+(1120-hero.width)//2,285))
    d.text((80,1900),'01  /  LIGHT, FORM & SILVER CLADDING',font=font(26,True),fill=ink)
    d.text((80,1945),'Cycles / OptiX / AgX / 64 samples',font=font(23),fill=muted)
    x=1270;w=790;h=600
    im.paste(fit(PRE/'detail.png',(w,h)),(x,285));im.paste(fit(PRE/'entry.png',(w,h)),(x+w+45,285))
    d.text((x,910),'02  /  CURTAIN WALL & MECHANICAL BANDS',font=font(23,True),fill=ink)
    d.text((x+w+45,910),'03  /  GROUND ARRIVAL & LANDSCAPE',font=font(23,True),fill=ink)
    stats=[('828 m','ARCHITECTURAL HEIGHT'),('276','MOVING GROUPS'),('120 m','ASSEMBLY ALTITUDE'),('2 km','DISTRICT RADIUS')]
    for i,(value,label) in enumerate(stats):
        xx=x+i*415;d.text((xx,1010),value,font=font(67,True),fill=ink);d.text((xx,1102),label,font=font(19),fill=muted)
    d.line((x,1170,2920,1170),fill='#c7cbc6',width=2)
    d.text((x,1220),'BUILD FROM THE SKY',font=font(45,True),fill=ink)
    d.text((x,1291),'Descending components / assembly at +120 m / controlled landing',font=font(24),fill=muted)
    names=['assembly-0270','assembly-0540','assembly-0810','assembly-1080'];labels=['09 s  /  CORE & FLOORS','18 s  /  FACADE','27 s  /  HOVER','36 s  /  LANDED']
    for i,(name,label) in enumerate(zip(names,labels)):
        xx=x+i*415;im.paste(fit(PRE/(name+'.png'),(385,289)),(xx,1360));d.text((xx,1675),label,font=font(20,True),fill=ink)
    d.text((x,1785),'EDITABLE SOURCE + STATIC / ASSEMBLY / EXPLODE GLB',font=font(26,True),fill=ink)
    d.text((x,1830),'Primary tower drawings: SOM. Context: OpenStreetMap contributors (ODbL).',font=font(22),fill=muted)
    d.text((x,1870),'Visualization reconstruction; estimated details and heights documented.',font=font(22),fill=muted)
    d.text((x,1910),'Dubai Mall main volume: approximate aerial trace; not surveyed.',font=font(22),fill=muted)
    d.text((80,2020),'AIModels  /  2026.10  /  CS-AM-1',font=font(22),fill=muted)
    d.text((2470,2020),'01  /  FORM & MOTION',font=font(22),fill=muted)
    im.save(PRE/'portfolio.jpg',quality=94,subsampling=0)
def contacts():
    for name,files in [('motion-contact',['assembly-0000','assembly-0270','assembly-0540','assembly-0810','assembly-0960','assembly-1080','explode-0000','explode-0210','explode-0420']),('lighting-contact',['day','sunset','blue','night','entry','rear','aerial','detail','district'])]:
        out=Image.new('RGB',(1800,1530),'#f1f0eb');d=ImageDraw.Draw(out)
        for i,file in enumerate(files):
            picture=ImageOps.contain(Image.open(PRE/(file+'.png')).convert('RGB'),(584,462),Image.Resampling.LANCZOS);x=(i%3)*600;y=(i//3)*510
            out.paste(picture,(x+(600-picture.width)//2,y));d.text((x+10,y+472),file,font=font(22),fill='#182c35')
        out.save(PRE/(name+'.jpg'),quality=92)
def main():
    clips=movies();board();contacts();write(ROOT/'verification'/'media.json',dict(renderer='Blender 5.2.1',movies=clips,still_rendering='Eevee, 32 samples; beauty-sunset Cycles 64 samples',movie_rendering='Eevee, 16 samples, 15 fps, 1280x960; same 30 fps source poses sampled every second frame',visual_review='See visual-review.md'))
    print('MEDIA_COMPLETE',[(c['file'],c['bytes']) for c in clips],flush=True)
if __name__=='__main__':main()
