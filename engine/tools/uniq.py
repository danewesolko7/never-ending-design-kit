#!/usr/bin/env python3
"""Uniqueness check of one fingerprint against every past project, before anyone sees the option.

    uniq.py <fingerprint.json> [--name <option>]      fails when, against any one past project, the option:
        - shares more than one signature move
        - repeats the type pair or the display face
        - matches both page form and grid
        - has its two dominant colours within ΔE 10 (CIEDE2000) of that project's two
    and, with or without history, against common tool defaults (ref/defaults.json): a default display face, an accent
    within ΔE 6 of a default accent, or a default signature move. Build one is checked even with an empty registry.
    uniq.py --pages                                   fails when two pages of this project share a signature
                                                      technique (page fingerprints in projects/<p>/fingerprints/)

A failing option is revised once: the design, not only the words in its fingerprint. If it still fails, the creative director may override at the
gate (gate.py --override uniq --target <option> --reason ".."); uniq.py then reports OVERRIDDEN and passes.
Writes out/uniq.json (out/uniq-pages.json for --pages). The current project is never compared with itself.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, ST, current_project, die, event, read_json, read_jsonl, write_json

S = read_json(J('settings.json'))
STOP = {'the', 'a', 'an', 'of', 'and', 'per', 'as', 'with', 'in', 'on', 'to', 'by'}
KEYS = ('form', 'grid', 'hero', 'nav', 'type_pair', 'type_class', 'hues', 'roles', 'image', 'texture', 'moves', 'motion')
OPTIONAL = ('movement',)   # read by seed.py; older fingerprints lack it


def toks(s):
    return {w[:-1] if w.endswith('s') and len(w) > 3 else w for w in re.findall(r'[a-z0-9]+', str(s).lower()) if w not in STOP}


def same(a, b, t=0.6):
    A, B = toks(a), toks(b)
    return bool(A and B) and len(A & B) / len(A | B) >= t


def faces(pair):
    return [re.sub(r'\s+', ' ', x).strip().lower() for x in re.split(r'[/+,]', pair or '') if x.strip()]


def hex2lab(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    x = (lin[0] * 0.4124 + lin[1] * 0.3576 + lin[2] * 0.1805) / 0.95047
    y = lin[0] * 0.2126 + lin[1] * 0.7152 + lin[2] * 0.0722
    z = (lin[0] * 0.0193 + lin[1] * 0.1192 + lin[2] * 0.9505) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return [116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))]


def de2000(h1, h2):
    import math
    L1, a1, b1 = hex2lab(h1); L2, a2, b2 = hex2lab(h2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p
    dh = 0 if C1p * C2p == 0 else (h2p - h1p if abs(h2p - h1p) <= 180 else h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360)
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lb, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hb = h1p + h2p if C1p * C2p == 0 else ((h1p + h2p) / 2 if abs(h1p - h2p) <= 180 else (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2)
    T = 1 - .17 * math.cos(math.radians(hb - 30)) + .24 * math.cos(math.radians(2 * hb)) + .32 * math.cos(math.radians(3 * hb + 6)) - .2 * math.cos(math.radians(4 * hb - 63))
    SL = 1 + .015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2)
    SC, SH = 1 + .045 * Cbp, 1 + .015 * Cbp * T
    RT = -2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-((hb - 275) / 25) ** 2)))
    return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))


def ishex(h):
    return bool(re.fullmatch(r'#?[0-9a-fA-F]{6}|#?[0-9a-fA-F]{3}', str(h or '')))


def check(fp, past):
    hits = []
    moves = [m for m in fp.get('moves', []) if m]
    for r in past:
        name = r.get('project', '?')
        shared = [m for m in moves if any(same(m, x) for x in r.get('moves', []))]
        if len(shared) > 1:
            hits.append(f'{name}: shares {len(shared)} signature moves ({"; ".join(shared[:3])})')
        fa, fb = faces(fp.get('type_pair')), faces(r.get('type_pair'))
        if fa and fb and (set(fa) == set(fb) or fa[0] == fb[0]):
            hits.append(f'{name}: repeats {"type pair" if set(fa) == set(fb) else "display face"} {fa[0].title()}')
        if fp.get('form') and fp.get('grid') and same(fp['form'], r.get('form'), .75) and same(fp['grid'], r.get('grid'), .75):
            hits.append(f'{name}: page form and grid both match ({fp["form"]}; {fp["grid"]})')
        ha, hb = [h for h in fp.get('hues', []) if ishex(h)], [h for h in r.get('hues', []) if ishex(h)]
        if len(ha) >= 2 and len(hb) >= 2:
            d = min(max(de2000(ha[0], hb[0]), de2000(ha[1], hb[1])), max(de2000(ha[0], hb[1]), de2000(ha[1], hb[0])))
            if d <= S['delta_e']:
                hits.append(f'{name}: two dominant colours within ΔE {d:.1f} of its pair')
    return hits


def defaults_check(fp):
    d = read_json(J('ref', 'defaults.json'), {})
    hits = []
    fa = faces(fp.get('type_pair'))
    if fa and fa[0] in {x.lower() for x in d.get('faces', [])}:
        hits.append(f'default: display face {fa[0].title()} is a common tool default')
    for h in [x for x in fp.get('hues', []) if ishex(x)]:
        near = [x for x in d.get('accents', []) if de2000(h, x) <= d.get('accent_delta_e', 6)]
        if near:
            hits.append(f'default: colour {h} is within ΔE {d.get("accent_delta_e", 6)} of the stock accent {near[0]}')
    for m in [x for x in fp.get('moves', []) if x]:
        hit = next((x for x in d.get('moves', []) if same(m, x)), None)
        if hit:
            hits.append(f'default: move "{m}" is the stock pattern "{hit}"')
    return hits


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    proj = current_project()
    event('call')
    ov = read_json(P('overrides.json'), {}).get('uniq', [])
    if a[0] == '--pages':
        fps = []
        for f in sorted(glob.glob(P('fingerprints', '*.json'))):
            d = read_json(f)
            if d and d.get('scope') == 'page':
                fps.append((os.path.basename(f)[:-5], d))
        hits = []
        for i, (n1, d1) in enumerate(fps):
            for n2, d2 in fps[i + 1:]:
                sh = [m for m in d1.get('moves', []) if any(same(m, x) for x in d2.get('moves', []))]
                if sh:
                    hits.append(f'pages {n1} and {n2} share "{sh[0]}"')
        res = {'pass': not hits, 'hits': hits, 'mode': 'pages'}
        write_json(P('out', 'uniq-pages.json'), res)
        for h in hits[:15]:
            print('FAIL ' + h)
        print(f'uniq --pages: {len(fps)} page fingerprint(s): ' + ('PASS' if not hits else f'FAIL ({len(hits)})'))
        return 0 if not hits else 1
    path = a[0] if os.path.isabs(a[0]) or os.path.exists(a[0]) else P(a[0])
    fp = read_json(path)
    if fp is None:
        die(f'uniq: {a[0]} not found')
    bad = [k for k in KEYS if k not in fp]
    long = [k for k in KEYS + OPTIONAL if k != 'type_pair' and isinstance(fp.get(k), str) and len(fp[k].split()) > 4]
    if bad or long:
        die('uniq: fingerprint ' + (f'missing keys: {", ".join(bad)} ' if bad else '') + (f'values over 4 words: {", ".join(long)}' if long else ''))
    name = a[a.index('--name') + 1] if '--name' in a else os.path.basename(path)[:-5]
    latest = {}
    for r in read_jsonl(ST('registry', 'fingerprints.jsonl')):
        if r.get('scope', 'project') == 'project':
            latest[r.get('project')] = r   # append-only log: the latest line per project wins
    past = [r for p, r in latest.items() if p != proj]
    hits = check(fp, past) + defaults_check(fp)
    over = [o for o in ov if o['target'] in (name, '*')] if hits else []
    res = {'pass': not hits or bool(over), 'hits': hits, 'name': name, 'overridden': bool(over and hits)}
    write_json(P('out', 'uniq.json'), res)
    for h in hits[:15]:
        print(('OVERRIDDEN ' if over else 'FAIL ') + h)
    if over:
        print(f'uniq {name}: OVERRIDDEN by the creative director: {over[-1]["reason"]}')
        return 0
    hist = f'{len(past)} past project(s) and tool defaults' if past else 'tool defaults only (no history yet)'
    print(f'uniq {name}: checked against {hist}: ' + ('PASS' if not hits else f'FAIL ({len(hits)}): revise the design once, not only its words'))
    return 0 if not hits else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
