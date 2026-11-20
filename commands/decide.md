---
description: Record the creative director's decision at a studio gate (approve, pick, fixes or stop).
argument-hint: <gate> approve | pick <n> | fixes "<a; b>" | stop  [note "<why>"] [last]
---

Record this gate decision exactly as the creative director gave it: `$ARGUMENTS`. Only run this command when the CD
typed it; never on your own judgement.

1. Translate it to `studio gate --decide <gate>` with one of `--approve`, `--pick <n>`, `--fixes "<a; b>"` or `--stop`,
   plus `--note "<why>"` when a note is given and `--last` when the CD says this is the last G8 batch (packaging then
   runs). Set `KIT_PROJECT=<project>` when a project other than the current one is meant. Run it.
2. Show what it printed. If the decision names fixes, the next `/design-studio-kit:next` applies them as diffs. Say that
   `/design-studio-kit:next` continues, and STOP: the CD starts the next stage.
