#!/usr/bin/env python3
"""Gate control: the only tool that writes the gate packet, state.md, usage records and the audit log.

    gate.py --ready                         close the stage: check the hand-off, close the usage record, build packet + state
    gate.py --decide <gate> --approve | --pick <n> | --fixes "<a; b>" | --stop  [--note ".."] [--options <n>] [--last]
    gate.py --credits <n>                   enter this session's credits (split across its stages by words)
    gate.py --checklist [--page <id>]       the 10 taste questions, script answers filled in where they exist
    gate.py --reopen <gate> [--confirm]     list what reopening invalidates and its typical cost; --confirm records it
    gate.py --retro                         open S10 (studio director) on a packaged or stopped project; G10 closes it
    gate.py --override <check> --reason ".." [--target <name>]
    gate.py --budget <n>                    raise the project credit budget (logged)
    gate.py --event <render|image> [n]
    gate.py --typical <stage>  |  --status

Gates: G0 G1 G2 G3a G3b/G4a G4b G5 G6 G7 G8 G10. Every decision, override, reopen and credit entry goes to
projects/<p>/audit.jsonl with the time and the person (--by, default CD). The model never writes the packet or state.
"""
import os, re, statistics, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import (J, P, R, ST, Out, append_jsonl, current_project, die, file_words, now, read_json, read_jsonl,
                    secrets_in, words, write_atomic, write_json)

S = read_json(J('settings.json'))
FIELDS = ('stage', 'decided', 'new files', 'open', 'next reads', 'decide')
OPTIONAL = ('options', 'revisions', 'images viewed', 'fixes')


def arg(a, name, default=None):
    if name in a:
        i = a.index(name)
        return a[i + 1] if i + 1 < len(a) else default
    return default


def state():
    return read_json(P('state.json'), {})


def save_state(st):
    write_json(P('state.json'), st)


def audit(action, gate='', detail='', by='CD'):
    append_jsonl(P('audit.jsonl'), {'time': now(), 'person': by, 'gate': gate, 'action': action, 'detail': detail})


# ---------- hand-off ----------
def latest_handoff(st):
    d = P('docs', 'stages')
    if not os.path.isdir(d):
        return None
    fs = [f for f in os.listdir(d) if re.match(r'^\d+[a-z]?(-\d+)?\.md$', f)]
    if not fs:
        return None
    fs.sort(key=lambda f: os.path.getmtime(os.path.join(d, f)))
    return os.path.join(d, fs[-1])


def parse_handoff(text):
    out, key = {}, None
    for line in text.splitlines():
        m = re.match(r'^\s*(stage|decided|new files|open|next reads|decide|options|revisions|images viewed|fixes)\s*:\s*(.*)$', line, re.I)
        if m:
            key = m.group(1).lower()
            rest = m.group(2).strip()
            if key == 'stage':   # stage: <n> | status: done | date: ...
                for part in rest.split('|'):
                    if ':' in part:
                        k, v = part.split(':', 1); out[k.strip().lower()] = v.strip()
                    else:
                        out['stage'] = part.strip()
                continue
            out[key] = rest
        elif key and line.strip():
            out[key] = (out.get(key, '') + '\n' + line.strip()).strip()
    return out


def split_list(v):
    return [x.strip(' -') for x in re.split(r'[\n,]', v or '') if x.strip(' -') and x.strip().lower() != 'none']


# ---------- usage ----------
def usage_rows():
    return read_jsonl(P('usage.jsonl'))


def open_record():
    rows = usage_rows()
    closed = {r['rid'] for r in rows if r.get('type') == 'close'}
    opens = [r for r in rows if r.get('type') == 'open' and r['rid'] not in closed]
    return opens[-1] if opens else None


def events_since(t0):
    c = {'call': 0, 'fetch': 0, 'render': 0, 'spawn': 0, 'image': 0, 'read': 0}
    for e in read_jsonl(P('events.jsonl')):
        if e['t'] >= t0 and e['kind'] in c:
            c[e['kind']] += e.get('n', 1)
    return c


