#!/usr/bin/env bash
# Cached install (one cache for the kit, $KIT_CACHE or ~/.cache/design-kit). The kit's own tools are pinned in
# deps/package-lock.json and installed with npm ci whenever the lock changes: axe-core, playwright and its Chromium,
# the greeking face. The current project's Fontsource faces (tokens*.json type.faces[].source = "fontsource:<package>",
# including each direction card's tokens-d<n>.json) are added on top without changing the lock. Python needs
# requirements.txt (Pillow). Later sessions reuse the cache. Prints one line.
K="$(cd "$(dirname "$0")/.." && pwd)"; cd "$K"
H="${KIT_HOME:-$(cd .. && pwd)}"
C="${KIT_CACHE:-$HOME/.cache/design-kit}"; mkdir -p "$C"
command -v node >/dev/null || { echo "setup: node is missing"; exit 1; }
did=""
if ! cmp -s deps/package-lock.json "$C/package-lock.json" || [ ! -d "$C/node_modules/playwright" ]; then
  cp deps/package.json deps/package-lock.json "$C/"
  ( cd "$C" && npm ci --silent --no-audit --no-fund >/dev/null 2>&1 ) || { echo "setup: npm ci failed in $C"; exit 1; }
  did=" pinned tools installed;"
fi
P="${KIT_PROJECT:-$(cat "$H/.current" 2>/dev/null)}"
fonts=""
if [ -n "$P" ] && ls "$H/projects/$P"/tokens*.json >/dev/null 2>&1; then
  fonts="$(python3 -c "
import glob,json,sys
s=set()
for f in glob.glob(sys.argv[1] + '/tokens*.json'):
    t=json.load(open(f))
    s|={x['source'].split(':',1)[1] for x in (t.get('type') or {}).get('faces',[]) if str(x.get('source','')).startswith('fontsource:')}
print(' '.join(sorted(s)))" "$H/projects/$P")"
fi
need=""; for p in $fonts; do [ -d "$C/node_modules/${p%@[0-9]*}" ] || need="$need $p"; done
if [ -n "$need" ]; then
  ( cd "$C" && npm i --no-save --silent --no-audit --no-fund $need >/dev/null 2>&1 ) || { echo "setup: npm install failed for:$need"; exit 1; }
  did="$did faces installed:$need;"
fi
echo "$C/node_modules" > "$H/.node"
# playwright's Chromium is downloaded once for the pinned playwright (shared by every kit on this machine)
NODE_PATH="$C/node_modules" node -e "process.exit(require('fs').existsSync(require('playwright').chromium.executablePath()) ? 0 : 1)" 2>/dev/null \
  || "$C/node_modules/.bin/playwright" install chromium >/dev/null 2>&1 \
  || { echo "setup: Chromium for playwright could not be installed (run $C/node_modules/.bin/playwright install chromium)"; exit 1; }
python3 -c "import PIL" 2>/dev/null || { echo "setup: Pillow is missing (python3 -m pip install -r $K/requirements.txt)"; exit 1; }
echo "setup: cache ready (${did:- reused;} $(echo $fonts | wc -w | tr -d ' ') project face(s))"
