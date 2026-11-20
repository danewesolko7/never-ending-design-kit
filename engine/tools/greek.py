#!/usr/bin/env python3
"""Greeked rough from structure.json: the grid, grey image blocks, and text set in a greeking face at true copy length.

    greek.py [structure.json] [--key <page id>] [--name <concept>] [--no-shot]
    One rough per concept: greek.py structure-1.json --name c1 (writes out/rough/c1.html).

Reads projects/<p>/structure.json (and content.json for word counts), writes out/rough/<key>.html, then renders it
through shot.js at 1440, 390 and 320 (out/rough/png/). Measure it with pass.py --rough. Fails on a schema error.

structure.json:
{"page_form": "...", "grid": {"columns": 12, "gutter": 24, "margin": 80, "nested": []},
 "sections": [{"id": "s1", "order": 1, "rhythm": "loud|normal|rest", "span": [1, 12], "ground": "none|tint|dark",
               "block": [{"t": "h1|h2|h3|kicker|lede|body|caption|link|list|img|fig|num|rule",
                          "start": 1, "span": 7, "words": 9, "size": 88, "h": 560, "bleed": "none|left|right|both",
                          "phone": [1, 4]}]}],
 "breakpoints": [390, 768, 1440]}
"block" may also be a shorthand string such as "h2+body+img". Missing word counts come from content.json
(the key page's section with the same id). No colour, no typeface choice, no style: structure only.
"""
import html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, current_project, die, event, node_env, read_json, write_atomic

TEXT = {'h1': 88, 'h2': 48, 'h3': 28, 'kicker': 14, 'lede': 24, 'body': 19, 'caption': 14, 'link': 18, 'list': 18}
PAD = {'loud': 96, 'normal': 112, 'rest': 176}
TYPES = set(TEXT) | {'img', 'fig', 'num', 'rule'}


def expand(block):
    if isinstance(block, str):
        return [{'t': t.strip()} for t in block.split('+') if t.strip()]
    return block or []