def credits_total():
    return sum(r.get('credits', 0) or 0 for r in usage_rows() if r.get('type') == 'credits')


def budget_left(brief):
    b = (brief.get('budget') or {}).get('credits')
    if not b:
        return None
    return max(0.0, 1 - credits_total() / float(b))


def typical(stage):
    vals = []
    for path in (ST('registry', 'usage-log.jsonl'), P('usage.jsonl')):
        for r in read_jsonl(path):
            if r.get('type') in ('stage', 'credits_split') and str(r.get('stage')) == str(stage) and r.get('credits'):
                vals.append(float(r['credits']))
    return f'{statistics.median(vals):,.0f}' if vals else 'n/a'


def resolve(x):
    """A path as prompts write it: absolute, the project's, the studio workspace's (studio/...), else the engine's."""
    if os.path.isabs(x):
        return x
    return next((p for p in (P(x), R(x)) if os.path.exists(p)), J(x))


def caps_for(stage):
    return S['caps'].get(str(stage), {})


# ---------- commands ----------
def cmd_ready(a):
    st, brief = state(), read_json(P('brief.json'), {})
    o = Out('gate', P('out', 'gate-ready.md'))
    hp = latest_handoff(st)
    if not hp:
        die('gate: no hand-off in docs/stages/: write it from the HAND-OFF template first')
    text = open(hp, encoding='utf-8').read()
    h = parse_handoff(text)
    missing = [f for f in FIELDS if not h.get(f)]
    n = words(text)
    cap = S['words_caps']['handoff']
    bad = []
    if missing:
        bad.append(f'hand-off missing fields: {", ".join(missing)}')
    if n > cap:
        bad.append(f'hand-off is {n} words (cap {cap}): cut it, delta only')
    newf = split_list(h.get('new files'))
    for f in [hp] + [P(x) if not os.path.isabs(x) else x for x in newf]:
        if os.path.isfile(f):
            s = secrets_in(open(f, encoding='utf-8', errors='ignore').read())
            if s:
                bad.append(f'secret pattern in {os.path.relpath(f, P())}: {s[0]} (remove it; nothing secret goes in files)')
    if bad:
        for b in bad:
            print('FAIL ' + b)
        sys.exit(1)
    stage = re.sub(r'[^\dA]', '', h.get('stage', '')) or str(st.get('stage', '?'))
    rec = open_record() or {'rid': f'{stage}-{now()}', 'stage': stage, 'start': now(), 'reads': []}
    ev = events_since(rec['start'])
    read_w = ev['read'] or sum(file_words(resolve(x)) for x in rec.get('reads', []))   # measured reads (hooks), else the planned list
    written = n + sum(file_words(P(x)) for x in newf)
    choices = [c for c in re.split(r'\s*/\s*', (h.get('decide', '').split('choices:')[1].split('|')[0] if 'choices:' in h.get('decide', '') else '')) if c.strip()]
    made = int(re.match(r'\d+', h.get('options', '')).group(0)) if re.match(r'\d+', h.get('options', '')) else max(1, len(choices) if len(choices) > 1 and 'approve' not in (h.get('decide') or '').lower() else 1)
    caps = caps_for(stage)
    hit = []
    if caps.get('read') and read_w > caps['read'] * (1 if not caps.get('per_page') else max(1, len(newf))):
        hit.append('words read')
    if ev['image'] > caps.get('images', 99):
        hit.append('images viewed')
    close = {'type': 'close', 'rid': rec['rid'], 'project': current_project(),
             'stage': stage, 'gate': gate_for(stage, h), 'session': rec.get('session', ''), 'start': rec['start'], 'end': now(),
             'renders': ev['render'], 'images_viewed': ev['image'], 'words_read': read_w, 'words_written': written,
             'options_made': made, 'revisions': int(h.get('revisions') or 0), 'caps_hit': hit}
    append_jsonl(P('usage.jsonl'), close)
    left = budget_left(brief)
    nxt = S['gates'].get(close['gate'], {}).get('next')
    st.update({'stage': stage, 'status': 'waiting', 'gate_pending': close['gate'], 'last_handoff': os.path.relpath(hp, P()),
               'open': split_list(h.get('open'))})
    save_state(st)
    usage = (f"usage: S{stage} | renders {ev['render']} | images viewed {ev['image']} | "
             f"read {read_w / 1000:.1f}k words | options {made}/- | next typical {typical(nxt) if nxt is not None else 'n/a'} | "
             f"budget left {('%d%%' % round(left * 100)) if left is not None else 'n/a'}")
    dq = h.get('decide', '')
    q = re.sub(r'^\s*G[0-9A-Za-z/]+\s*:\s*', '', dq.split('|')[0].strip())
    packet = [f"made: {h.get('decided', '').splitlines()[0][:140]}",
              f'decide: {close["gate"]}: {q}',
              f"choices: {' / '.join(choices) if choices else 'approve / change / stop'}",
              f"unlocks: {(dq.split('unlocks:')[1].strip() if 'unlocks:' in dq else S['gates'].get(close['gate'], {}).get('unlocks', ''))[:120]}",
              f"open: {(split_list(h.get('open')) or ['none'])[0][:120]}" + (f' (+{len(split_list(h.get("open"))) - 1})' if len(split_list(h.get('open'))) > 1 else ''),
              usage]
    if hit:
        packet.append(f'caps hit: {", ".join(hit)}')
    if left is not None and left <= 0:
        packet.append('STOP: project budget reached. Raise it with gate.py --budget <n> to continue.')
    elif left is not None and left <= 1 - S['budget_warn']:
        packet.append(f'warning: {round((1 - left) * 100)}% of the budget used')
    if close['gate'] in [g for g, v in S['gates'].items() if v['visual']] and not os.path.exists(P('out', f'checklist-{close["gate"].replace("/", "-")}.md')):
        packet.append('note: visual gate: run gate.py --checklist before showing it')
    write_atomic(P('out', 'packet.md'), '\n'.join(packet) + '\n')
    write_state_md()
    print('\n'.join(packet))
    print('credits: enter this session\'s figure with gate.py --credits <n> (unit: %s)' % ((brief.get('budget') or {}).get('unit') or S['credit_unit']))
    return 1 if (left is not None and left <= 0) else 0


