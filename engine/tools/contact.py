#!/usr/bin/env python3
"""One labelled contact sheet from a set of PNGs, 1000px or less on its long side (the only size a model views).

    contact.py <out.png> <png or glob> [more ...] [--w 200] [--hmax 1500] [--cols N]

Expands the globs, then draws the sheet with contact.js (Chromium's canvas through the pinned playwright).
"""
import glob, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import event, node_env   # noqa: E402
OPTS = ('--w', '--hmax', '--cols')


def main(a):
    if len(a) < 2 or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    args, i = [a[0]], 1
    while i < len(a):
        if a[i] in OPTS:
            args += [a[i], str(int(a[i + 1]))]; i += 2; continue
        args += sorted(glob.glob(a[i])) or ([a[i]] if os.path.exists(a[i]) else []); i += 1
    r = subprocess.run(['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contact.js'), *args],
                       capture_output=True, text=True, env=node_env())
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)
    if r.returncode == 0 and 'no PNGs matched' not in r.stdout:
        event('render')
    return r.returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
