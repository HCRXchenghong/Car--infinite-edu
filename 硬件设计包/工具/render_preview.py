"""Render PDF page contact sheets for human layout review (requires pdftoppm)."""
from pathlib import Path
import argparse
import subprocess
import tempfile
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='car-hw-review-'))
parser=argparse.ArgumentParser()
parser.add_argument('--pdf',default=str(ROOT/'打印版/四轮四转底盘_硬件实施与检验手册_HW-R1.pdf'))
options=parser.parse_args()
pdf=Path(options.pdf)
subprocess.run(['pdftoppm','-png','-scale-to','1100',str(pdf),str(out/'page')],check=True,capture_output=True)
pages=sorted(out.glob('page-*.png'))
for begin in range(0,len(pages),16):
    canvas=Image.new('RGB',(1200,4*448),'#cbd5da')
    draw=ImageDraw.Draw(canvas)
    for j,path in enumerate(pages[begin:begin+16]):
        im=Image.open(path); im.thumbnail((286,408))
        x=(j%4)*300+7; y=(j//4)*448+28
        canvas.paste(im,(x,y)); draw.text((x,y-20),f'PAGE {begin+j+1:02d}',fill='black')
    dest=out/f'contact-{begin+1:02d}.png'; canvas.save(dest); print(dest)
print('Individual page directory:',out)
