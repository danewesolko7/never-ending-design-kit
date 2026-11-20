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

## Inspiration
- `engine/ref/library.md`: the starter library, 122 techniques with public sources, by section (page forms, grid,
  type, colour, image, texture, motion, data, proof, conversion, notation, avoid).
- `studio/library.md`: the studio's own rows and Proven marks, added to at packaging.
- Sweeps A (subject, S1), B (structure, S3) and C (aesthetic, S4): `refs.py --gaps` names the thin sections, the
  inspiration scout searches the web for those, opens every page it cites, and records one technique per reference in
  the project's `references.jsonl` (`refs.py --check`). References the build used go to the studio library.
- `uniq.py` checks every option against the studio's past projects and against common tool defaults
  (`engine/ref/defaults.json`), so the first build is checked too.

## Changing the kit
After an approved G10 (or a CD instruction): start a kit session with `KIT_DEV=1` (the hooks otherwise refuse engine
edits), work on a branch, run `bash engine/tools/selftest.sh` (all steps pass; CI runs it on macOS and Linux), add a
dated line to `engine/MANIFEST` [changes], and merge. `claude plugin validate .` checks the plugin.

## Images
None in the kit. Captures, roughs, boards, renders and stock photos live in each project's `out/` and `images/` and
are never packed. The self-test draws its one fixture photo at run time.

## Licence
Code is under the Apache License 2.0 (`LICENSE`); prompts, rules, reference text and agent and command text are under
Creative Commons Attribution 4.0 (`LICENSE-CONTENT`). `NOTICE` says which folders fall under which, and covers
third-party sources.