def gate_for(stage, h):
    m = re.search(r'\b(G\d+[ab]?(?:/G\d+[ab]?)?)\b', h.get('decide', ''))
    if m:
        return m.group(1)
    return {'0': 'G0', '1': 'G1', '2': 'G2', '3': 'G3a', '4': 'G3b/G4a', '5': 'G5', '6': 'G6', '7': 'G7', '8': 'G8', '10': 'G10'}.get(str(stage), f'G{stage}')


def cmd_decide(a):
    g = arg(a, '--decide')
    if g not in S['gates']:
        die(f'gate: unknown gate {g}. Gates: {" ".join(S["gates"])}')
    st, brief = state(), read_json(P('brief.json'), {})
    left = budget_left(brief)
    if left is not None and left <= 0 and '--stop' not in a:
        die('gate: project budget reached. Raise it first: gate.py --budget <n>')
    by = arg(a, '--by', 'CD')
    if '--approve' in a:
        action, detail = 'approve', ''
    elif '--pick' in a:
        action, detail = 'pick', arg(a, '--pick')
    elif '--fixes' in a:
        action, detail = 'change', arg(a, '--fixes')
    elif '--stop' in a:
        action, detail = 'stop', ''
    else:
        die('gate: give --approve, --pick <n>, --fixes "<a; b>" or --stop')
    note = arg(a, '--note', '')
    opts = arg(a, '--options')
    if opts:
        n = int(opts)
        if brief.get('lean_mode') and n > 1:
            die('gate: lean mode is on: every option count is 1 (reopen G0 to change lean mode)')
        if n > S['options_max']:
            die(f'gate: at most {S["options_max"]} options')
        st['options_next'] = n
    rec = {'time': now(), 'gate': g, 'action': action, 'detail': detail, 'note': note}
    st.setdefault('decisions', []).append(rec)
    audit('decide', g, f'{action} {detail} {note}'.strip(), by)
    fixes = len([x for x in re.split(r';', detail) if x.strip()]) if action == 'change' else 0
    append_jsonl(P('usage.jsonl'), {'type': 'outcome', 'gate': g, 'stage': S['gates'][g]['stage'], 'time': now(),
                                    'outcome': {'approve': 'approved', 'pick': 'approved', 'change': 'changed', 'stop': 'stopped'}[action],
                                    'options_chosen': 1 if action in ('pick', 'approve') else 0, 'fixes_named': fixes})
    if action == 'stop':
        st.update({'status': 'stopped', 'gate_pending': None})
    elif action == 'change':
        st.update({'status': 'working', 'fixes': detail, 'gate_pending': g})
    else:
        nxt = S['gates'][g]['next']
        if g == 'G5' and str(st.get('stage')) == '8':   # copy approved during page batches: production goes on
            nxt = 8
        st.update({'status': 'working', 'gate_pending': None, 'fixes': None})
        if g == 'G8':
            st.setdefault('batches_done', 0)
            st['batches_done'] += 1
            if '--last' in a:
                save_state(st); write_state_md()
                print(f'{g} {action}: last batch approved, packaging runs now')
                r = subprocess.run([sys.executable, J('tools', 'checkpoint.py')], cwd=J())
                return r.returncode
        if nxt is not None:
            st['stage'] = str(nxt)
        elif g == 'G10':   # the retro closes; the project returns to where it was
            st.update({'stage': st.pop('retro_from_stage', '9'), 'status': st.pop('retro_from_status', 'packaged')})
        else:
            st['status'] = 'done'
    save_state(st)
    write_state_md()
    print(f'{g} {action}' + (f' {detail}' if detail else '') + f': recorded. Next: stage {st.get("stage")} ({st["status"]}).'
          + (f' Options next gate: {st.get("options_next")}.' if opts else ''))
    print('Continue to the next stage in this session (run start.sh again), unless the context is long: then start a new session.')
    return 0


