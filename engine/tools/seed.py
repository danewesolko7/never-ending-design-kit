#!/usr/bin/env python3
"""Unused ground: list the page forms, grids, movements and type classes none of the last N projects used.

    seed.py [--window 5]

Reads studio/registry/fingerprints.jsonl (project scope) and ref/catalogue.json. Writes out/seed.json in the current
project and prints the unused seeds. Each structure concept is built from one subject artefact plus one unused seed.
Fails only when the registry is unreadable.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, R, ST, current_project, die, event, read_json, read_jsonl, write_json

S = read_json(J('settings.json'))


def norm(s):
    return ' '.join(str(s).lower().replace('-', ' ').split())


def main(a):
    if a and a[0] in ('-h', '--help'):
        print(__doc__); return 0
    win = int(a[a.index('--window') + 1]) if '--window' in a else S['seed_window']
    try:
        latest = {}
        for r in read_jsonl(ST('registry', 'fingerprints.jsonl')):
            if r.get('scope', 'project') == 'project':
                latest.pop(r.get('project'), None); latest[r.get('project')] = r
        reg = list(latest.values())
    except (ValueError, OSError) as e:
        die(f'seed: registry unreadable ({e})')
    cat = read_json(J('ref', 'catalogue.json'))
    if not cat:
        die('seed: ref/catalogue.json missing')
    recent = reg[-win:]
    used = {'page_forms': {norm(r.get('form')) for r in recent}, 'grids': {norm(r.get('grid')) for r in recent},
            'movements': {norm(r.get('movement', '')) for r in recent}, 'type_classes': {norm(r.get('type_class')) for r in recent}}
    out = {k: [x for x in cat[k] if norm(x) not in used[k]] for k in used}
    out['window'] = [r.get('project') for r in recent]
    proj = current_project(required=False)
    if proj and os.path.isdir(R('projects', proj)):
        write_json(P('out', 'seed.json'), out)
        event('call')
    print(f'seed: last {len(recent)} project(s): {", ".join(out["window"])}')
    for k in ('page_forms', 'grids', 'movements', 'type_classes'):
        print(f'unused {k.replace("_", " ")} ({len(out[k])}): ' + '; '.join(out[k]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
