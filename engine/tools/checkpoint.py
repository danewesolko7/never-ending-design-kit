#!/usr/bin/env python3
"""Packaging (stage 9): runs on the last G8 approval. No gate; the creative director can still reopen any page.

    checkpoint.py [--ship-open]

1. Blocker check: a [NEW] figure, a placeholder image, a missing image or font licence, an unresolved fact flag
   ([CONFLICT] or UNRESOLVED in research.md), a missing rationale.md, or a failed pass.py --package.
   Client open items are listed; packaging waits until the CD reruns with --ship-open or resolves them.
2. Pack the project (out/store/<project>.py), write the final fingerprint to the studio registry, append the usage
   roll-up to studio/registry/usage-log.jsonl, and add each reference the build used to studio/library.md
   (refs.py --promote). Each step runs once, so a rerun after a reopen adds nothing twice. No image is kept.
3. Export out/package/: every page at 1440 and 390 (key page also 768), the brand sheet, licences, accessibility
   notes, the rationale, and an index page. The Design System artifact is published at G7, not here.
A build never changes the engine: the kit stays a clean starting point for the next project.
"""
import glob, html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import (J, P, ST, append_jsonl, current_project, die, event, node_env, now, read_json, read_jsonl,
                    words, write_atomic, write_json)


def run(args):
    return subprocess.run(args, capture_output=True, text=True, env={**node_env(), 'KIT_PROJECT': current_project()}, cwd=J())


def lum(h):
    h = h.lstrip('#'); h = ''.join(c * 2 for c in h) if len(h) == 3 else h
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def blockers(o):
    for f in sorted(glob.glob(P('pages', '*.json'))):
        if re.search(r'\[NEW[\]:]', open(f, encoding='utf-8').read()):
            o.append(f'[NEW] figure in pages/{os.path.basename(f)}')
    ib = read_json(P('image-brief.json'), [])
    for r in ib if isinstance(ib, list) else []:
        if r.get('status') != 'sourced':
            o.append(f'image slot {r.get("slot")} is still a placeholder')
        if not str(r.get('licence', '')).strip():
            o.append(f'image slot {r.get("slot")} has no licence')
    r = run([sys.executable, 'tools/fontcheck.py'])
    if r.returncode:
        o.append('font check failed: ' + r.stdout.strip().splitlines()[-1])
    if os.path.exists(P('research.md')):
        t = open(P('research.md'), encoding='utf-8').read()
        n = len(re.findall(r'\[CONFLICT\]|UNRESOLVED', t))
        if n:
            o.append(f'{n} unresolved fact flag(s) in research.md')
    if not os.path.exists(P('rationale.md')):
        o.append('rationale.md missing (250 words or fewer: problem, insight, structure, direction, what was rejected)')
    elif words(open(P('rationale.md'), encoding='utf-8').read()) > 250:
        o.append('rationale.md is over 250 words')
    r = run([sys.executable, 'tools/pass.py', '--package'])
    if r.returncode:
        o.append('pass.py --package failed: ' + r.stdout.strip().splitlines()[-1])


def final_fingerprint(proj, brief):
    fp = read_json(P('fingerprints', 'chosen.json')) or {}
    tok, stc = read_json(P('tokens.json'), {}), read_json(P('structure.json'), {})
    # the art director's chosen type pair and dominant colours stand; tokens only fill what the card left blank
    faces = [f['family'] for f in (tok.get('type') or {}).get('faces', [])]
    if faces and not str(fp.get('type_pair', '')).strip():
        fp['type_pair'] = ' / '.join(faces[:2])
    col = tok.get('color') or {}
    pick = [col[k] for k in ('accent', 'strong', 'ground', 'paper', 'ink') if k in col][:2] or list(col.values())[:2]
    if pick and len([h for h in fp.get('hues', []) if re.fullmatch(r'#?[0-9a-fA-F]{3,6}', str(h))]) < 2:
        fp['hues'] = pick
    if stc.get('page_form'):
        fp['form'] = ' '.join(stc['page_form'].split()[:4])
    g = stc.get('grid') or {}
    if g.get('columns') and not fp.get('grid'):
        fp['grid'] = f'{g["columns"]}-col' + (' nested' if g.get('nested') else '')
    fp.update({'project': proj, 'scope': 'project', 'confirmed': True, 'time': now()})
    return fp