def cmd_credits(a):
    val = float(arg(a, '--credits'))
    brief = read_json(P('brief.json'), {})
    unit = (brief.get('budget') or {}).get('unit') or S['credit_unit']
    session = open(P('.session')).read().strip() if os.path.exists(P('.session')) else ''
    rows = usage_rows()
    entered = {r.get('session') for r in rows if r.get('type') == 'credits'}
    closes = [r for r in rows if r.get('type') == 'close' and r.get('session') == session]
    append_jsonl(P('usage.jsonl'), {'type': 'credits', 'session': session, 'credits': val, 'unit': unit, 'time': now()})
    tot = sum(r['words_read'] + r['words_written'] for r in closes) or 1
    for r in closes:   # split across this session's stages by words read and written
        share = val * (r['words_read'] + r['words_written']) / tot if len(closes) > 1 else val
        append_jsonl(P('usage.jsonl'), {'type': 'credits_split', 'rid': r['rid'], 'stage': r['stage'], 'session': session,
                                        'credits': round(share, 2), 'unit': unit})
    audit('credits', '', f'{val} {unit} session {session}' + (' (second entry this session)' if session in entered else ''))
    left = budget_left(brief)
    print(f'credits: {val:g} {unit} recorded for session {session or "?"} across {len(closes)} stage(s).'
          + (f' Budget left {round(left * 100)}%.' if left is not None else ''))
    if left is not None and left <= 1 - S['budget_warn']:
        print('warning: 80% or more of the project budget is used' if left > 0 else 'STOP: budget reached; gate.py --budget <n> to raise it')
    return 0


