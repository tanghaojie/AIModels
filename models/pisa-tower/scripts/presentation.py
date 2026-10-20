"""Build labeled contact sheets and a portfolio board from actual Blender outputs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'previews'
def font(n,bold=False):
    candidates=[Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf'),Path('C:/Windows/Fonts/msyh.ttc')]
    return ImageFont.truetype(str(next(p for p in candidates if p.exists())),n)
def sheet(name,files,labels,cols=4):
    w,h=480,360;rows=(len(files)+cols-1)//cols;out=Image.new('RGB',(w*cols,(h+54)*rows),(21,25,27));d=ImageDraw.Draw(out)
    for i,(file,label) in enumerate(zip(files,labels)):
        im=Image.open(P/file).convert('RGB');im=ImageOps.contain(im,(w,h));x=(i%cols)*w;y=(i//cols)*(h+54);out.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2));d.text((x+16,y+h+12),label,font=font(19),fill=(219,216,207))
    out.save(P/name)
def main():
    sheet('day-night-contact.jpg',[p+'.png' for p in ['day','sunset','blue','night']],['01  DAYLIGHT','02  SUNSET','03  BLUE HOUR','04  NIGHT'],cols=2)
    frames=[0,30,150,210,420,630,720,840]
    sheet('assembly-contact.jpg',['assembly-%03d.png'%f for f in frames],['%02d  |  %.1f s'%(i+1,f/30) for i,f in enumerate(frames)])
    frames=[0,90,180,270,360]
    sheet('explode-contact.jpg',['explode-%03d.png'%f for f in frames],['EXPLODE  |  %.1f s'%(f/30) for f in frames],cols=3)
    sheet('views-contact.jpg',[p+'.png' for p in ['low','rear','detail','aerial','district']],['LOW / SOUTH ENTRANCE','NORTH-EAST / REAR','MARBLE / LOGGIA DETAIL','PIAZZA DEI MIRACOLI','RADIUS 1000 m / OSM'],cols=3)
    # Quiet typography, two complete hero frames and an evidence strip.
    board=Image.new('RGB',(2400,2200),(20,25,28));d=ImageDraw.Draw(board)
    d.text((84,58),'TORRE PENDENTE',font=font(90,True),fill=(239,231,209));d.text((88,170),'PISA, ITALY  /  ARCHITECTURAL RECONSTRUCTION  /  2026',font=font(26),fill=(161,178,181))
    d.line((88,228,2312,228),fill=(143,117,71),width=2)
    for i,(file,label) in enumerate([('beauty-day.png','01 / MARBLE IN DAYLIGHT'),('beauty-night.png','02 / ARCHITECTURAL FLOODLIGHT')]):
        im=ImageOps.contain(Image.open(P/file).convert('RGB'),(1100,850));x=88+i*1136;board.paste(im,(x+(1100-im.width)//2,268+(850-im.height)//2));d.text((x,1140),label,font=font(26,True),fill=(228,218,192))
    for i,(file,label) in enumerate([('detail.png','CRAFT / LOGGIA'),('assembly-420.png','CHOREOGRAPHY / 14 s'),('explode-360.png','COMPONENT STUDY / 12 s'),('district.png','URBAN CONTEXT / 1 km')]):
        x=88+i*566;im=ImageOps.contain(Image.open(P/file).convert('RGB'),(534,430));board.paste(im,(x+(534-im.width)//2,1250+(430-im.height)//2));d.text((x,1720),label,font=font(21,True),fill=(185,199,198))
    d.line((88,1802,2312,1802),fill=(86,101,104),width=1)
    for i,(big,small) in enumerate([('224','ANIMATED COMPONENTS'),('207','COLUMN CAPITALS'),('28 s','EIGHT-DIRECTION ASSEMBLY'),('2,664','MAPPED BUILDING FOOTPRINTS')]):
        x=88+i*566;d.text((x,1850),big,font=font(65,True),fill=(231,217,183));d.text((x,1943),small,font=font(20),fill=(161,178,181))
    d.text((88,2070),'BLENDER 5.2.1  /  PBR  /  CORE glTF TRS  /  EDITABLE SOURCE',font=font(23),fill=(166,180,180))
    d.text((88,2120),'Context: OpenStreetMap contributors / ODbL. Heights, facade details and historic ornament are visualization estimates.',font=font(19),fill=(126,144,145))
    board.save(P/'portfolio-board.jpg',quality=95)
    files=[]
    for p in sorted(P.glob('*')):
        if p.is_file() and p.suffix.lower() in ['.png','.jpg','.mp4'] and 'draft' not in p.name:
            row=dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            if p.suffix!='.mp4':row['pixels']=list(Image.open(p).size)
            files.append(row)
    (ROOT/'verification/preview-manifest.json').write_text(json.dumps(dict(renderer='Blender 5.2.1, EEVEE stages + Cycles 32-sample hero pair',color_management='AgX',timezone='Asia/Singapore',date='2026-10-21',actual_engine_acceptance='not performed',files=files),indent=2),encoding='utf-8')
    print('PREVIEW_FILES',len(files))
if __name__=='__main__':main()
