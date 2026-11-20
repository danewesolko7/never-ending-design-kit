"""Shared helpers for the kit tools: paths, atomic writes, event log, short output, secrets, word counts.

Every tool imports this. Nothing here holds a project value.
"""
import datetime, json, os, re, sys, tempfile

# Three layers: engine/ (this kit: tools, prompts, rules, ref), studio/ (one studio's taste, library and registry)
# and projects/ (one folder per project). studio/ and projects/ live in $KIT_HOME, by default beside the engine, so the
# engine can be installed anywhere (a plugin). The engine never holds a studio or project value.
KIT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ROOT = os.path.realpath(os.environ.get('KIT_HOME') or os.path.dirname(KIT))   # the studio's workspace (studio/, projects/)
J = lambda *p: os.path.join(KIT, *p)
R = lambda *p: os.path.join(ROOT, *p)
ST = lambda *p: os.path.join(ROOT, 'studio', *p)
MAX_LINES = 20


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def current_project(required=True):
    """The project named in .current (written by start.sh), or $KIT_PROJECT."""
    p = os.environ.get('KIT_PROJECT')
    if not p and os.path.exists(R('.current')):
        p = open(R('.current')).read().strip()
    if required and not p:
        die('no current project: run tools/start.sh <project> first')
    return p


def P(*parts, project=None):
    return R('projects', project or current_project(), *parts)


def write_atomic(path, data, mode='w'):
    """Write to a temp file in the same folder, then rename: a failed run never leaves a half-written file."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.tmp-')
    with os.fdopen(fd, mode if 'b' in mode else 'w', **({} if 'b' in mode else {'encoding': 'utf-8'})) as f:
        f.write(data)
    os.replace(tmp, path)


def write_json(path, obj):
    write_atomic(path, json.dumps(obj, indent=1, ensure_ascii=False) + '\n')


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def append_jsonl(path, rec):
    """Append-only, with an exclusive lock so concurrent projects never interleave a line."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    import fcntl
    with open(path, 'a', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        fcntl.flock(f, fcntl.LOCK_UN)


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]


def event(kind, n=1, **kv):
    """Kit tools log their own events (call, fetch, render, spawn) to the project's events file."""
    proj = current_project(required=False)
    if not proj or not os.path.isdir(R('projects', proj)):
        return
    append_jsonl(R('projects', proj, 'events.jsonl'), {'t': now(), 'kind': kind, 'n': n, **kv})


def words(text):
    return len(re.findall(r"[A-Za-z0-9][\w'’.-]*", text or ''))


def file_words(path):
    if not os.path.exists(path):
        return 0
    if os.path.isdir(path):
        return sum(file_words(os.path.join(r, f)) for r, _, fs in os.walk(path) for f in fs
                   if f.endswith(('.md', '.json', '.html', '.css', '.txt')))
    try:
        return words(open(path, encoding='utf-8').read())
    except UnicodeDecodeError:
        return 0


SECRET = re.compile(r'(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}'
                    r'|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:password|api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9/+_-]{12,})')


def secrets_in(text):
    return [m.group(0)[:12] + '...' for m in SECRET.finditer(text or '')]


class Out:
    """Collect report lines; print at most 20, write all to the report file."""
    def __init__(self, tool, report):
        self.tool, self.report, self.lines, self.fail = tool, report, [], False

    def add(self, line, fail=False):
        self.lines.append(line)
        self.fail = self.fail or fail

    def done(self, summary):
        write_atomic(self.report, '\n'.join(self.lines + ['', summary]) + '\n')
        shown = self.lines[:MAX_LINES - 2]
        for l in shown:
            print(l)
        if len(self.lines) > len(shown):
            print(f'... {len(self.lines) - len(shown)} more line(s)')
        print(f'{summary} | report: {os.path.relpath(self.report, KIT)}')
        return 1 if self.fail else 0


def node_env():
    """Environment for node tools: the setup cache (axe-core, fonts) plus the workspace's playwright."""
    nm = os.environ.get('KIT_NODE') or (open(R('.node')).read().strip() if os.path.exists(R('.node')) else J('tools', 'node_modules'))
    env = {**os.environ, 'KIT_NODE': nm}
    env['NODE_PATH'] = ':'.join(x for x in (nm, os.environ.get('NODE_PATH', ''), '/opt/npm-tools/node_modules',
                                            os.path.expanduser('~/.npm-global/lib/node_modules')) if x)
    return env


def die(msg, code=1):
    print(msg)
    sys.exit(code)
