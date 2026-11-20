---
description: Run the studio project's current stage with its agents, up to the next creative-director gate, then stop.
argument-hint: [project-name]
---

Run the current stage of the studio project (`$ARGUMENTS`, or the current project when empty). You orchestrate; the
stage agents do the work. Pass the project name to every agent and set `KIT_PROJECT=<project>` on every `studio` call.

1. Run `KIT_PROJECT=<project> studio start <project>`. Read what it prints: the stage, the status, the options this
   stage and the paths. If it says the project is waiting for the creative director, show `out/packet.md` from the
   project folder and STOP. If it is packaged or stopped, say so and STOP.
2. Run the stage:

| Stage | Who runs it |
|---|---|
| 0 | You, as in `/design-studio-kit:new` (S0 asks the CD questions) |
| 1 | `inspiration-scout` (sweep A), then `researcher` |
| 2 | `content-strategist` |
| 3 | `inspiration-scout` (sweep B), then `layout-designer` once per concept, in parallel: c1, c2, c3 (lean mode: one run, no option named) |
| 4, before the G3b/G4a pick | `inspiration-scout` (sweep C), then `art-director` once per direction, in parallel: d1, d2, d3 (lean mode: one run) |
| 4, after the pick | `art-director` with the task "finish" |
| 5 | `copywriter` for the key page |
| 6 | `comp-designer` |
| 7 | `systems-designer` |
| 8 | `copywriter` for the batch's pages (text only), then `production-designer` for the batch |
| 9 | Nothing to run: packaging ran at the last G8 approval. Publish the package (step 4) |
| 10 | `studio-director` (after `/design-studio-kit:retro`) |

3. For stages 3 and 4 run in parallel, you close the stage once all agents return: check each option's uniq.py result
   (a failing option is revised once by its agent), run `studio tool pass.py --rough` (stage 3), write the hand-off
   `docs/stages/<stage>.md` naming every option, and run `studio gate --ready`.
4. At a visual gate (G3a, G3b/G4a, G4b, G6, G7, G8): run `studio gate --checklist`, then
   `studio tool milestone.py <gate>`, and publish the canvas as the engine's `adapters/claude-code.md` says. At G7, after
   approval, publish the Design System; at stage 9, publish `out/package/`.
5. Show the creative director the packet (`out/packet.md`), the canvas link if any, and every check an agent did not
   run. STOP. Never record a decision yourself: the CD answers with `/design-studio-kit:decide`.
