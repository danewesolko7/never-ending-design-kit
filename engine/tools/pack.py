#!/usr/bin/env python3
"""Pack the kit or one project into one self-unpacking Python file, for hosts that keep files but not folders.

    pack.py --kit <out.py>             the whole kit: engine/ (tools, prompts, rules, ref, primitives, fixtures, settings,
                                       MANIFEST), studio/ (taste, library, registry), studio.example/ and README (text only)
    pack.py <project> <out.py>         projects/<project>/ without out/ and without images/ (photos are never packed)
    pack.py <project> <out.py> --with-images   include images/ (a local backup only; never share it)

Restore: save the file to disk, then
    python3 <file> [kit folder]        default folder: ./design-kit (kit), or the kit folder for a project
Save and restore by file path (adapters/<host>.md says where); bytes never pass through the model.
"""
import base64, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, R, ST, die, write_atomic

KIT_PARTS = ('engine/', 'studio.example/', '.claude-plugin/', 'agents/', 'commands/', 'skills/', 'hooks/', 'bin/',
             'README.md', 'NOTICE', 'LICENSE', 'LICENSE-CONTENT', '.gitignore')
ENGINE_SKIP = ('engine/out/', 'engine/tools/node_modules', 'engine/deps/node_modules')
STUDIO_SKIP = ('registry/thumbs/', 'registry/library/')
IMAGE_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif')

TEMPLATE = '''#!/usr/bin/env python3
"""%s

Restore: python3 <this file> [kit folder]   (default: ./design-kit). Then: bash <kit>/engine/tools/start.sh <project>
"""
import base64, json, os, sys
FILES = json.loads(%%r)
root = sys.argv[1] if len(sys.argv) > 1 else 'design-kit'
base = os.path.join(root, %%r)
for rel, text in FILES.items():
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    tmp = p + '.part'
    if text.startswith('b64:'):
        open(tmp, 'wb').write(base64.b64decode(text[4:]))
    else:
        open(tmp, 'w', encoding='utf-8').write(text)
    os.replace(tmp, p)
    if rel.endswith('.sh') or rel.startswith('bin/'):
        os.chmod(p, 0o755)
print(f'{len(FILES)} files written to {base or root}/')
'''


def collect(root, skip=(), keep=()):
    files = {}
    for d, dirs, fs in os.walk(root):
        if keep and d == root:   # walk only the kit's own top-level folders, never projects/
            dirs[:] = [x for x in dirs if x + '/' in keep]
        dirs.sort()
        for f in sorted(fs):
            full = os.path.join(d, f)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            if (keep and not rel.startswith(keep)) or rel.startswith(skip) or '/__pycache__/' in '/' + rel or '/.git/' in '/' + rel or f.startswith('.tmp-') or f == '.DS_Store':
                continue
            raw = open(full, 'rb').read()
            try:
                files[rel] = raw.decode('utf-8')
            except UnicodeDecodeError:
                files[rel] = 'b64:' + base64.b64encode(raw).decode()
    return files


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    if a[0] == '--kit':
        files, sub, head = collect(os.path.dirname(J()), ENGINE_SKIP, KIT_PARTS), '', 'Design kit: the one working kit (engine, studio overlay).'
        files.update({'studio/' + k: v for k, v in collect(ST(), STUDIO_SKIP).items()})   # the studio from $KIT_HOME
        files = {k: v for k, v in files.items() if not k.lower().endswith(IMAGE_EXT)}
    else:
        if not os.path.isdir(R('projects', a[0])):
            die(f'pack: no project {a[0]}')
        skip = ('out/', '.session') + (() if '--with-images' in a else ('images/',))
        files, sub, head = collect(R('projects', a[0]), skip), f'projects/{a[0]}', f'Project pack: {a[0]}. Photos are not packed: re-source them from image-brief.json.'
    a = [x for x in a if x != '--with-images']
    out = a[1] if len(a) > 1 else die('pack: give an output path')
    write_atomic(out, (TEMPLATE % head) % (json.dumps(files), sub))
    size = os.path.getsize(out)
    print(f'pack: {len(files)} files -> {out} ({size // 1024} KB)')
    if size > 1024 * 1024:
        print('pack: warning: over 1 MB: photos or built output got in. Do not save this pack.')
    print('pack: save it as adapters/<host>.md says' + (' (a project pack, never in place of the kit)' if sub.startswith('projects/') else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
