# Never-ending design kit

A boilerplate agentic design studio for websites. Ten stages take a project from brief to package, each ending at a
creative-director (CD) gate. Agents do each stage's work; scripts check, build and measure; hooks enforce the gates.
Inspiration comes from a starter technique library plus live web sweeps for whatever the library lacks. Every build
starts from the same clean kit and never changes it. The kit is never versioned: `main` is the kit, and git keeps its
history.

## Install (Claude Code)
```
/plugin marketplace add <owner>/<repo>
/plugin install studio@never-ending-design-kit
```
Needs node, python3 with Pillow (`python3 -m pip install -r engine/requirements.txt`) and a network connection the
first time: setup installs the pinned tools (axe-core, playwright and its Chromium, fonts) into one cache
(`$KIT_CACHE`, default `~/.cache/design-kit`).

## Use
Open Claude Code in a studio workspace: a folder that holds `studio/` (your studio, a private repository) and
`projects/`. The first project creates `studio/` from `studio.example/` if there is none.

| Command | Does |
|---|---|
| `/studio:new <project>` | starts a project and runs the brief (S0), then stops at G0 |
| `/studio:next [project]` | runs the current stage with its agents, then stops at the next gate |
| `/studio:decide <gate> approve \| pick <n> \| fixes "..." \| stop` | records the CD's decision |
| `/studio:sweep <A\|B\|C> [project]` | one inspiration sweep: the libraries first, then the web |
| `/studio:status [project]` | where a project stands |
| `/studio:retro [project]` | the studio director's retro after packaging, ending at G10 |

Agents, one per role: inspiration scout, researcher, content strategist, layout designer, art director, copywriter,
comp designer, systems designer, production designer, studio director. Choice stages (concepts at S3, directions at
S4) run three agents in parallel. Hooks refuse a write the project's state does not allow (structure before S3,
tokens before S4, anything while a gate waits, the engine during a build), rebuild after page edits, log what is read
so usage is measured, and hold a stage until its gate has run.

Without Claude Code, `bin/studio` runs the same engine from any shell; `engine/adapters/` says how saving and
publishing work on each host (Claude Code, a claude.ai Project, any other agent).

## Layers
| Folder | Holds | Changes |
|---|---|---|
| `engine/` | stage prompts (P0, S0-S10, templates), rules, ref (with the starter library), primitives, tools, settings, pinned deps, adapters, fixtures | only at an approved G10, with the self-test passing |
| `agents/`, `commands/`, `skills/`, `hooks/`, `bin/`, `.claude-plugin/` | the Claude Code plugin: thin adapters over the engine | with the engine |
| `studio/` | one studio's taste, studio library, registry of past projects, history, `studio.json`: its own private repository, ignored here | at packaging (library, registry) and by the CD (taste) |
| `projects/` | one folder per project (ignored here) | at every gate |

`KIT_HOME` is the workspace holding `studio/` and `projects/`: Claude Code's project folder, else the folder beside
`engine/`. The engine never holds a studio or project value: `kitcheck.sh` fails on any name listed in
`studio/studio.json` identifiers, and on colours in the text of `engine/ref/` or `engine/rules/`.

## Compliance
Every project names its markets in `brief.json` `compliance{}` (S0): codes such as `EU`, `DE`, `UK`, `US-CA`,
`CA-QC`, `BR`, `ZA`, `AU`, `JP`, or `"all"` for all 34 in `engine/ref/compliance/jurisdictions.json`, plus the
sector, every outside service with its purpose and category, and what the site does with data (forms, sales,
accounts, a newsletter, children, selling or sharing). The rules are data, so a new market is a new row.
- `policy.py` prints what the markets require: pages, topics each page must cover, features and manual items.
- `comply.py --plan` (S2) fails a sitemap that leaves out a required page (privacy notice, accessibility statement,
  cookie policy, privacy choices, legal notice or Impressum, terms, returns, PAIA manual, 404).
- `comply.py` (S8, S9) checks the built site: required pages and their topics; footer links on every page;
  the consent banner in a real browser (nothing outside "necessary" loads before a choice, reject is as easy as
  accept, no ticked boxes, the choice is remembered and reopens from the footer, Global Privacy Control turns
  marketing off); forms (privacy link, nothing ticked); every outside host declared; markup a strict Content
  Security Policy allows; `security.txt`; canonical links, favicon, `robots.txt` and `sitemap.xml`.
- `build.py` adds the legal footer, the kit's consent banner when the site tracks, and writes `_headers` (CSP, HSTS
  and the rest), `security.txt`, `robots.txt` and `sitemap.xml`. Right-to-left languages get `dir="rtl"`.
