"""Original editorial overlay and mandatory source attribution for preview videos."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    font=Path('C:/Windows/Fonts/msyh.ttc');latin=Path('C:/Windows/Fonts/segoeui.ttf')
    if not font.exists():raise RuntimeError('Set a Chinese-capable font path for this platform')
    for name,title,caption in [('assembly','FLOATING ASSEMBLY','404 个构件 · 高空 85 米组装 · 整体降落'),('explode','EXPLODED SYSTEMS','分层楼板 · 幕墙分区 · 12 秒爆炸分解')]:
        im=Image.new('RGBA',(960,660));d=ImageDraw.Draw(im)
        d.rounded_rectangle((20,18,570,96),radius=8,fill=(12,21,31,190))
        d.rectangle((20,34,23,79),fill=(205,173,112,255))
        d.text((38,26),'WANGJING SOHO  /  '+title,font=ImageFont.truetype(str(latin),21),fill=(242,243,241,255))
        d.text((38,61),caption,font=ImageFont.truetype(str(font),15),fill=(197,211,221,255))
        d.rectangle((0,633,960,660),fill=(12,21,31,210))
        d.text((14,638),'AIModels  |  © OpenStreetMap contributors · Overture · Qian Shi et al.  |  ODbL / CC BY 4.0',font=ImageFont.truetype(str(latin),12),fill=(213,221,226,255))
        im.save(ROOT/'previews'/(name+'-overlay.png'))
if __name__=='__main__':main()
