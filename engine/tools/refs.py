#!/usr/bin/env python3
"""Inspiration references: the library first, then the web for what it lacks.

    refs.py --gaps [--sections 3-7]      rows per library section (engine ref/library.md + studio/library.md + this
                                         project's references); flags thin sections: sweep the web for those
    refs.py --check [--sweep A|B|C]      validates references.jsonl: fields, real links, one technique each, no more
                                         than two from one site per sweep, the sweep's minimum count
    refs.py --promote                    at packaging: appends each reference the build used to studio/library.md
                                         (studio only, never the engine), once

references.jsonl (one row per reference, in the project folder):
{"sweep": "A|B|C", "section": 1-11, "title": "", "url": "https://...", "seen": "YYYY-MM-DD",
 "technique": "the one technique borrowed", "use": "when to use it", "used": false}
Sections are the library's numbers (1 page forms, 2 grid, 3 type, 4 colour, 5 image, 6 texture, 7 motion, 8 data,
9 proof, 10 conversion, 11 notation). Set "used": true when the build uses the technique.
"""
import os, re, sys
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, ST, Out, current_project, die, event, read_json, read_jsonl, words, write_atomic, write_json
from uniq import same

S = read_json(J('settings.json'))
NAMES = {1: 'page forms', 2: 'grid and pacing', 3: 'typography', 4: 'colour', 5: 'image treatment', 6: 'texture and surfaces',
         7: 'motion', 8: 'data and explanation', 9: 'proof and trust', 10: 'conversion', 11: 'notation'}
FIELDS = ('sweep', 'section', 'title', 'url', 'seen', 'technique')


def library_rows(path):
    """{section number: [technique, ...]} from a library file's tables."""
    rows, sec = {}, None
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding='utf-8'):
        m = re.match(r'^## (\d+)\.', line)
        if m:
            sec = int(m.group(1)) if int(m.group(1)) in NAMES else None
            continue
        if line.startswith('## '):
            sec = None
        if sec and line.startswith('|'):
            c = [x.strip() for x in line.strip()[1:-1].split('|')]
            if c[0] != 'Technique' and not all(set(x) <= set('-') for x in c):
                rows.setdefault(sec, []).append(c[0])
    return rows


def sections_arg(a):
    if '--sections' not in a:
        return sorted(NAMES)
    lo, _, hi = a[a.index('--sections') + 1].partition('-')
    return list(range(int(lo), int(hi or lo) + 1))


def cmd_gaps(a, o):
    eng, stu = library_rows(J('ref', 'library.md')), library_rows(ST('library.md'))
    proj = {}
    for r in read_jsonl(P('references.jsonl')):
        proj[r.get('section')] = proj.get(r.get('section'), 0) + 1
    thin = S.get('library_thin', 4)
    gaps = []
    for s in sections_arg(a):
        n = len(eng.get(s, [])) + len(stu.get(s, [])) + proj.get(s, 0)
        flag = n < thin
        gaps += [s] if flag else []
        o.add(f'{"SWEEP" if flag else "ok   "} {s:>2} {NAMES[s]}: {n} technique(s) (engine {len(eng.get(s, []))}, studio {len(stu.get(s, []))}, project {proj.get(s, 0)})')
    write_json(P('out', 'refs-gaps.json'), {'thin': gaps, 'threshold': thin})
    return o.done(f'refs gaps: {len(gaps)} thin section(s)' + (f' to sweep: {", ".join(NAMES[s] for s in gaps)}' if gaps else ''))