def rollup(proj):
    rows = read_jsonl(P('usage.jsonl'))
    log = ST('registry', 'usage-log.jsonl')
    # a rerun after a reopen adds only records not yet rolled up
    seen = {(r.get('project'), r.get('type'), r.get('rid') or r.get('gate'), r.get('time') or r.get('end')) for r in read_jsonl(log)}
    split = {}
    for r in rows:
        if r.get('type') == 'credits_split':
            split[r['rid']] = split.get(r['rid'], 0) + r['credits']
    for r in rows:
        rec = {**r, 'type': 'stage', 'credits': split.get(r['rid'])} if r.get('type') == 'close' else \
              {**r, 'project': proj} if r.get('type') == 'outcome' else None
        if rec and (rec.get('project'), rec['type'], rec.get('rid') or rec.get('gate'), rec.get('time') or rec.get('end')) not in seen:
            append_jsonl(log, rec)


def export(proj, brief):
    pk = P('out', 'package'); os.makedirs(pk, exist_ok=True)
    key = brief.get('key_page') or 'home'
    pages = [os.path.basename(f)[:-5] for f in sorted(glob.glob(P('out', 'site', '*.html'))) if not f.endswith('specimen.html')]
    for p in pages:
        w = '1440,768,390' if p == key else '1440,390'
        run(['node', 'tools/shot.js', P('out', 'site', f'{p}.html'), '--widths', w, '--out', os.path.join(pk, 'pages')])
    event('render', len(pages) * 2 + 1)
    run([sys.executable, 'tools/contact.py', os.path.join(pk, 'contact-1440.png'), os.path.join(pk, 'pages', '*-1440.png')])
    run([sys.executable, 'tools/contact.py', os.path.join(pk, 'contact-390.png'), os.path.join(pk, 'pages', '*-390.png'), '--w', '120'])
    tok = read_json(P('tokens.json'), {})
    col = tok.get('color') or {}
    ground = col.get('paper') or col.get('ground') or '#ffffff'
    ink = col.get('ink') or '#000000'
    rows = ''.join(f'<tr><td>{html.escape(k)}</td><td>{v}</td><td><span class="b-chip b-c{i}"></span></td><td>{ratio(v, ground):.1f}:1</td><td>{ratio(v, ink):.1f}:1</td></tr>'
                   for i, (k, v) in enumerate(col.items()))
    chips = ''.join(f'.b-c{i}{{background:{v}}}' for i, v in enumerate(col.values()))
    faces = ''.join(f'<li>{html.escape(f["family"])}: {html.escape(f.get("source", ""))}, licence {html.escape(f.get("licence", ""))}</li>'
                    for f in (tok.get('type') or {}).get('faces', []))
    write_atomic(os.path.join(pk, 'brand-sheet.html'),
                 f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(proj)}: brand sheet</title><style>'
                 f'body{{font:16px/1.5 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px}}table{{border-collapse:collapse;width:100%}}'
                 f'td,th{{text-align:left;padding:8px;border-bottom:1px solid #ccc}}.b-chip{{display:inline-block;width:48px;height:24px;outline:1px solid #999}}{chips}</style></head>'
                 f'<body><h1>{html.escape(brief.get("site_name") or proj)}: brand sheet</h1><h2>Palette roles and contrast</h2><table><tr><th>Role</th><th>Value</th>'
                 f'<th>Swatch</th><th>On ground</th><th>On ink</th></tr>{rows}</table><h2>Typefaces</h2><ul>{faces}</ul>'
                 f'<h2>Wordmark and clear space</h2><p>See partials/header.html and the Design System artifact.</p></body></html>')
    ib = read_json(P('image-brief.json'), [])
    lic = ['# Licences', '', '## Images', ''] + [f'- {r.get("slot")}: {r.get("subject")} | {r.get("source")} | {r.get("licence")} | treatment: {r.get("treatment")}'
                                                 for r in (ib if isinstance(ib, list) else [])]
    lic += ['', '## Fonts', ''] + [f'- {f["family"]}: {f.get("source")} | {f.get("licence")}' for f in (tok.get('type') or {}).get('faces', [])]
    write_atomic(os.path.join(pk, 'licences.md'), '\n'.join(lic) + '\n')
    acc = ['# Accessibility notes', '', 'Target: WCAG 2.2 AAA where achievable, AA floor. Automated: axe-core at 1440 and 390 (pass.py --package).', '']
    for p in pages:
        t = open(P('out', 'site', f'{p}.html'), encoding='utf-8').read()
        hs = [f'{m.group(1)} {re.sub("<[^>]+>", "", m.group(2)).strip()[:60]}' for m in re.finditer(r'<(h[1-4])[^>]*>(.*?)</h[1-4]>', t, re.S)]
        alts = re.findall(r'<img[^>]+alt="([^"]*)"', t)
        acc += [f'## {p}', '- Heading order: ' + ' > '.join(hs), '- Alt text: ' + ('; '.join(alts) if alts else 'no images'), '']
    acc += ['## Still to test', '- Screen readers (VoiceOver, NVDA) on every page', '- Safari, Firefox, Edge, iOS Safari, Android Chrome (only Chromium is automated)',
            '- Keyboard focus order with real users', '']
    write_atomic(os.path.join(pk, 'accessibility.md'), '\n'.join(acc))
    if os.path.exists(P('rationale.md')):
        write_atomic(os.path.join(pk, 'rationale.md'), open(P('rationale.md'), encoding='utf-8').read())
    imgs = sorted(os.path.relpath(f, pk) for f in glob.glob(os.path.join(pk, 'pages', '*.png')) if not f.endswith('-m.png'))
    write_atomic(os.path.join(pk, 'index.html'),
                 f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(proj)}: final package</title>'
                 '<style>body{font:16px/1.5 system-ui,sans-serif;margin:0;padding:32px 20px;background:#f4f4f1}main{max-width:1200px;margin:0 auto}'
                 '.p-row{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start}.p-fig{margin:0;max-width:100%}.p-fig img{display:block;max-width:100%;height:auto;outline:1px solid #ccc}'
                 'a{display:inline-flex;min-height:44px;align-items:center}</style></head><body><main>'
                 f'<h1>{html.escape(brief.get("site_name") or proj)}: final package</h1>'
                 '<p><a href="brand-sheet.html">Brand sheet</a> · <a href="licences.md">Licences</a> · <a href="accessibility.md">Accessibility notes</a> · <a href="rationale.md">Rationale</a></p>'
                 '<div class="p-row">' + ''.join(f'<figure class="p-fig"><img src="{i}" alt="{html.escape(os.path.basename(i)[:-4])}" loading="lazy"><figcaption>{html.escape(os.path.basename(i)[:-4])}</figcaption></figure>' for i in imgs)
                 + '</div></main></body></html>')
    return pk, len(pages)


