#!/usr/bin/env bash
# Engine tests at no credit cost: every tool against the 3-page fixture with golden files, on a throwaway copy.
# One PASS or FAIL line per step, grouped by build phase; exit 1 if any step fails. Run before saving any kit change.
K="$(cd "$(dirname "$0")/.." && pwd)"; KR="$(cd "$K/.." && pwd)"
T="$(mktemp -d)"; W="$T/kit"; fails=0; trap 'rm -rf "$T"' EXIT
# portable in-place edit (GNU and BSD sed differ on -i)
sedi() { local e="$1"; shift; for f; do sed "$e" "$f" > "$f.sedi" && mv "$f.sedi" "$f"; done; }; export -f sedi
step() { local name="$1"; shift; if out="$("$@" 2>&1)"; then echo "PASS  $name"; else echo "FAIL  $name"; echo "$out" | tail -4 | sed 's/^/      /'; fails=$((fails+1)); fi; }
[ -f "$KR/.node" ] || { echo "selftest: run tools/setup.sh first"; exit 1; }
# anchored excludes (tar patterns are not anchored on BSD: ./studio would also drop bin/studio)
mkdir -p "$W" && rsync -a --exclude=/projects --exclude=/studio --exclude=/engine/out --exclude=/.current --exclude=/.git "$KR/" "$W/"
# a throwaway studio from the example overlay, so the test never reads or writes the real studio
cd "$W"; cp -R studio.example studio; mkdir -p projects; cp -r engine/fixtures/sample projects/fx
cp engine/fixtures/registry.jsonl studio/registry/fingerprints.jsonl; : > studio/registry/usage-log.jsonl
# the kit holds no images: the fixture's one photo is drawn here, so the golden files test the real-image path
mkdir -p projects/fx/images && python3 -c "from PIL import Image; Image.new('RGB', (1200, 1500), (120, 110, 100)).save('projects/fx/images/hero.jpg', quality=60)"
export NODE_PATH="$(cat .node)" KIT_HOME="$W"; cd engine
python3 - <<'PY'
import json; f='../projects/fx/brief.json'; d=json.load(open(f)); d['project']='fx'; json.dump(d, open(f,'w'))
PY
export KIT_PROJECT=fx
H=../projects/fx/docs/stages
handoff() { cat > "$H/$1.md" <<HO
stage: $1 | status: done | date: 2026-11-18
decided: fixture stage $1
new files: brief.json
open: none
next reads: brief.json
decide: $2: approve this? | choices: approve / change / stop | unlocks: next
HO
}
echo "-- phase 1: control tools"
step "start.sh --check opens no usage record"        bash -c 'bash tools/start.sh fx --no-setup --check | grep -q "check only" && ! test -s ../projects/fx/usage.jsonl'
step "start.sh opens a session and a usage record"   bash -c 'bash tools/start.sh fx --no-setup | grep -q "stage 0" && grep -q "\"type\": \"open\"" ../projects/fx/usage.jsonl'
step "start.sh reuses the open record (no strays)"   bash -c 'bash tools/start.sh fx --no-setup >/dev/null && test "$(grep -c "\"type\": \"open\"" ../projects/fx/usage.jsonl)" = 1 && ! grep -q abandoned ../projects/fx/usage.jsonl'
step "start.sh offers 3 options (1 in lean mode)"   bash -c 'bash tools/start.sh fx --no-setup | grep -q "options this stage: 1 (lean mode)" && cp ../projects/fx/brief.json ../b.json && sedi "s/\"lean_mode\": true/\"lean_mode\": false/" ../projects/fx/brief.json && bash tools/start.sh fx --no-setup | grep -q "options this stage: 3"; r=$?; cp ../b.json ../projects/fx/brief.json; exit $r'
handoff 0 G0
step "gate.py --ready writes packet, state and usage"  bash -c 'python3 tools/gate.py --ready | grep -q "^usage: S0" && test -f ../projects/fx/out/packet.md && test -f ../projects/fx/state.md && grep -q "\"type\": \"close\"" ../projects/fx/usage.jsonl'
step "gate packet names the gate once"              bash -c 'grep -q "^decide: G0: approve this?" ../projects/fx/out/packet.md && ! grep -q "G0: G0:" ../projects/fx/out/packet.md'
step "gate.py --decide records the audit trail"      bash -c 'python3 tools/gate.py --decide G0 --approve --note fixture && grep -q "\"action\": \"decide\"" ../projects/fx/audit.jsonl && grep -q "\"stage\": \"1\"" ../projects/fx/state.json'
step "gate.py --credits records and splits"          bash -c 'python3 tools/gate.py --credits 1200 && grep -q credits_split ../projects/fx/usage.jsonl && grep -q "\"action\": \"credits\"" ../projects/fx/audit.jsonl'
python3 -c "print('stage: 1 | status: done\ndecided: '+'word '*300+'\nnew files: x\nopen: none\nnext reads: x\ndecide: G1: ok?')" > "$H/1.md"
step "gate.py refuses an over-cap hand-off"           bash -c '! python3 tools/gate.py --ready'
handoff 1 G1; echo "token = sk-abcdefghijklmnopqrstuvwxyz123456" >> "$H/1.md"
step "gate.py refuses a secret pattern"               bash -c '! python3 tools/gate.py --ready'
handoff 1 G1
step "gate.py --checklist writes 10 questions"        bash -c 'test "$(python3 tools/gate.py --checklist | grep -cE "^[0-9]+\.")" = 10'
step "gate.py --reopen lists the cost, changes nothing" bash -c 'python3 tools/gate.py --reopen G2 | grep -q "redone:"'
step "pass.py passes the fixture site"                python3 tools/pass.py --all
cp -r ../projects/fx ../projects/fx.bak
plant() { rm -rf ../projects/fx; cp -r ../projects/fx.bak ../projects/fx; }
python3 - <<'PY'
import json; f='../projects/fx/pages/about.json'; d=json.load(open(f)); d['sections'].append({"id":"s9","partial":"widow","text":{"raw":"aaaa bbbb cccc dddd eeeeeeeeeeeee"}}); json.dump(d,open(f,'w'))
open('../projects/fx/partials/widow.html','w').write('<section class="wd-sec" id="wd"><p class="wd-p">{{raw}}</p></section>')
open('../projects/fx/partials/widow.css','w').write('.wd-p{font-family:monospace;width:20ch;font-size:16px}')
PY
step "pass.py fails a planted widow"                  bash -c 'python3 tools/pass.py --page about | grep -q "FAIL widow"'
plant; sedi 's/"ink-2": "#454b52"/"ink-2": "#a0a0a0"/' ../projects/fx/tokens.json
step "pass.py fails a planted contrast error"         bash -c 'python3 tools/pass.py --page home | grep -q "color-contrast"'
plant; python3 -c "import json;f='../projects/fx/pages/about.json';d=json.load(open(f));d['meta'].pop('description');json.dump(d,open(f,'w'))"
step "pass.py fails missing meta"                     bash -c 'python3 tools/pass.py --page about | grep -q "FAIL meta"'
plant; python3 -c "import json;f='../projects/fx/brief.json';d=json.load(open(f));d['budget']['page_weight_mb']=0.01;json.dump(d,open(f,'w'))"
step "pass.py fails an over-weight page"              bash -c 'python3 tools/pass.py --page home | grep -q "FAIL weight"'
plant; python3 -c "
import json;f='../projects/fx/pages/about.json';d=json.load(open(f));d['sections'].append({'id':'s9','partial':'widow','text':{'raw':'aaaa bbbb cccc dddd eeeeeeeeeeeee'}});json.dump(d,open(f,'w'))
open('../projects/fx/partials/widow.html','w').write('<section class=\"wd-sec\" id=\"wd\"><p class=\"wd-p\">{{raw}}</p></section>')
open('../projects/fx/partials/widow.css','w').write('.wd-p{font-family:monospace;width:20ch;font-size:16px}')"
step "pass.py honours a CD override"                  bash -c 'python3 tools/gate.py --override pass --target widow --reason test >/dev/null && python3 tools/pass.py --page about | grep -q "OVERRIDDEN widow"'
plant; sedi 's/"ink-2": "#454b52"/"ink-2": "#666666"/' ../projects/fx/tokens.json
step "pass.py checks AAA, or AA when the brief says"  bash -c 'python3 tools/pass.py --page home >/dev/null; grep -q color-contrast-enhanced ../projects/fx/out/reports/pass-page.md && python3 -c "import json;f=\"../projects/fx/brief.json\";d=json.load(open(f));d[\"wcag\"]=\"AA\";json.dump(d,open(f,\"w\"))" && python3 tools/pass.py --page home >/dev/null; ! grep -q color-contrast ../projects/fx/out/reports/pass-page.md'
plant
step "gate.py: copy approved in S8 keeps production" bash -c 'python3 -c "import json;f=\"../projects/fx/state.json\";d=json.load(open(f));d.update(stage=\"8\",status=\"waiting\",gate_pending=\"G5\");json.dump(d,open(f,\"w\"))" && python3 tools/gate.py --decide G5 --approve >/dev/null && grep -q "\"stage\": \"8\"" ../projects/fx/state.json'
step "setup.sh installs from the pinned lock"         bash -c 'cmp -s deps/package-lock.json "$(dirname "$(cat ../.node)")/package-lock.json"'
plant; rm -rf ../projects/fx.bak
echo "-- phase 2: page data pipeline"
step "build.py matches the golden files"              bash -c 'python3 tools/build.py --all && for f in home about visit specimen; do cmp -s ../projects/fx/out/site/$f.html fixtures/sample/golden/$f.html || exit 1; done && cmp -s ../projects/fx/out/site/site.css fixtures/sample/golden/site.css'
step "build.py writes no inline styles"               bash -c '! grep -l "style=" ../projects/fx/out/site/*.html'
step "build.py fails a schema error"                  bash -c 'echo "{\"id\":\"bad\",\"title\":\"x\",\"sections\":[{\"id\":\"s\",\"primitive\":\"nope\"}]}" > ../projects/fx/pages/bad.json; ! python3 tools/build.py --all; r=$?; rm ../projects/fx/pages/bad.json; exit $r'
step "a text change touches only page JSON output"    bash -c 'python3 tools/build.py --all >/dev/null && cp -r ../projects/fx/out/site $PWD/../before && sedi "s/A quiet room three streets from the park/A quiet room near the park/" ../projects/fx/pages/home.json && python3 tools/build.py --all >/dev/null && ! cmp -s ../projects/fx/out/site/home.html ../before/home.html && cmp -s ../projects/fx/out/site/site.css ../before/site.css && cmp -s ../projects/fx/out/site/about.html ../before/about.html'
step "greek.py renders a rough from structure.json"   bash -c 'python3 tools/greek.py && test -f ../projects/fx/out/rough/png/home-1440.png && test -f ../projects/fx/out/rough/png/home-390-m.png'
step "greek.py --name renders one rough per concept"  bash -c 'cp ../projects/fx/structure.json ../projects/fx/structure-2.json && python3 tools/greek.py structure-2.json --name c2 && test -f ../projects/fx/out/rough/png/c2-1440-m.png'
step "build.py --board builds a direction board"      bash -c 'cp ../projects/fx/tokens.json ../projects/fx/tokens-d1.json && python3 tools/build.py home --board d1 --tokens tokens-d1.json && test -f ../projects/fx/out/boards/d1/home.html && test -f ../projects/fx/out/boards/d1/site.css && node tools/shot.js ../projects/fx/out/boards/d1/home.html --widths 1440,390 --out ../projects/fx/out/boards/png/d1 >/dev/null && test -f ../projects/fx/out/boards/png/d1/home-1440-m.png'
step "milestone.py frames concepts and directions"    bash -c 'python3 tools/milestone.py G3a | grep -q "^publish:" && python3 tools/milestone.py G3b/G4a | grep -q "^publish:"'
step "pass.py --rough measures the rough"             python3 tools/pass.py --rough
step "contact.py makes a sheet of 1000px or less"     bash -c 'python3 tools/contact.py ../projects/fx/out/sheet.png "../projects/fx/out/rough/png/home-*-m.png" && python3 -c "from PIL import Image;i=Image.open(\"../projects/fx/out/sheet.png\");assert max(i.size)<=1000"'
step "fontcheck.py passes with licences"              python3 tools/fontcheck.py
echo "-- phase 3: uniqueness and registry"
step "fixture registry holds six projects"              bash -c 'test "$(python3 -c "import json;print(len({json.loads(l)[\"project\"] for l in open(\"../studio/registry/fingerprints.jsonl\") if l.strip()}))")" -ge 6'
step "seed.py lists unused ground"                    bash -c 'python3 tools/seed.py | grep -q "unused page forms"'
step "uniq.py fails a deliberate repeat"              bash -c '! python3 tools/uniq.py fingerprints/card-1.json'
step "uniq.py passes a new fingerprint"               python3 tools/uniq.py fingerprints/card-2.json
step "uniq.py honours a logged override"              bash -c 'python3 tools/gate.py --override uniq --target card-1 --reason test && python3 tools/uniq.py fingerprints/card-1.json | grep -q OVERRIDDEN && rm ../projects/fx/overrides.json'
step "uniq.py fails a stock default look"            bash -c 'python3 -c "import json;d=json.load(open(\"../projects/fx/fingerprints/card-2.json\"));d.update(type_pair=\"Inter / Inter\",hues=[\"#6366f1\",\"#ffffff\"],moves=[\"bento grid\"]);json.dump(d,open(\"../projects/fx/fingerprints/stock.json\",\"w\"))" && ! python3 tools/uniq.py fingerprints/stock.json > ../stock.out; r=$?; grep -c "^FAIL default" ../stock.out | grep -q 3 && test $r = 0; r=$?; rm -f ../projects/fx/fingerprints/stock.json; exit $r'
step "uniq.py with no history checks tool defaults"  bash -c 'cp ../studio/registry/fingerprints.jsonl ../fp.bak && : > ../studio/registry/fingerprints.jsonl && python3 tools/uniq.py fingerprints/card-2.json | grep -q "tool defaults only"; r=$?; cp ../fp.bak ../studio/registry/fingerprints.jsonl; exit $r'
step "refs.py --gaps lists thin library sections"    bash -c 'python3 tools/refs.py --gaps --sections 1-11 | grep -q "refs gaps:"'
step "refs.py --check passes the fixture sweep"      python3 tools/refs.py --check --sweep C
step "refs.py --check fails a bad reference"         bash -c 'cp ../projects/fx/references.jsonl ../refs.bak && echo "{\"sweep\":\"C\",\"section\":3,\"title\":\"x\",\"url\":\"notalink\",\"seen\":\"2026-11-18\",\"technique\":\"y\"}" >> ../projects/fx/references.jsonl && python3 tools/refs.py --check --sweep C | grep -q "not a web link"; r=$?; cp ../refs.bak ../projects/fx/references.jsonl; exit $r'
step "uniq.py --pages catches a repeated technique"   bash -c 'echo "{\"scope\":\"page\",\"moves\":[\"pressed leaf cut-outs\"]}" > ../projects/fx/fingerprints/page-a.json; echo "{\"scope\":\"page\",\"moves\":[\"pressed-leaf cut-out\"]}" > ../projects/fx/fingerprints/page-b.json; ! python3 tools/uniq.py --pages; r=$?; rm ../projects/fx/fingerprints/page-*.json; exit $r'
echo "-- phase 4: prompts, card and caps"
step "kitcheck.sh: prompts within caps, no images"   bash tools/kitcheck.sh
step "kitcheck.sh fails a studio name in the engine or example" bash -c 'python3 -c "import json;f=\"../studio/studio.json\";d=json.load(open(f));d[\"identifiers\"]=[\"Plantname\"];json.dump(d,open(f,\"w\"))" && echo "Plantname" > ../studio.example/leak.md && bash tools/kitcheck.sh | grep -q "LEAK.*studio.example/leak.md.*Plantname" && rm ../studio.example/leak.md && echo "Plantname" > ref/leak.md && bash tools/kitcheck.sh | grep -q "LEAK.*Plantname"; r=$?; rm -f ref/leak.md ../studio.example/leak.md; exit $r'
for s in 1 2; do handoff $s G$s; sleep 1; python3 tools/gate.py --ready >/dev/null; python3 tools/gate.py --decide G$s --approve >/dev/null; bash tools/start.sh fx --no-setup >/dev/null; done
step "dry run G0 to G2 stays within caps"             bash -c '! grep -q "caps_hit\": \[\"" ../projects/fx/usage.jsonl'
echo "-- phase 5: plugin, launcher and hooks"
export W
hk() { python3 tools/hook.py "$1"; }; export -f hk
setst() { python3 -c "import json,sys;f='../projects/fx/state.json';d=json.load(open(f));d.update(json.loads(sys.argv[1]));json.dump(d,open(f,'w'))" "$1"; }; export -f setst
cp ../projects/fx/state.json ../state.bak
step "studio launcher finds the engine and runs tools" bash -c '../bin/studio paths | grep -q "^engine  /.*/kit/engine$" && KIT_PROJECT=fx ../bin/studio tool refs.py --gaps --sections 1-2 | grep -q "refs gaps:"'
step "hook refuses a file before its stage"           bash -c 'setst "{\"stage\":\"2\",\"status\":\"working\"}" && echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/tokens.json\"}}" | hk pre | grep -q "opens at stage 4"'
step "hook allows a file its stage opens"             bash -c 'setst "{\"stage\":\"2\",\"status\":\"working\"}" && test -z "$(echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/content.json\"}}" | hk pre)"'
step "hook refuses writes while a gate waits"         bash -c 'setst "{\"stage\":\"6\",\"status\":\"waiting\",\"gate_pending\":\"G6\"}" && echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/pages/home.json\"}}" | hk pre | grep -q "waiting for the creative director at G6"'
step "hook refuses tool-owned files and the engine"   bash -c 'setst "{\"stage\":\"6\",\"status\":\"working\"}" && echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/state.json\"}}" | hk pre | grep -q "written by the kit tools" && echo "{\"tool_input\":{\"file_path\":\"$W/engine/rules/rules.md\"}}" | hk pre | grep -q "approved G10" && test -z "$(echo "{\"tool_input\":{\"file_path\":\"$W/engine/rules/rules.md\"}}" | KIT_DEV=1 hk pre)"'
step "hook does nothing outside a studio workspace"   bash -c 'mkdir -p ../elsewhere && test -z "$(echo "{\"tool_input\":{\"file_path\":\"/tmp/x.json\"}}" | KIT_HOME="$W/elsewhere" hk pre)"'
step "hook measures reads and images"                 bash -c 'echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/brief.json\"}}" | hk read && echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/out/sheet.png\"}}" | hk read && grep -q "\"kind\": \"read\"" ../projects/fx/events.jsonl && grep -q "\"kind\": \"image\"" ../projects/fx/events.jsonl'
step "hook reports a page that no longer builds"      bash -c 'setst "{\"stage\":\"6\",\"status\":\"working\"}" && cp ../projects/fx/pages/home.json ../home.bak && echo "{\"id\":\"home\",\"title\":\"x\",\"sections\":[{\"id\":\"s\",\"primitive\":\"nope\"}]}" > ../projects/fx/pages/home.json && echo "{\"tool_input\":{\"file_path\":\"$W/projects/fx/pages/home.json\"}}" | hk post | grep -q "build.py failed"; r=$?; cp ../home.bak ../projects/fx/pages/home.json; exit $r'
step "hook holds a stage until its gate has run"      bash -c 'setst "{\"stage\":\"6\",\"status\":\"working\"}" && sleep 1 && touch ../projects/fx/docs/stages/6.md && KIT_PROJECT=fx hk stop <<< "{}" | grep -q "gate has not run" && test -z "$(KIT_PROJECT=fx hk stop <<< "{\"stop_hook_active\":true}")"; r=$?; rm -f ../projects/fx/docs/stages/6.md; exit $r'
cp ../state.bak ../projects/fx/state.json
echo "-- packaging"
step "checkpoint.py blocks on a [NEW] figure"         bash -c 'sedi "s/Story time/[NEW] 40 children at story time/" ../projects/fx/pages/home.json; ! python3 tools/checkpoint.py; r=$?; sedi "s/\[NEW\] 40 children at story time/Story time/" ../projects/fx/pages/home.json; exit $r'
step "checkpoint.py blocks on a [NEW: note] figure"  bash -c 'sedi "s/Story time/[NEW: count] 40 children at story time/" ../projects/fx/pages/home.json; ! python3 tools/checkpoint.py; r=$?; sedi "s/\[NEW: count\] 40 children at story time/Story time/" ../projects/fx/pages/home.json; exit $r'
step "pass.py --all fails a page nobody can reach"    bash -c 'cp ../projects/fx/pages/about.json ../projects/fx/pages/lost.json && python3 -c "import json;f=\"../projects/fx/pages/lost.json\";d=json.load(open(f));d[\"id\"]=\"lost\";d[\"nav\"]=False;d.setdefault(\"meta\",{})[\"title\"]=\"Lost\";d[\"meta\"][\"description\"]=\"Lost page\";json.dump(d,open(f,\"w\"))" && python3 tools/pass.py --all | grep -q "FAIL reach: lost"; r=$?; rm -f ../projects/fx/pages/lost.json ../projects/fx/out/site/lost.html; python3 tools/build.py --all >/dev/null; exit $r'
step "checkpoint.py packages and records"             bash -c 'python3 tools/checkpoint.py && test -f ../projects/fx/out/package/index.html && ! test -e ../studio/registry/thumbs && grep -q "\"project\": \"fx\"" ../studio/registry/fingerprints.jsonl && grep -q "\"type\": \"stage\"" ../studio/registry/usage-log.jsonl'
step "checkpoint.py promotes used references once"   bash -c 'n1=$(wc -l < ../studio/registry/usage-log.jsonl) && python3 tools/checkpoint.py >/dev/null && test "$(grep -c "Index-card headings" ../studio/library.md)" = 1 && test "$(wc -l < ../studio/registry/usage-log.jsonl)" = "$n1"'
step "gate.py --retro opens S10; G10 closes it"      bash -c 'python3 tools/gate.py --retro >/dev/null && grep -q "\"stage\": \"10\"" ../projects/fx/state.json && python3 tools/gate.py --decide G10 --approve >/dev/null && grep -q "\"status\": \"packaged\"" ../projects/fx/state.json'
step "pack.py round trip (kit + project)"             bash -c 'python3 tools/pack.py --kit ../k.py >/dev/null && python3 tools/pack.py fx ../p.py >/dev/null && cd .. && python3 k.py fresh >/dev/null && python3 p.py fresh >/dev/null && test -f fresh/engine/tools/gate.py && test -f fresh/projects/fx/pages/home.json'
step "kit pack carries library and registry, no images" bash -c 'cd .. && test -f fresh/studio/library.md && grep -q "\"project\": \"fx\"" fresh/studio/registry/fingerprints.jsonl && ! find fresh -path fresh/projects -prune -o -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) -print | grep -q .'
step "project pack carries no photos"                 bash -c 'mkdir -p ../projects/fx/images && cp ../projects/fx/out/rough/png/home-1440-m.png ../projects/fx/images/x.png && python3 tools/pack.py fx ../p2.py >/dev/null && ! grep -q "images/x.png" ../p2.py'
echo
if [ $fails = 0 ]; then echo "selftest: all steps pass"; else echo "selftest: $fails step(s) failed"; fi
exit $((fails > 0))
