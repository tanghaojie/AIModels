"""Evidence contact sheets, using actual Blender outputs without image generation."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'previews'
def sheet(files,name,cols=3,w=480,h=330):
    rows=(len(files)+cols-1)//cols;im=Image.new('RGB',(w*cols,(h+28)*rows),(19,26,34));draw=ImageDraw.Draw(im)
    for idx,file in enumerate(files):
        with Image.open(P/file) as frame:
            frame=frame.convert('RGB');frame.thumbnail((w,h));x=(idx%cols)*w+(w-frame.width)//2;y=(idx//cols)*(h+28);im.paste(frame,(x,y));draw.text(((idx%cols)*w+10,y+h+7),file,fill=(223,227,231))
    im.save(P/name)
def main():
    sheet([f'assembly-{f:03d}.png' for f in [0,120,225,450,600,660,735,810,900]],'assembly-contact.jpg')
    sheet([f'explode-{f:03d}.png' for f in [0,90,180,270,360]],'explode-contact.jpg')
    sheet([x+'.png' for x in ['day','sunset','blue','night']],'day-night-contact.jpg',cols=2,w=640,h=440)
if __name__=='__main__':main()