- Accessibility: axe-core at WCAG 2.2 AAA by default (`"wcag": "AA"` for the AA floor), plus 44px targets, focus,
  reduced motion, reflow at 320px, reading level, layout shift and largest paint.
- Packaging blocks while `comply.py` fails. `out/package/compliance/` holds the checklist (laws, every requirement,
  manual items), a data inventory, a WCAG 2.2 conformance report template and the same headers for Netlify,
  Cloudflare Pages, nginx, Apache and Vercel.

The kit checks that pages, links and behaviour exist and work. It is not legal advice: policy pages are drafts
until a lawyer approves them, and `compliance.legal_review` stays `pending` (a client item at packaging) until then.

## Inspiration
- `engine/ref/library.md`: the starter library, 122 techniques with public sources, by section (page forms, grid,
  type, colour, image, texture, motion, data, proof, conversion, notation, avoid).
- `studio/library.md`: the studio's own rows and Proven marks, added to at packaging.
- Sweeps A (subject, S1), B (structure, S3) and C (aesthetic, S4): `refs.py --gaps` names the thin sections, the
  inspiration scout searches the web for those, opens every page it cites, and records one technique per reference in
  the project's `references.jsonl` (`refs.py --check`). References the build used go to the studio library.
- `uniq.py` checks every option against the studio's past projects and against common tool defaults
  (`engine/ref/defaults.json`: the faces, accents and trend looks AI design tools reach for), so the first build is
  checked too.
- `ref/motion/` (when and how things move, the one motion moment per page) and `ref/copy/` (copy tells, worst-case
  content) feed the direction, copy and system stages. img2threejs is documented there as an optional 3D add-on.
- `studio browse` drives the pinned Chromium through the Playwright agent CLI: open a benchmark or a built page,
  hover, Tab, scroll and snapshot it, with files kept in the project's `out/browse/`.

## Craft checks
`pass.py` measures every page at 1440, 768, 390 and 320: accessibility (axe-core), widows, overlaps, targets, meta,
headings, code standard, page weight, copy expansion, reading level, layout shift and largest paint, plus:
- **slop**: the impeccable detector (62 deterministic rules for generated-looking UI, pinned, telemetry off), at 1440
  and 390, one check per rule so the CD can override one at a time;
- **copy**: copy tells (`tells.py`): stand-in words, stock lines, residue fail; capped devices warn;
- **stress**: a 30-letter compound and a long email in every heading, text block and link at 320px;
- **spacing**: the WCAG 1.4.12 text-spacing overrides at 390px;
- **keyboard**: Tab through every page: skip link first, every control reached, no trap, a visible ring, and the
  focused control never under a fixed bar;
- **motion-css** (`--system`): no transition on "all" or layout properties, no `scale(0)`, no ease-in, interface
  transitions at 500ms or less.

`designmd.py` exports the system as a nine-section `DESIGN.md` that design agents read; the package includes it.

## Changing the kit
After an approved G10 (or a CD instruction): start a kit session with `KIT_DEV=1` (the hooks otherwise refuse engine
edits), work on a branch, run `bash engine/tools/selftest.sh` (all steps pass; CI runs it on macOS and Linux), add a
dated line to `engine/MANIFEST` [changes], and merge. `claude plugin validate .` checks the plugin.
`CONTRIBUTING.md` has the full path, including how to add a jurisdiction; `SECURITY.md` says how to report a
vulnerability; `CODE_OF_CONDUCT.md` applies to everyone taking part. CI also audits the pinned dependencies
(`npm audit`, `pip-audit`) and publishes a CycloneDX SBOM; Dependabot proposes updates weekly.

## Supported platforms
| | Supported |
|---|---|
| Hosts | Claude Code (plugin), a claude.ai Project, any agent or shell via `bin/studio` |
| Operating systems | macOS and Linux (CI runs both); Windows through WSL |
| Runtimes | Node 20 or later; Python 3.9 or later with Pillow from `engine/requirements.txt` |
| Automated browser | Chromium (Playwright, pinned). Safari, Firefox and Edge are manual checks in the handover |
| Built sites | Static HTML and one CSS file; any static host that can send headers (Netlify, Cloudflare Pages, Vercel, nginx, Apache) |

## Images
None in the kit. Captures, roughs, boards, renders and stock photos live in each project's `out/` and `images/` and
are never packed. The self-test draws its one fixture photo at run time.

## Licence
Code is under the Apache License 2.0 (`LICENSE`); prompts, rules, reference text and agent and command text are under
Creative Commons Attribution 4.0 (`LICENSE-CONTENT`). `NOTICE` says which folders fall under which, and covers
third-party sources.