def cmd_check(a, o):
    rows = read_jsonl(P('references.jsonl'))
    sweep = a[a.index('--sweep') + 1] if '--sweep' in a else None
    if sweep:
        rows = [r for r in rows if r.get('sweep') == sweep]
    known = [t for d in (library_rows(J('ref', 'library.md')), library_rows(ST('library.md'))) for ts in d.values() for t in ts]
    urls, hosts = set(), {}
    for i, r in enumerate(rows, 1):
        tag = f'row {i} ({r.get("title", "?")[:40]})'
        miss = [k for k in FIELDS if not str(r.get(k, '')).strip()]
        if miss:
            o.add(f'FAIL {tag}: missing {", ".join(miss)}', True)
        u = urlparse(str(r.get('url', '')))
        if u.scheme not in ('http', 'https') or not u.netloc:
            o.add(f'FAIL {tag}: url is not a web link (open what you cite)', True)
        elif r['url'] in urls:
            o.add(f'FAIL {tag}: duplicate url', True)
        urls.add(r.get('url'))
        host = u.netloc.lower().removeprefix('www.')
        hosts.setdefault((r.get('sweep'), host), []).append(i)
        if r.get('sweep') not in ('A', 'B', 'C'):
            o.add(f'FAIL {tag}: sweep must be A, B or C', True)
        if r.get('section') not in NAMES:
            o.add(f'FAIL {tag}: section must be a library number 1-11', True)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(r.get('seen', ''))):
            o.add(f'FAIL {tag}: seen must be a date (YYYY-MM-DD)', True)
        if words(r.get('technique', '')) > 25:
            o.add(f'FAIL {tag}: one technique in 25 words or fewer', True)
        dup = next((k for k in known if same(r.get('technique', ''), k)), None)
        if dup:
            o.add(f'note {tag}: the library already has "{dup[:60]}" (find a technique it lacks)')
    for (sw, host), ids in hosts.items():
        if len(ids) > 2:
            o.add(f'FAIL sweep {sw}: {len(ids)} references from {host} (two per site at most)', True)
    mins = S.get('sweep_min', {})
    for sw in ([sweep] if sweep else sorted({r.get('sweep') for r in rows if r.get('sweep')})):
        n = len([r for r in rows if r.get('sweep') == sw])
        if n < mins.get(sw, 0):
            o.add(f'FAIL sweep {sw}: {n} reference(s), at least {mins[sw]} needed', True)
    return o.done(f'refs check: {len(rows)} reference(s)' + (f' in sweep {sweep}' if sweep else '') + (': PASS' if not o.fail else ': FAIL'))


def cmd_promote(a, o):
    rows = read_jsonl(P('references.jsonl'))
    todo = [r for r in rows if r.get('used') and not r.get('promoted')]
    path = ST('library.md')
    if not todo:
        return o.done('refs promote: nothing new to add')
    text = open(path, encoding='utf-8').read() if os.path.exists(path) else '# Technique library (studio)\n'
    for r in todo:
        row = f'| {r["technique"]} | {r["title"]} ({r["url"]}) | {r.get("use", "")} | yes |'
        head = re.search(rf'^## {r["section"]}\. .*$', text, re.M)
        if head:   # end of that section's table
            nxt = re.search(r'^## ', text[head.end():], re.M)
            at = head.end() + (nxt.start() if nxt else len(text) - head.end())
            text = text[:at].rstrip('\n') + '\n' + row + '\n\n' + text[at:]
        else:      # a new section, before "Proven here" when it exists
            block = f'## {r["section"]}. {NAMES[r["section"]].capitalize()}\n\n| Technique | Seen at | Use when | Proven |\n|---|---|---|---|\n{row}\n\n'
            m = re.search(r'^## Proven here', text, re.M)
            text = text[:m.start()] + block + text[m.start():] if m else text.rstrip('\n') + '\n\n' + block
        r['promoted'] = True
        o.add(f'added to studio/library.md section {r["section"]}: {r["technique"][:70]}')
    write_atomic(path, text)
    write_atomic(P('references.jsonl'), ''.join(__import__('json').dumps(r, ensure_ascii=False) + '\n' for r in rows))
    return o.done(f'refs promote: {len(todo)} technique(s) added to the studio library')


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    current_project(); event('call')
    for flag, fn in (('--gaps', cmd_gaps), ('--check', cmd_check), ('--promote', cmd_promote)):
        if flag in a:
            return fn(a, Out('refs', P('out', 'reports', f'refs-{flag[2:]}.md')))
    die('refs: give --gaps, --check or --promote')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
