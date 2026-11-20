#!/usr/bin/env python3
"""Claude Code hooks for the studio plugin: the gates and the measuring, enforced by the kit instead of by the prompt.

    hook.py pre     PreToolUse (Write|Edit|NotebookEdit): refuses a write the project's state does not allow yet
    hook.py post    PostToolUse (Write|Edit): rebuilds after a page, partial or token change; reports a schema error
    hook.py read    PostToolUse (Read): logs words read and images viewed to the project's events (gate.py counts them)
    hook.py stop    Stop: a stage that wrote its hand-off may not stop before gate.py --ready has run

Reads the hook event on stdin. Acts only inside a studio workspace ($KIT_HOME, else $CLAUDE_PROJECT_DIR, else the
working directory, holding studio/ or projects/); anywhere else it does nothing.
Writes refused: the engine (it changes only through G10; KIT_DEV=1 allows kit work), the studio registry and the
files tools own (state, usage, audit, events, packet), anything while a gate waits for the CD or after packaging,
and a project file before the stage that makes it (structure at S3, tokens at S4, page JSON at S5 ...).
"""
import json, os, re, subprocess, sys

EVENT = json.loads(sys.stdin.read() or '{}')
HOME = os.path.realpath(os.environ.get('KIT_HOME') or os.environ.get('CLAUDE_PROJECT_DIR') or EVENT.get('cwd') or os.getcwd())
os.environ['KIT_HOME'] = HOME
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, R, event, file_words, read_json   # noqa: E402  (after KIT_HOME is set)

ENGINE = os.path.realpath(J())
TOOL_ONLY = {'state.json', 'state.md', 'audit.jsonl', 'usage.jsonl', 'events.jsonl', 'overrides.json', '.session'}
# (pattern on the path inside the project, first stage that may write it); first match wins, unlisted paths are free
OPENS = [(r'^brief\.(json|md)$', 0), (r'^(research\.md|image-brief\.json|images/)', 1), (r'^content\.json$', 2),
         (r'^(structure(-\d+)?\.json|docs/cards/c\d|fingerprints/c\d)', 3),
         (r'^(tokens(-d\d+)?\.json|docs/cards/d\d|fingerprints/(d\d|chosen)|partials/)', 4), (r'^pages/', 5),
         (r'^interaction\.json$', 7), (r'^fingerprints/page-', 8)]
IMAGE = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif')


def workspace():
    return os.path.isdir(R('projects')) or os.path.isdir(R('studio'))


def where(path):
    """('engine', rel) | ('registry', rel) | ('project', name, rel) | (None,)"""
    p = os.path.realpath(path)
    if p == ENGINE or p.startswith(ENGINE + os.sep) or p.startswith(os.path.join(HOME, 'engine') + os.sep):
        return ('engine', p)
    if p.startswith(os.path.realpath(R('studio', 'registry')) + os.sep):
        return ('registry', p)
    proj = os.path.realpath(R('projects')) + os.sep
    if p.startswith(proj):
        name, _, rel = p[len(proj):].partition(os.sep)
        return ('project', name, rel.replace(os.sep, '/'))
    return (None,)


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                             'permissionDecisionReason': 'studio kit: ' + reason}}))
    return 0


def pre():
    ti = EVENT.get('tool_input') or {}
    path = ti.get('file_path') or ti.get('notebook_path')
    if not path or not workspace():
        return 0
    w = where(path)
    if w[0] == 'engine' and os.environ.get('KIT_DEV') != '1':
        return deny('the engine changes only through an approved G10 (S10 retro). Projects never edit it. '
                    'For kit work, start Claude Code with KIT_DEV=1.')
    if w[0] == 'registry':
        return deny('the studio registry is written by checkpoint.py only.')
    if w[0] != 'project':
        return 0
    name, rel = w[1], w[2]
    if not rel or rel in TOOL_ONLY or rel.startswith(('out/packet', 'out/checklist-')):
        return deny(f'{rel or name} is written by the kit tools (gate.py, start.sh), never by hand.')
    st = read_json(R('projects', name, 'state.json'), {})
    status, stage = st.get('status', 'working'), str(st.get('stage', '0'))
    if status == 'waiting':
        return deny(f'{name} is waiting for the creative director at {st.get("gate_pending")}. Show the packet and stop; '
                    'the CD records the decision (gate.py --decide).')
    if status in ('packaged', 'stopped', 'done'):
        return deny(f'{name} is {status}. The CD reopens a gate first (gate.py --reopen <gate>).')
    n = int(re.sub(r'\D', '', stage) or 0)
    for pat, opens in OPENS:
        if re.search(pat, rel):
            if n < opens:
                return deny(f'{rel} opens at stage {opens}; {name} is at stage {n}.')
            if opens == 0 and n > 0:
                return deny(f'{rel} was approved at G0. The CD reopens G0 to change it (gate.py --reopen G0).')
            break
    return 0


def post():
    w = where((EVENT.get('tool_input') or {}).get('file_path', ''))
    if w[0] != 'project' or not re.search(r'^(pages/|partials/|tokens\.json$)', w[2]):
        return 0
    r = subprocess.run([sys.executable, J('tools', 'build.py'), '--all'], capture_output=True, text=True,
                       env={**os.environ, 'KIT_PROJECT': w[1]})
    if r.returncode:
        print(json.dumps({'decision': 'block', 'reason': 'studio kit: build.py failed after this edit: '
                          + (r.stdout + r.stderr).strip()[-500:]}))
    return 0


def read():
    path = (EVENT.get('tool_input') or {}).get('file_path', '')
    w = where(path)
    proj = w[1] if w[0] == 'project' else os.environ.get('KIT_PROJECT') or (open(R('.current')).read().strip() if os.path.exists(R('.current')) else '')
    if not proj or not os.path.isdir(R('projects', proj)):
        return 0
    os.environ['KIT_PROJECT'] = proj
    if path.lower().endswith(IMAGE):
        event('image', 1, path=os.path.basename(path))
    else:
        event('read', file_words(path), path=os.path.basename(path))
    return 0


def stop():
    if EVENT.get('stop_hook_active') or not workspace():
        return 0
    proj = os.environ.get('KIT_PROJECT') or (open(R('.current')).read().strip() if os.path.exists(R('.current')) else '')
    st = read_json(R('projects', proj, 'state.json'), {}) if proj else {}
    if st.get('status') != 'working':
        return 0
    stages = R('projects', proj, 'docs', 'stages')
    hs = [os.path.join(stages, f) for f in os.listdir(stages)] if os.path.isdir(stages) else []
    newest = max((os.path.getmtime(f) for f in hs), default=0)
    if newest > os.path.getmtime(R('projects', proj, 'state.json')):
        print(json.dumps({'decision': 'block', 'reason': f'studio kit: {proj} has a new hand-off but the gate has not run. '
                          'Run gate.py --ready (studio gate --ready), show the packet, then stop for the CD.'}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit({'pre': pre, 'post': post, 'read': read, 'stop': stop}[sys.argv[1]]())
    except (KeyError, IndexError):
        print(__doc__); sys.exit(0)
    except Exception as e:   # a broken hook must never block the person's work; it reports and lets the call through
        print(f'studio kit hook error ({type(e).__name__}: {e})', file=sys.stderr); sys.exit(0)
