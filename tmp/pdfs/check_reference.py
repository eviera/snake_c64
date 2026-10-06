from pypdf import PdfReader
from PIL import Image, ImageDraw
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
r = PdfReader(root / 'opcodes_C64.pdf')
print('Pages:', len(r.pages), 'Bookmarks:', len(r.outline))
files = sorted((root / 'tmp/pdfs').glob('page-*.png'))
assert len(files) == len(r.pages) == 18
text = '\n'.join(p.extract_text() for p in r.pages)
assert '\ufffd' not in text
assert all(x in text for x in ['.watch', '.dw', 'CHROUT', 'GETIN', 'sbc', '#importonce'])
manual = PdfReader(root / 'KickAssembler.pdf')
source = '\n'.join(p.extract_text() for p in manual.pages)
names = set(re.findall(r'(?m)^\s*(\.[a-zA-Z]+)\b', source))
assert all(name in text for name in names), names-set(text.split())
print('Verified all', len(names), 'directive names found at line starts in the local manual.')
for i,p in enumerate(r.pages):
    print(i+1, len(p.extract_text()), 'characters')
for start in range(0,len(files),6):
    sheet=Image.new('RGB',(1200,1740),'#cbd5df')
    for j,f in enumerate(files[start:start+6]):
        im=Image.open(f)
        im.thumbnail((390,550))
        x=(j%2)*600+100
        y=(j//2)*580+22
        sheet.paste(im,(x,y))
        ImageDraw.Draw(sheet).text((x,y-16),f.stem,fill='black')
    sheet.save(root / f'tmp/pdfs/contact-{start//6+1}.png')