def main(a):
    if a and a[0] in ('-h', '--help'):
        print(__doc__); return 0
    proj = current_project(); event('call')
    brief = read_json(P('brief.json'), {})
    b = []
    blockers(b)
    if b:
        for x in b[:15]:
            print('BLOCKED ' + x)
        print(f'checkpoint: {len(b)} blocker(s); packaging stopped. Fix them, then rerun tools/checkpoint.py.')
        return 1
    st = read_json(P('state.json'), {})
    client = [o for o in st.get('open', []) if re.search(r'\|\s*client\b', o, re.I)]
    if client and '--ship-open' not in a:
        for c in client[:12]:
            print('CLIENT ' + c)
        print('checkpoint: client items are open. The CD decides: resolve them, or rerun with --ship-open to ship with them listed.')
        return 1
    os.makedirs(P('out', 'store'), exist_ok=True)
    r = run([sys.executable, 'tools/pack.py', proj, P('out', 'store', f'{proj}.py')])
    print(r.stdout.strip())
    fp = final_fingerprint(proj, brief)
    append_jsonl(ST('registry', 'fingerprints.jsonl'), fp)   # append-only: the latest line per project wins
    rollup(proj)
    print(run([sys.executable, 'tools/refs.py', '--promote']).stdout.strip().splitlines()[-1])
    pk, n = export(proj, brief)
    st.update({'status': 'packaged', 'stage': '9', 'packaged': now()})
    write_json(P('state.json'), st)
    append_jsonl(P('audit.jsonl'), {'time': now(), 'person': 'kit', 'gate': 'G8', 'action': 'package', 'detail': f'{n} pages' + (' shipped with client items open' if client else '')})
    print(f'checkpoint: packaged {n} page(s) -> {os.path.relpath(pk, P())}; fingerprint added to the studio registry; usage rolled up.')
    print(f'Save the project pack {os.path.relpath(P("out", "store", proj + ".py"), P())} and publish out/package/ (how: adapters/<host>.md).')
    print('Learn: references marked used are now in studio/library.md; add any other reusable technique the build used there'
          ' (right section, no client facts or project names). Never edit the engine at packaging: kit changes go through G10.')
    if client:
        print('Shipped with client items open: ' + '; '.join(client[:4]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
