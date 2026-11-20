---
description: Open the studio director's retro (S10) on a packaged or stopped project and propose kit changes for G10.
argument-hint: [project-name]
---

1. Run `KIT_PROJECT=<project> studio gate --retro` for `$ARGUMENTS` (or the current project). If it refuses, show why
   and STOP.
2. Run the `studio-director` agent with the project name. When it returns, show its proposals (at most five, each with
   its target file) and the packet, then STOP for `/studio:decide G10 ...`.
3. The engine is edited only after G10 is approved, in a kit session started with KIT_DEV=1 and with the self-test
   passing (`bash engine/tools/selftest.sh`).
