"""A presentation board composed entirely from the delivered Blender renders."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
R=Path(__file__).resolve().parents[1];P=R/'previews'
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('seguisb.ttf' if bold else 'segoeui.ttf'),size)
def main():
    im=Image.new('RGB',(2400,1800),(17,25,34));d=ImageDraw.Draw(im)
    d.text((60,46),'WANGJING SOHO',font=font(74,True),fill=(240,242,239));d.text((63,145),'FLOATING ASSEMBLY  /  ARCHITECTURAL RECONSTRUCTION  /  BEIJING',font=font(26),fill=(152,173,189))
    def panel(file,box):
        with Image.open(P/file) as src:im.paste(ImageOps.fit(src.convert('RGB'),(box[2],box[3])),box[:2])
    panel('beauty-day.png',(60,220,1510,1040));panel('night.png',(1600,220,740,505));panel('detail.png',(1600,755,740,505))
    for file,x,label in [('assembly-000.png',60,'01  /  EMPTY SITE'),('assembly-660.png',830,'02  /  85 m ASSEMBLY'),('assembly-900.png',1600,'03  /  GROUNDING')]:
        panel(file,(x,1320,740,310));d.text((x,1644),label,font=font(22,True),fill=(207,180,127))
    d.text((60,1280),'CYCLES  /  757,278 TRIANGLES  /  404 ANIMATED PARTS',font=font(22),fill=(196,207,216))
    d.text((60,1710),'1500 m RADIUS  |  1463 REAL FOOTPRINTS  |  30 s ASSEMBLY + LANDING  |  12 s EXPLODED VIEW',font=font(24,True),fill=(225,231,233))
    d.text((60,1760),'Architecture: ZHA / CCDI  ·  Independent AIModels reconstruction  ·  © OSM contributors / Overture / East Asian Buildings. Heights partly estimated.',font=font(17),fill=(136,157,173))
    im.save(P/'portfolio-board.jpg',quality=94)
if __name__=='__main__':main()
