#!/usr/bin/env python3
"""One labelled contact sheet from a set of PNGs, 1000px or less on its long side (the only size a model views).

    contact.py <out.png> <png or glob> [more ...] [--w 200] [--hmax 1500] [--cols N]
"""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import event
from PIL import Image, ImageDraw, ImageFont
MAX = 1000


def main(a):
    if len(a) < 2 or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    opts = {'--w': 200, '--hmax': 1500, '--cols': 0}
    files, i, out = [], 1, a[0]
    while i < len(a):
        if a[i] in opts:
            opts[a[i]] = int(a[i + 1]); i += 2; continue
        files += sorted(glob.glob(a[i])) or ([a[i]] if os.path.exists(a[i]) else []); i += 1
    files = [f for f in dict.fromkeys(files) if f.lower().endswith('.png') and os.path.abspath(f) != os.path.abspath(out)]
    if not files:
        print('contact: no PNGs matched'); return 0
    W, HM, gap, lab = opts['--w'], opts['--hmax'], 12, 22
    tiles = []
    for f in files:
        im = Image.open(f).convert('RGB')
        h = round(im.height * W / im.width)
        im = im.resize((W, h), Image.LANCZOS)
        tiles.append((os.path.splitext(os.path.basename(f))[0], im.crop((0, 0, W, min(h, HM)))))
    cols = opts['--cols'] or max(1, min(len(tiles), (1560 - gap) // (W + gap)))
    rows = [tiles[k:k + cols] for k in range(0, len(tiles), cols)]
    rh = [max(t[1].height for t in r) + lab for r in rows]
    SW, SH = gap + cols * (W + gap), gap + sum(h + gap for h in rh)
    sheet = Image.new('RGB', (SW, SH), (136, 136, 136)); d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 14)
    except OSError:
        font = ImageFont.load_default()
    y = gap
    for r, h in zip(rows, rh):
        x = gap
        for name, im in r:
            sheet.paste(im, (x, y)); d.text((x, y + im.height + 4), name[:28], fill=(255, 255, 255), font=font); x += W + gap
        y += h + gap
    s = min(1.0, MAX / max(SW, SH))
    if s < 1:
        sheet = sheet.resize((round(SW * s), round(SH * s)), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, optimize=True)
    event('render')
    print(f'contact: {out} {sheet.width}x{sheet.height}, {len(tiles)} tiles, about {sheet.width * sheet.height // 750} image tokens')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