QUESTIONS = ['Own subject, or like the last project?', 'Designed page or placed page?', 'Where does the grid break, and why?',
             'One idea, visible in the first screen?', 'Eye path: first, second, third?', 'Is the typography doing the layout?',
             'Would a graphic arts professor pass this?', 'Structured and balanced: where is the rest, what holds the loud move?',
             'Could this sit beside the benchmark, finished, and suit the reader?', 'Can this reader act from here, and reach every page?']


def cmd_checklist(a):
    st = state()
    g = st.get('gate_pending') or arg(a, '--gate') or 'G6'
    ans = ['CD'] * len(QUESTIONS)
    u = read_json(P('out', 'uniq.json'))
    if u:
        ans[0] = 'pass' if u.get('pass') else 'FAIL: ' + '; '.join(u.get('hits', [])[:2])
    stc = read_json(P('structure.json'))
    if stc:
        br = [s['id'] for s in stc.get('sections', []) for b in (s.get('block') or []) if isinstance(b, dict) and b.get('bleed') not in (None, 'none')]
        nested = stc.get('grid', {}).get('nested') or []
        ans[2] = (f'bleeds: {", ".join(dict.fromkeys(br))}' if br else 'no bleed found') + (f'; nested: {len(nested)}' if nested else '') + ' (CD: why)'
        loud = [s['id'] for s in stc.get('sections', []) if s.get('rhythm') == 'loud']
        rest = [s['id'] for s in stc.get('sections', []) if s.get('rhythm') == 'rest']
        ans[7] = f'loud {len(loud)}, rest {len(rest)}'
    pr = read_json(P('out', 'pass.json'))
    if pr:
        f = pr.get('counts', {})
        ans[7] = (ans[7] + '; ' if ans[7] != 'CD' else '') + f"overlaps {f.get('overlap', 0)}, widows {f.get('widow', 0)} (CD: balance)"
    bm = [x for x in os.listdir(P('out', 'bench')) if x.endswith('.png')] if os.path.isdir(P('out', 'bench')) else []
    ans[8] = f'{len(bm)} benchmark capture(s) this project (CD)'
    if pr:
        ans[9] = f"reach: {pr.get('counts', {}).get('reach', 0)} page(s) with no way in (CD: main action and phone in the header?)"
    lines = [f'GATE CHECKLIST {g}'] + [f'{i + 1}. {q}: {ans[i]}' for i, q in enumerate(QUESTIONS)]
    ib = read_json(P('image-brief.json'), [])
    ph = [r['slot'] for r in (ib if isinstance(ib, list) else []) if r.get('status') == 'placeholder']
    if ph:
        lines.append(f'image slots still placeholder: {", ".join(ph[:8])}' + (' ...' if len(ph) > 8 else ''))
    write_atomic(P('out', f'checklist-{g.replace("/", "-")}.md'), '\n'.join(lines) + '\n')
    print('\n'.join(lines[:20]))
    return 0


def cmd_reopen(a):
    g = arg(a, '--reopen')
    if g not in S['reopen']:
        die(f'gate: cannot reopen {g}. Reopenable: {" ".join(S["reopen"])}')
    redo, keep = S['reopen'][g]
    st = S['gates'][g]['stage']
    cost = typical(st)
    print(f'reopen {g}\nredone: {redo}\nkept: {keep}\ntypical cost of stage {st}: {cost}')
    if '--confirm' not in a:
        print('Nothing changed. Rerun with --confirm to reopen.')
        return 0
    s = state()
    s.update({'stage': str(st), 'status': 'working', 'gate_pending': None, 'reopened': g})
    save_state(s)
    audit('reopen', g, arg(a, '--note', ''), arg(a, '--by', 'CD'))
    write_state_md()
    print(f'{g} reopened: stage {st} is current.')
    return 0


