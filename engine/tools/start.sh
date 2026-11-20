#!/usr/bin/env bash
# Start (or resume) a session on one project.
#   bash tools/start.sh <project> [--no-setup] [--check]
# Checks the kit (setup cache + kitcheck), opens the stage's usage record (reusing one already open for this stage),
# and prints a resume of 300 words or fewer: state, what to read and the stage prompt.
# --check prints the resume without opening a usage record. Fails when the kit check fails.
K="$(cd "$(dirname "$0")/.." && pwd)"; cd "$K"
H="${KIT_HOME:-$(cd .. && pwd)}"; export KIT_HOME="$H"   # the studio's workspace: studio/, projects/
PROJ="$1"
[ -n "$PROJ" ] || { echo "start: usage: bash tools/start.sh <project>"; exit 1; }
[[ "$PROJ" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "start: project names are lower-case letters, digits and hyphens"; exit 1; }
case " $* " in *" --no-setup "*) ;; *)
  bash tools/setup.sh || { echo "start: setup failed (run bash tools/setup.sh to see why)"; exit 1; } ;;
esac
case " $* " in *" --check "*) export KIT_CHECK=1 ;; esac
# a fresh copy of the boilerplate has no studio yet: start one from the example overlay
[ -d "$H/studio" ] || { cp -R ../studio.example "$H/studio" && echo "start: new studio created from studio.example/ (fill in studio/studio.json and studio/taste.md)"; }
bash tools/kitcheck.sh >/tmp/kitcheck.$$ 2>&1 || { tail -8 /tmp/kitcheck.$$; rm -f /tmp/kitcheck.$$; echo "start: kitcheck failed. Stop and tell the creative director; never rewrite a kit tool by hand."; exit 1; }
rm -f /tmp/kitcheck.$$
echo "$PROJ" > "$H/.current"
KIT_PROJECT="$PROJ" python3 - <<'EOF'
import os, random, re, string, sys
sys.path.insert(0, 'tools')
from kitlib import J, P, ST, append_jsonl, event, file_words, now, read_json, read_jsonl, words, write_json
proj = os.environ['KIT_PROJECT']
new = not os.path.isdir(P())
for d in ('docs/stages', 'pages', 'partials', 'out', 'fingerprints'):
    os.makedirs(P(d), exist_ok=True)
st = read_json(P('state.json'))
if st is None:
    st = {'project': proj, 'stage': '0', 'status': 'working', 'options_next': read_json(J('settings.json'))['options_default'], 'decisions': []}
    write_json(P('state.json'), st)
brief = read_json(P('brief.json'), {})
check = bool(os.environ.get('KIT_CHECK'))
stage = str(st.get('stage', '0'))
reads = ['prompts/P0.md', 'rules/rules.md', 'studio/taste-checks.md', f'prompts/S{stage}.md']
last = st.get('last_handoff')
nxt = []
if last and os.path.exists(P(last)):
    t = open(P(last), encoding='utf-8').read()
    m = re.search(r'^next reads:\s*(.+)$', t, re.M | re.I)
    if m:
        nxt = [x.strip() for x in m.group(1).split(',') if x.strip()]
    reads.append(last)
reads += nxt
# reuse a record already open for this stage; close records left open for other stages; open one only if none
rows = read_jsonl(P('usage.jsonl'))
closed = {r['rid'] for r in rows if r.get('type') == 'close'}
live = [r for r in rows if r.get('type') == 'open' and r['rid'] not in closed]
same = [r for r in live if str(r.get('stage')) == stage]
sess = same[-1]['session'] if same else now()[:10].replace('-', '') + '-' + ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
if not check:
    for r in live:
        if str(r.get('stage')) != stage:
            append_jsonl(P('usage.jsonl'), {'type': 'close', 'rid': r['rid'], 'stage': r['stage'], 'end': now(), 'outcome': 'abandoned',
                                            'project': proj, 'session': r.get('session'), 'words_read': 0, 'words_written': 0, 'caps_hit': []})
    open(P('.session'), 'w').write(sess)
    if not same and st.get('status') != 'waiting':
        append_jsonl(P('usage.jsonl'), {'type': 'open', 'rid': f'{stage}-{sess}', 'project': proj, 'stage': stage,
                                        'session': sess, 'start': now(), 'reads': reads})
caps = read_json(J('settings.json'))['caps'].get(stage, {})
print(f'kit ok | project {proj}' + (' (new)' if new else '') + (' | check only' if check else f' | session {sess}'))
print(f'stage {stage} | status {st.get("status")}' + (f' | waiting on {st["gate_pending"]}' if st.get('gate_pending') else '')
      + (f' | fixes to apply: {st["fixes"]}' if st.get('fixes') else ''))
print(f'paths: engine {J()} | studio {ST()} | project {P()}')
print(f'read, in order: ' + ', '.join(reads))
print(f'limits: read {caps.get("read", "?")} words, view {caps.get("images", 0)} image(s)')
print(f'options this stage: {1 if brief.get("lean_mode") else st.get("options_next", read_json(J("settings.json"))["options_default"])}' + (' (lean mode)' if brief.get('lean_mode') else ''))
if st.get('status') == 'waiting':
    print(f'waiting for the creative director at {st.get("gate_pending")}: show out/packet.md; record with gate.py --decide')
elif st.get('status') in ('stopped', 'done', 'packaged'):
    print(f'project is {st.get("status")}. Reopen a gate with gate.py --reopen <gate>, or run a retro with gate.py --retro.')
else:
    print('end of stage: write the hand-off, run tools/gate.py --ready, then STOP and wait for the decision.')
EOF
