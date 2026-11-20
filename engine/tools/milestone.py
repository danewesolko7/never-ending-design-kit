#!/usr/bin/env python3
"""Canvas frame for a visual gate, built only from files that already exist. One canvas per project, one frame per
visual gate, updated in place.

    milestone.py <gate>        G3a | G3b/G4a | G4b | G6 | G7 | G8
    G3a frames every concept rough (out/rough/png/<concept>-1440-m.png); G3b/G4a every direction board
    (out/boards/png/<direction>/<key>-1440-m.png).

Reads out/packet.md, the gate checklist and the renders (rough or shots; run shot.js first).
Writes out/canvas/index.html, out/canvas/<gate>.html and the 1000px images beside them, then prints what to publish
(adapters/<host>.md says how): publish by file path, never by pasting HTML. Fails when a render is missing.
"""
import glob, html, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, current_project, die, event, now, read_json, write_atomic

CSS = """body{margin:0;font:16px/1.5 system-ui,sans-serif;color:#1b1c1a;background:#f4f4f1}
.f-wrap{max-width:1120px;margin:0 auto;padding:40px 20px 64px;display:grid;gap:28px}
.f-meta{font-size:13px;color:#55574f;letter-spacing:.04em;text-transform:uppercase}
.f-title{font-size:32px;line-height:1.15;margin:4px 0 0}
.f-packet{background:#1b1c1a;color:#f4f4f1;padding:18px 22px;white-space:pre-wrap;font:14px/1.6 ui-monospace,monospace;margin:0}
.f-row{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
.f-fig{margin:0}.f-fig img{display:block;max-width:100%;height:auto;outline:1px solid #c9cac4}
.f-cap{font-size:13px;color:#55574f;margin-top:6px}
.f-list{margin:0;padding-left:20px}
.f-nav{display:flex;flex-wrap:wrap;gap:8px 20px}.f-nav a{display:inline-flex;align-items:center;min-height:44px;color:#1b1c1a}
@media (prefers-color-scheme:dark){body{background:#151614;color:#ecece8}.f-packet{background:#ecece8;color:#151614}.f-meta,.f-cap{color:#a8aaa2}.f-nav a{color:#ecece8}}
"""


def renders(g, key, brief):
    if g == 'G3a':
        fs = sorted(glob.glob(P('out', 'rough', 'png', '*-1440-m.png')))
        if not fs:
            die('milestone: no concept roughs: run greek.py structure-<n>.json --name c<n> for each concept')
        return [x for f in fs for x in ((f, f'Concept {os.path.basename(f).split("-1440")[0]}, 1440'),
                                       (f.replace('-1440-m.png', '-390-m.png'), f'Concept {os.path.basename(f).split("-1440")[0]}, 390'))]
    if g == 'G3b/G4a':
        fs = sorted(glob.glob(P('out', 'boards', 'png', '*', f'{key}-1440-m.png')))
        if not fs:
            die('milestone: no direction boards: build.py <key> --board d<n> --tokens tokens-d<n>.json, then shot.js each')
        return [x for f in fs for x in ((f, f'Direction {os.path.basename(os.path.dirname(f))}, 1440'),
                                       (f.replace('-1440-m.png', '-390-m.png'), f'Direction {os.path.basename(os.path.dirname(f))}, 390'))]
    if g in ('G4b', 'G6'):
        return [(P('out', 'shots', f'{key}-1440-m.png'), f'{key} at 1440 (first screen)'), (P('out', 'shots', f'{key}-390-m.png'), f'{key} at 390')]
    if g == 'G7':
        return [(P('out', 'shots', 'specimen-1440-m.png'), 'Specimen, 1440'), (P('out', 'shots', 'specimen-390-m.png'), 'Specimen, 390')]
    if g == 'G8':
        st = read_json(P('state.json'), {})
        pages = [x for x in (st.get('batch') or []) if x]
        if not pages:
            die('milestone: state.json has no "batch" list (the production designer records the batch page ids)')
        return [(P('out', 'shots', f'{p}-{w}-m.png'), f'{p} at {w}') for p in pages for w in (1440, 390)]
    die(f'milestone: {g} is not a visual gate')


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    proj = current_project(); event('call')
    g = a[0]
    brief = read_json(P('brief.json'), {})
    key = brief.get('key_page') or 'home'
    items = renders(g, key, brief)
    miss = [os.path.relpath(f, P()) for f, _ in items if not os.path.exists(f)]
    if miss:
        die('milestone: render missing: ' + ', '.join(miss) + ' (run shot.js or greek.py first)')
    cdir = P('out', 'canvas')
    slug = g.replace('/', '-')
    os.makedirs(cdir, exist_ok=True)
    figs = []
    for i, (f, cap) in enumerate(items):
        fn = f'{slug}-{i + 1}.png'
        shutil.copy(f, os.path.join(cdir, fn))
        figs.append(f'<figure class="f-fig"><img src="{fn}" alt="{html.escape(cap)}"><figcaption class="f-cap">{html.escape(cap)}</figcaption></figure>')
    packet = open(P('out', 'packet.md'), encoding='utf-8').read() if os.path.exists(P('out', 'packet.md')) else 'no packet yet: run gate.py --ready'
    cl = (sorted(glob.glob(P('out', f'checklist-{slug}.md'))) or [None])[-1]
    cli = ''.join(f'<li>{html.escape(l)}</li>' for l in open(cl, encoding='utf-8').read().splitlines()[1:]) if cl else '<li>run gate.py --checklist</li>'
    frame = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
             f'<title>{html.escape(proj)} · {g}</title><style>{CSS}</style></head><body><main class="f-wrap">'
             f'<p class="f-nav"><a href="index.html">All gates</a></p>'
             f'<div><p class="f-meta">{html.escape(proj)} · {g} · {now()[:10]}</p><h1 class="f-title">{html.escape(g)}: decide</h1></div>'
             f'<pre class="f-packet">{html.escape(packet)}</pre><div class="f-row">{"".join(figs)}</div>'
             f'<section><h2>Gate checklist</h2><ol class="f-list">{cli}</ol></section></main></body></html>')
    write_atomic(os.path.join(cdir, f'{slug}.html'), frame)
    frames = sorted(os.path.basename(f) for f in glob.glob(os.path.join(cdir, 'G*.html')))
    idx = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>{html.escape(proj)}: gates</title><style>{CSS}</style></head><body><main class="f-wrap"><h1 class="f-title">{html.escape(proj)}: visual gates</h1>'
           '<nav class="f-nav" aria-label="Gates">' + ''.join(f'<a href="{f}">{f[:-5].replace("-", "/", 1) if f.startswith("G3b") else f[:-5]}</a>' for f in frames)
           + '</nav></main></body></html>')
    write_atomic(os.path.join(cdir, 'index.html'), idx)
    files = ['index.html', f'{slug}.html'] + sorted(os.path.basename(f) for f in glob.glob(os.path.join(cdir, f'{slug}-*.png')))
    canvas = read_json(P('canvas.json'), {})
    link = canvas.get('link') or canvas.get('slug')
    print(f'milestone {g}: frame with {len(figs)} image(s) -> out/canvas/{slug}.html')
    print(f'publish: page {os.path.join(cdir, "index.html")} with files {", ".join(files[1:])} from {cdir}'
          + (f'; update the existing canvas {link}' if link else f'; a new canvas titled "{proj}: gates"') + ' (how: adapters/<host>.md)')
    if not link:
        print('Then record its link in canvas.json as {"link": "..."}.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