def main(a):
    if a and a[0] in ('-h', '--help'):
        print(__doc__); return 0
    current_project()
    event('call')
    src = next((x for x in a if x.endswith('.json')), P('structure.json'))
    s = read_json(src if os.path.isabs(src) else (P(src) if os.path.exists(P(src)) else src))
    if s is None:
        die(f'greek: {src} not found')
    content = read_json(P('content.json'), {})
    brief = read_json(P('brief.json'), {})
    key = a[a.index('--key') + 1] if '--key' in a else (brief.get('key_page') or 'home')
    pg = next((p for p in content.get('pages', []) if p.get('id') == key), {'sections': []})
    words = {x['id']: x.get('words', 40) for x in pg.get('sections', [])}
    g = s.get('grid') or {}
    cols, gut, mar = int(g.get('columns', 12)), int(g.get('gutter', 24)), int(g.get('margin', 80))
    errs, css, body = [], [], []
    secs = sorted(s.get('sections', []), key=lambda x: x.get('order', 0))
    if not secs:
        errs.append('structure.json has no sections')
    for sec in secs:
        sid = sec.get('id') or 'x'
        blocks = expand(sec.get('block'))
        if not blocks:
            errs.append(f'section {sid}: no block')
        base = sec.get('span') or [1, cols]
        text_blocks = [b for b in blocks if b.get('t') in TEXT]
        budget = words.get(sid)
        items = []
        for i, b in enumerate(blocks):
            t = b.get('t')
            if t not in TYPES:
                errs.append(f'section {sid}: unknown block type "{t}"'); continue
            st, sp = int(b.get('start', base[0])), int(b.get('span', base[1] if len(base) > 1 else cols))
            if st < 1 or st + sp - 1 > cols:
                errs.append(f'section {sid}: block {i + 1} runs outside {cols} columns ({st}+{sp})')
            ph = b.get('phone') or [1, 4]
            cls = f'gk-b{len(css)}'
            bleed = b.get('bleed', 'none')
            ml = f'margin-left:calc(-1 * var(--m))' if bleed in ('left', 'both') and st == 1 else ''
            mr = f'margin-right:calc(-1 * var(--m))' if bleed in ('right', 'both') and st + sp - 1 == cols else ''
            css.append(f'.{cls}{{grid-column:{st}/span {sp};{ml};{mr}}}'
                       f'@media (max-width:700px){{.{cls}{{grid-column:{ph[0]}/span {ph[1]};margin-left:0;margin-right:0}}}}')
            if t in TEXT:
                size = int(b.get('size', TEXT[t]))
                n = b.get('words')
                if n is None:
                    n = 8 if t in ('h1', 'h2') else 5 if t in ('h3', 'kicker', 'link') else 18 if t == 'caption' else \
                        max(10, (budget or 60) - 12) // max(1, len([x for x in text_blocks if x.get('t') in ('body', 'lede', 'list')]))
                css.append(f'.{cls}.gk-t,.{cls} .gk-t{{font-size:{size}px;font-size:clamp({max(12, size * 0.45):.0f}px,{size / 14.4:.2f}vw,{size}px)}}')
                txt = ' '.join('xxxxx'[: 2 + (k * 7) % 5] for k in range(int(n)))
                if t == 'list':
                    lis = ''.join(f'<li class="gk-t">{" ".join("xxxx"[: 2 + (k * 3) % 3] for k in range(int(b.get("words", 3))))}</li>'
                                  for _ in range(int(b.get('items', 4))))
                    items.append(f'<ul class="gk-l {cls}">{lis}</ul>')
                else:
                    tag = 'p'
                    items.append(f'<{tag} class="gk-t gk-{t} {cls}">{txt}</{tag}>')
            elif t in ('img', 'fig'):
                h = int(b.get('h', 400))
                w = sp * ((1440 - 2 * mar - (cols - 1) * gut) / cols) + (sp - 1) * gut
                css.append(f'.{cls}{{aspect-ratio:{w:.0f}/{h}}}')
                note = html.escape(b.get('note', ''))
                items.append(f'<div class="gk-i gk-{t} {cls}" role="img" aria-label="{t} {note}">{("<span>" + note + "</span>") if note else ""}</div>')
            elif t == 'num':
                css.append(f'.{cls}{{font-size:clamp(64px,{int(b.get("size", 200)) / 14.4:.2f}vw,{int(b.get("size", 200))}px)}}')
                items.append(f'<p class="gk-t gk-num {cls}">{"0" * int(b.get("chars", 4))}</p>')
            elif t == 'rule':
                items.append(f'<hr class="gk-rule {cls}">')
        pad = PAD.get(sec.get('rhythm', 'normal'), 112)
        ground = sec.get('ground', 'none')
        body.append(f'<section class="gk-sec gk-{ground}" id="{html.escape(sid)}" style="--pad:{pad}px"><span class="gk-name">{html.escape(sid)} · {html.escape(sec.get("rhythm", "normal"))}</span>'
                    + ''.join(items) + '</section>')
    if errs:
        for e in errs[:15]:
            print('schema error: ' + e)
        return 1
    font = ''
    for base in [os.path.expanduser('~/.cache/design-kit')]:
        for r, _, fs in os.walk(base):
            for f in fs:
                if f.startswith('flow-block-latin-400-normal.woff2'):
                    font = os.path.join(r, f)
    ff = f"@font-face{{font-family:'Flow Block';src:url(file://{font}) format('woff2')}}" if font else ''
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rough: {html.escape(s.get('page_form', key))}</title><style>{ff}
:root{{--m:{mar}px;--g:{gut}px;--n:{cols}}}
body{{margin:0;background:#fff;color:#8a8a8a;font-family:'Flow Block',monospace}}
.gk-sec{{position:relative;display:grid;grid-template-columns:repeat({cols},minmax(0,1fr));column-gap:{gut}px;row-gap:24px;align-items:start;
  padding:var(--pad) var(--m)}}
.gk-sec::before{{content:'';position:absolute;top:0;bottom:0;left:var(--m);right:var(--m);pointer-events:none;background-image:linear-gradient(90deg,rgba(120,170,220,.14) calc(100% - var(--g)),transparent 0);background-size:calc((100% + var(--g))/var(--n)) 100%}}
.gk-sec>:not(.gk-name){{position:relative}}
.gk-tint{{background-color:#ececec}} .gk-dark{{background-color:#3a3a3a;color:#d0d0d0}}
.gk-name{{position:absolute;top:6px;right:8px;font:11px sans-serif;color:#7fb0e0}}
.gk-t{{margin:0;line-height:1.35;word-break:break-word}} .gk-h1,.gk-h2,.gk-h3,.gk-num{{line-height:1.05;color:#555}} .gk-dark .gk-h1,.gk-dark .gk-h2{{color:#eee}}
.gk-l{{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:8px}}
.gk-i{{background:linear-gradient(to top right,transparent calc(50% - 1px),#a5a5a5,transparent calc(50% + 1px)),linear-gradient(to top left,transparent calc(50% - 1px),#a5a5a5,transparent calc(50% + 1px)),#d6d6d6;outline:1px solid #a5a5a5;position:relative}}
.gk-fig{{background:none;outline:2px dashed #8a8a8a}} .gk-i span{{position:absolute;left:10px;top:8px;font:italic 13px sans-serif;color:#666}}
.gk-rule{{border:0;border-top:2px solid #555;width:100%;margin:0}}
@media (max-width:700px){{:root{{--m:20px;--g:16px;--n:4}} .gk-sec{{grid-template-columns:repeat(4,minmax(0,1fr));column-gap:16px;padding:calc(var(--pad)*.6) var(--m)}}}}
{''.join(css)}
</style></head><body>{''.join(body)}</body></html>"""
    name = a[a.index('--name') + 1] if '--name' in a else key
    out = P('out', 'rough', f'{name}.html')
    write_atomic(out, page)
    print(f'greek: {len(secs)} section(s) -> {os.path.relpath(out, P())}' + ('' if font else ' (greeking face not cached: run setup.sh)'))
    if '--no-shot' not in a:
        r = subprocess.run(['node', J('tools', 'shot.js'), out, '--widths', '1440,390,320', '--out', P('out', 'rough', 'png')],
                           capture_output=True, text=True, env=node_env())
        print((r.stdout + r.stderr).strip()[-300:])
        event('render', 3)
        if r.returncode:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
