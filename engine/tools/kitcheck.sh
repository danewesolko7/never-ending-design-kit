#!/usr/bin/env bash
# Prove the kit is whole before any stage runs: every tool in MANIFEST exists and parses, every prompt and template
# is present and under its word cap, the kit holds no images, the setup cache has axe-core, the studio overlay is
# complete, and the engine holds no studio or project value.
# Exit 1 on any failure: stop and tell the creative director; never rewrite a tool by hand.
K="$(cd "$(dirname "$0")/.." && pwd)"; cd "$K"; fail=0
H="${KIT_HOME:-$(cd .. && pwd)}"; export KIT_H="$H"
say() { printf '%-8s %s\n' "$1" "$2"; fail=1; }
[ -f MANIFEST ] || say MISSING MANIFEST
for t in $(sed -n '/^\[tools\]/,/^\[/p' MANIFEST | grep -v '^\['); do
  f="tools/$t"; [ -f "$f" ] || { say MISSING "$f"; continue; }
  case "$t" in
    *.py) python3 -m py_compile "$f" 2>/dev/null || say BROKEN "$f" ;;
    *.js) node --check "$f" 2>/dev/null || say BROKEN "$f" ;;
    *.sh) bash -n "$f" 2>/dev/null || say BROKEN "$f" ;;
  esac
done
for p in P0 S0 S1 S2 S3 S4 S5 S6 S7 S8 S9 S10; do
  f="prompts/$p.md"; [ -f "$f" ] || { say MISSING "$f"; continue; }
  n=$(sed '/^<!--/d' "$f" | wc -w); [ "$n" -le 250 ] || say LONG "$f is $n words (cap 250)"
done
for f in prompts/templates.md prompts/role-template.md rules/rules.md settings.json primitives/primitives.css ref/catalogue.json \
         primitives/consent.js primitives/consent.css primitives/consent.json ref/compliance/jurisdictions.json ref/compliance/wcag22.json \
         ref/motion/INDEX.md ref/copy/INDEX.md; do
  [ -f "$f" ] || say MISSING "$f"; done
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['jurisdictions'] and d['requirements']" ref/compliance/jurisdictions.json 2>/dev/null \
  || say BROKEN "ref/compliance/jurisdictions.json (not JSON, or no jurisdictions or requirements)"
for f in studio.json taste.md taste-checks.md library.md registry/fingerprints.jsonl registry/usage-log.jsonl; do
  [ -f "$H/studio/$f" ] || say MISSING "studio/$f (copy it from studio.example/)"; done
[ -f "$H/studio/taste-checks.md" ] && { n=$(wc -w < "$H/studio/taste-checks.md"); [ "$n" -le 150 ] || say LONG "studio/taste-checks.md is $n words (cap 150)"; }
[ -d fixtures/sample ] || say MISSING fixtures/sample
for f in adapters/claude-code.md adapters/claude-ai-project.md adapters/other-agents.md deps/package-lock.json; do
  [ -f "$f" ] || say MISSING "$f"; done
# the plugin: manifest and hooks parse, every stage agent and command exists and is named for its file, the launcher runs
for f in ../.claude-plugin/plugin.json ../.claude-plugin/marketplace.json ../hooks/hooks.json; do
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null || say BROKEN "$f (missing or not JSON)"; done
for a in inspiration-scout researcher content-strategist layout-designer art-director copywriter comp-designer \
         systems-designer production-designer studio-director; do
  grep -q "^name: $a$" "../agents/$a.md" 2>/dev/null || say MISSING "agents/$a.md (or its name line)"; done
for c in new next decide status sweep retro; do [ -f "../commands/$c.md" ] || say MISSING "commands/$c.md"; done
[ -x ../bin/studio ] || say MISSING "bin/studio (executable)"
NM="$(cat "$H/.node" 2>/dev/null)"; [ -n "$NM" ] && [ -d "$NM/axe-core" ] || say MISSING "setup cache (axe-core): run bash tools/setup.sh"
for x in "$H/studio/registry/thumbs" "$H/studio/registry/library"; do [ -e "$x" ] && say STRAY "$x: the kit keeps no images (move captures to projects/<p>/out/)"; done
# boundary: the engine and the example overlay hold no studio or project value (names from studio/studio.json;
# hex colours in the text of ref/ and rules/)
leaks="$(python3 - <<'PY'
import json, os, re
try:
    ids = [x for x in json.load(open(os.path.join(os.environ['KIT_H'], 'studio', 'studio.json'))).get('identifiers', []) if x.strip()]
except (OSError, ValueError):
    ids = []
pat = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(x) for x in ids) + r')(?![\w-])', re.I) if ids else None
for d, dirs, fs in [w for top in ('.', '../studio.example', '../agents', '../commands', '../skills', '../hooks', '../bin') for w in os.walk(top)]:
    dirs[:] = [x for x in dirs if x not in ('node_modules', 'out', '__pycache__')]
    for f in fs:
        p = os.path.normpath(os.path.join(d, f))
        if not (f.endswith(('.md', '.json', '.jsonl', '.py', '.sh', '.js', '.html', '.css')) or d.endswith('bin')) or p == 'MANIFEST':
            continue
        t = open(p, encoding='utf-8', errors='ignore').read()
        m = pat.search(t) if pat else None
        if m:
            print(f'{p}: names "{m.group(0)}"')
        if p.startswith(('ref/', 'rules/')) and p.endswith('.md'):   # data files such as ref/defaults.json may hold colours
            h = re.search(r'#[0-9a-fA-F]{6}\b', t)
            if h:
                print(f'{p}: holds the colour {h.group(0)}')
PY
)"
[ -n "$leaks" ] && while IFS= read -r l; do say LEAK "$l (move it to studio/ or a project)"; done <<< "$leaks"
if [ $fail = 0 ]; then echo "kitcheck: kit whole"; else echo "kitcheck: FAILED"; fi
exit $fail
