#!/usr/bin/env python3
"""Build and measure: every check a script can make, in one command.

    pass.py --rough [<key>]           greeked rough: overflow, text-on-image, section crossings, height
    pass.py --page <id> | --all       build.py, then widths 1440/768/390/320, WCAG 2.2 AAA (axe), widows, overlaps,
                                      44px targets, meta and sharing, headings, code standard, page weight,
                                      copy x1.3 expansion, motion, reading level
    pass.py --system                  the specimen page, plus components against tokens, focus and reduced motion
    pass.py --package                 every page and the system together (checkpoint.py runs this)

Prints 20 lines or fewer; the full report is out/reports/pass-<mode>.md and out/pass.json. Exit 1 on any failure.
Warnings (never fail): page height over the artboard, stacked rules, figure styles.
Accessibility runs at WCAG 2.2 AAA unless brief.json says "wcag": "AA". A check the CD overrode
(gate.py --override pass --target <check> --reason "..") is reported as OVERRIDDEN and does not fail.
--all and --package also fail a page no visitor can reach from the key page (reach).
"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, Out, die, event, node_env, read_json, write_json, current_project

S = read_json(J('settings.json'))
WARN = {'height', 'rules', 'numerals'}


def probe(files, widths, mode):
    wcag = str((read_json(P('brief.json'), {}) or {}).get('wcag', 'AAA')).upper()
    cfg = {'files': [os.path.abspath(f) for f in files], 'widths': widths, 'mode': mode, 'wcag': wcag,
           'expansion': S['expansion'] if mode == 'page' else 0, 'artboard': S['artboard_px']}
    r = subprocess.run(['node', J('tools', 'probe.js'), json.dumps(cfg)], capture_output=True, text=True, env=node_env())
    try:
        d = json.loads(r.stdout)
    except ValueError:
        die('pass: probe failed: ' + (r.stderr or r.stdout)[-400:])
    if 'error' in d:
        die('pass: probe failed: ' + d['error'][:300])
    event('render', len(files) * len(widths))
    return d


def fk_grade(text):
    sents = max(1, len(re.findall(r'[.!?](\s|$)', text)))
    ws = re.findall(r"[A-Za-z]+", text)
    if not ws:
        return 0.0
    syl = sum(max(1, len(re.findall(r'[aeiouy]+', w.lower())) - (1 if w.lower().endswith('e') and len(w) > 3 else 0)) for w in ws)
    return 0.39 * len(ws) / sents + 11.8 * syl / len(ws) - 15.59


def page_texts(pid):
    pj = read_json(P('pages', f'{pid}.json'), {})
    out = []
    for s in pj.get('sections', []):
        for k, v in (s.get('text') or {}).items():
            out += v if isinstance(v, list) else [str(v)]
    return ' '.join(x.strip() if re.search(r'[.!?:]$', x.strip()) else x.strip() + '.' for x in out if x.strip())


def weight(html_path):
    site = os.path.dirname(html_path)
    t = open(html_path, encoding='utf-8').read()
    total = os.path.getsize(html_path)
    css = os.path.join(site, 'site.css')
    if os.path.exists(css):
        total += os.path.getsize(css)
        for f in re.findall(r'url\((?:\.\/)?(fonts/[^)\'"]+)\)', open(css, encoding='utf-8').read()):
            fp = os.path.join(site, f)
            total += os.path.getsize(fp) if os.path.exists(fp) else 0
    for src in re.findall(r'<img[^>]+src="([^"]+)"', t):
        fp = os.path.join(site, src)
        total += os.path.getsize(fp) if os.path.exists(fp) else 0
    return total


def css_checks(o):
    css = P('out', 'site', 'site.css')
    if not os.path.exists(css):
        o.add('system: out/site/site.css missing (run build.py)', True); return
    t = open(css, encoding='utf-8').read()
    body = re.sub(r':root\s*\{[^}]*\}', '', t)
    body = re.sub(r'@font-face\s*\{[^}]*\}', '', body)
    raw = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)', body)))
    if raw:
        o.add(f'system: {len(raw)} raw colour value(s) outside the tokens: {" ".join(raw[:5])}', True)
    if ':focus-visible' not in t:
        o.add('system: no :focus-visible rule', True)
    if re.search(r'animation|transition', body) and 'prefers-reduced-motion' not in t:
        o.add('system: motion without a prefers-reduced-motion fallback', True)
    tok = read_json(P('tokens.json'), {})
    for k in ('hover', 'focus', 'active', 'disabled', 'error'):
        if k not in (tok.get('states') or {}):
            o.add(f'system: tokens.json states has no "{k}"', True)
    if not (tok.get('motion') or {}).get('reduced'):
        o.add('system: tokens.json motion.reduced (the reduced-motion fallback) is empty', True)


def reach(o, site, key):
    """Every built page is reachable by links from the key page (header, footer, crumbs or body)."""
    pages = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(site, '*.html'))}
    start = key if key in pages else 'index' if 'index' in pages else None
    if not start:
        return 0
    seen, todo = {start}, [start]
    while todo:
        h = open(os.path.join(site, todo.pop() + '.html'), encoding='utf-8').read()
        for t in re.findall(r'href="(?:\./)?([a-z0-9_-]+)\.html(?:[#?][^"]*)?"', h):
            if t in pages and t not in seen:
                seen.add(t); todo.append(t)
    exempt = set(S.get('reach_exempt') or [])
    lost = sorted(pages - seen - exempt)
    for p in lost:
        o.add(f'FAIL reach: {p} has no link from {start} (add it to the nav, footer, a hub page or crumbs)', True)
    return len(lost)


def summarise(o, d, label):
    counts = {}
    for f in d['findings']:
        counts[f['check']] = counts.get(f['check'], 0) + 1
    by = {}
    for f in d['findings']:
        by.setdefault(f['check'], []).append(f)
    over = {x['target']: x['reason'] for x in read_json(P('overrides.json'), {}).get('pass', [])}
    for check, fs in sorted(by.items()):
        ex = fs[0]
        if check in over:
            o.add(f'OVERRIDDEN {check} x{len(fs)}: {ex["page"]}@{ex["width"]} (CD: {over[check][:60]})')
            continue
        o.add(f'{"warn" if check in WARN else "FAIL"} {check} x{len(fs)}: {ex["page"]}@{ex["width"]} {ex["detail"]}', check not in WARN)
    for f in d['findings']:   # the full list goes to the report only
        o.lines.append(f'  - {f["check"]} {f["page"]}@{f["width"]}: {f["detail"]}') if len(o.lines) < 400 else None
    return counts


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    current_project()
    event('call')
    mode = 'rough' if '--rough' in a else 'system' if '--system' in a else 'package' if '--package' in a else 'page'
    o = Out('pass', P('out', 'reports', f'pass-{mode}.md'))
    counts, extra = {}, {}
    if mode == 'rough':
        key = a[a.index('--rough') + 1] if len(a) > a.index('--rough') + 1 else None
        files = [P('out', 'rough', f'{key}.html')] if key else sorted(glob.glob(P('out', 'rough', '*.html')))
        files = [f for f in files if os.path.exists(f)]
        if not files:
            die('pass: no rough in out/rough/: run greek.py structure.json first')
        d = probe(files, [1440, 390, 320], 'rough')
        counts = summarise(o, d, 'rough')
        extra['heights'] = {k: v.get('height') for k, v in d['info'].items()}
    else:
        r = subprocess.run([sys.executable, J('tools', 'build.py'), '--all'], capture_output=True, text=True, env={**os.environ, 'KIT_PROJECT': current_project()})
        if r.returncode:
            print((r.stdout + r.stderr).strip()[-600:]); return 1
        site = P('out', 'site')
        if mode == 'page' and '--page' in a:
            ids = [a[a.index('--page') + 1]]
        else:
            ids = [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(site, '*.html'))) if not f.endswith('specimen.html')]
        if mode in ('system', 'package') and os.path.exists(os.path.join(site, 'specimen.html')):
            ids = ([] if mode == 'system' else ids) + ['specimen']
        elif mode == 'system':
            die('pass: no specimen page: write pages/specimen.json (S7 step 3)')
        files = [os.path.join(site, f'{i}.html') for i in ids]
        for f in files:
            if not os.path.exists(f):
                die(f'pass: {os.path.relpath(f, P())} not built')
        d = probe(files, S['widths'], 'page')
        counts = summarise(o, d, mode)
        brief = read_json(P('brief.json'), {})
        b = brief.get('budget') or {}
        lim = float(b.get('page_weight_mb') or S['page_weight_mb']) * 1024 * 1024
        lvl = float(b.get('reading_level') or S['reading_level'])
        for f, i in zip(files, ids):
            w = weight(f)
            if w > lim:
                o.add(f'FAIL weight: {i} is {w / 1048576:.2f} MB (budget {lim / 1048576:.2f} MB)', True); counts['weight'] = counts.get('weight', 0) + 1
            if i != 'specimen':
                g = fk_grade(page_texts(i))
                if g > lvl + 0.5:
                    o.add(f'FAIL reading: {i} reads at grade {g:.1f} (target {lvl:g})', True); counts['reading'] = counts.get('reading', 0) + 1
                txt = page_texts(i)
                if '[NEW]' in txt:
                    o.add(f'note: {i} has {txt.count("[NEW]")} [NEW] figure(s) (blocks packaging)')
        metas = {k: v.get('meta', {}) for k, v in d['info'].items() if k != 'specimen'}
        for fld in ('title', 'desc'):
            seen = {}
            for k, m in metas.items():
                if m.get(fld):
                    seen.setdefault(m[fld], []).append(k)
            for v, ks in seen.items():
                if len(ks) > 1:
                    o.add(f'FAIL meta: pages {", ".join(ks)} share one {fld}', True); counts['meta'] = counts.get('meta', 0) + 1
        if mode in ('system', 'package') or (mode == 'page' and '--page' not in a):
            n = reach(o, site, brief.get('key_page') or 'home')
            if n:
                counts['reach'] = n
        if mode in ('system', 'package'):
            css_checks(o)
        extra['heights'] = {k: v.get('height') for k, v in d['info'].items()}
    write_json(P('out', 'pass.json'), {'mode': mode, 'pass': not o.fail, 'counts': counts, **extra})
    return o.done(f'pass {mode}: ' + ('PASS' if not o.fail else 'FAIL') + (f' ({sum(counts.values())} finding(s))' if counts else ''))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
