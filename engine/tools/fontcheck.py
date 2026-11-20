#!/usr/bin/env python3
"""Every typeface is present and licensed.

    fontcheck.py [tokens-d<n>.json]     default tokens.json; a direction card's tokens file checks that card's faces

Checks tokens.json type.faces: family, source and licence filled; every listed file found (setup cache for
"fontsource:<package>", or projects/<p>/fonts/ for faces the CD supplies). Also fails when a partial's CSS names a
family that is not in tokens.json. A face not on Fontsource needs files from the CD, or the card's alternate face.
"""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import P, current_project, die, event, read_json
from build import font_file

GENERIC = {'serif', 'sans-serif', 'monospace', 'system-ui', 'cursive', 'fantasy', 'inherit', 'ui-monospace', 'ui-sans-serif', 'ui-serif', '-apple-system'}


def main(a):
    if a and a[0] in ('-h', '--help'):
        print(__doc__); return 0
    current_project(); event('call')
    tf = next((x for x in a if x.endswith('.json')), 'tokens.json')
    tok = read_json(P(tf))
    if tok is None:
        die(f'fontcheck: no {tf}')
    faces = (tok.get('type') or {}).get('faces') or []
    bad = []
    if not faces:
        bad.append('tokens.json has no type.faces')
    fams = set()
    for f in faces:
        fam = f.get('family', '?'); fams.add(fam.lower())
        if f.get('alternate'):
            fams.add(f['alternate'].lower())
        for k in ('source', 'licence'):
            if not str(f.get(k, '')).strip():
                bad.append(f'{fam}: {k} is blank')
        if not f.get('files'):
            bad.append(f'{fam}: no files listed')
        for ff in f.get('files') or []:
            if not font_file(ff.get('file', '')):
                bad.append(f'{fam}: file {ff.get("file")} missing (run setup.sh; a face not on Fontsource needs files from the CD in projects/<p>/fonts/)')
    for css in glob.glob(P('partials', '*.css')):
        for m in re.finditer(r'font-family\s*:\s*([^;}]+)', open(css, encoding='utf-8').read()):
            first = m.group(1).split(',')[0].strip().strip('\'"')
            if first and not first.startswith('var(') and first.lower() not in GENERIC and first.lower() not in fams:
                bad.append(f'{os.path.basename(css)} names "{first}", which is not in tokens.json')
    for b in bad[:18]:
        print('FAIL ' + b)
    print(f'fontcheck: {len(faces)} face(s): ' + ('PASS' if not bad else f'FAIL ({len(bad)})'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