def cmd_retro(a):
    s = state()
    if s.get('status') not in ('packaged', 'stopped', 'done'):
        die(f'gate: a retro runs after packaging or a stop; this project is {s.get("status")} at stage {s.get("stage")}')
    s.update({'retro_from_stage': s.get('stage'), 'retro_from_status': s.get('status'), 'stage': '10', 'status': 'working', 'gate_pending': None})
    save_state(s)
    audit('retro', 'G10', arg(a, '--note', ''), arg(a, '--by', 'CD'))
    write_state_md()
    print('retro opened: stage 10 (studio director) is current; it ends at G10.')
    return 0


def cmd_override(a):
    check, reason = arg(a, '--override'), arg(a, '--reason')
    if not reason:
        die('gate: an override needs --reason "<why>"')
    ov = read_json(P('overrides.json'), {})
    ov.setdefault(check, []).append({'target': arg(a, '--target', '*'), 'reason': reason, 'time': now()})
    write_json(P('overrides.json'), ov)
    audit('override', state().get('gate_pending') or '', f'{check} {arg(a, "--target", "*")}: {reason}', arg(a, '--by', 'CD'))
    print(f'override recorded: {check} ({arg(a, "--target", "*")}). Reason logged.')
    return 0


def cmd_budget(a):
    b = read_json(P('brief.json'), {})
    b.setdefault('budget', {})['credits'] = float(arg(a, '--budget'))
    write_json(P('brief.json'), b)
    audit('budget', '', f'raised to {arg(a, "--budget")}')
    print(f'budget set to {arg(a, "--budget")}; budget left {round((budget_left(b) or 0) * 100)}%')
    return 0


def write_state_md():
    st, brief = state(), read_json(P('brief.json'), {})
    dec = st.get('decisions', [])[-6:]
    left = budget_left(brief)
    lines = [f'# {current_project()}: state', '',
             f'Written by gate.py {now()[:16]}Z. Lean mode: {"on" if brief.get("lean_mode") else "off"}.', '',
             f'- Stage: {st.get("stage", "0")} | status: {st.get("status", "working")}' + (f' | waiting on {st["gate_pending"]}' if st.get('gate_pending') else ''),
             f'- Last hand-off: {st.get("last_handoff", "none")}',
             f'- Options at next gate: {1 if brief.get("lean_mode") else st.get("options_next", S["options_default"])}',
             f'- Budget left: {("%d%%" % round(left * 100)) if left is not None else "no budget set"}']
    if st.get('fixes'):
        lines.append(f'- Fixes to apply: {st["fixes"]}')
    lines += ['', '## Decisions'] + ([f'- {d["time"][:10]} {d["gate"]}: {d["action"]} {d.get("detail") or ""} {d.get("note") or ""}'.rstrip() for d in dec] or ['- none yet'])
    lines += ['', '## Open'] + ([f'- {o}' for o in st.get('open', [])[:8]] or ['- none'])
    text = '\n'.join(lines) + '\n'
    while words(text) > S['words_caps']['state'] and len(lines) > 12:
        lines.pop(-1); text = '\n'.join(lines) + '\n'
    write_atomic(P('state.md'), text)


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    if '--event' in a:
        from kitlib import event
        i = a.index('--event')
        kind = a[i + 1] if i + 1 < len(a) else ''
        if kind not in ('call', 'fetch', 'render', 'spawn', 'image', 'read'):
            die('gate: --event call|fetch|render|spawn|image|read [n]')
        event(kind, int(a[i + 2]) if len(a) > i + 2 and a[i + 2].isdigit() else 1)
        return 0
    if '--typical' in a:
        print(typical(arg(a, '--typical'))); return 0
    if '--status' in a:
        write_state_md(); print(open(P('state.md')).read()); return 0
    for flag, fn in (('--ready', cmd_ready), ('--decide', cmd_decide), ('--credits', cmd_credits), ('--checklist', cmd_checklist),
                     ('--reopen', cmd_reopen), ('--retro', cmd_retro), ('--override', cmd_override), ('--budget', cmd_budget)):
        if flag in a:
            return fn(a)
    print(__doc__); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
