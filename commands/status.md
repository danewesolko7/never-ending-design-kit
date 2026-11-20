---
description: Show where a studio project stands: stage, gate, decisions, open items and budget.
argument-hint: [project-name]
---

Run `KIT_PROJECT=<project> studio gate --status` for `$ARGUMENTS` (or the current project when empty) and
`KIT_PROJECT=<project> studio start <project> --check --no-setup`. Show both outputs in short form: the stage and
status, the pending gate, the last decisions, open items, budget left, and the next command to run.
