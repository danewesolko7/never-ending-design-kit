---
name: studio
description: Design or redesign a multi-page website with the never-ending design kit, an agentic studio gated by a creative director. Use when someone asks to design a website with the studio kit, start or resume a studio project, run the next stage, record a gate decision, or run an inspiration sweep.
---

The studio kit runs a website project through ten stages, each ending at a gate the creative director (CD) decides.
Agents do each stage's work from the engine's stage prompts; hooks refuse writes a project's state does not allow.

- New project: `/design-studio-kit:new <project>` (runs the brief, S0, and stops at G0).
- Continue: `/design-studio-kit:next [project]` runs the current stage with its agents and stops at the next gate.
- Decide: only when the CD gives a decision, `/design-studio-kit:decide <gate> approve | pick <n> | fixes "..." | stop`.
- Inspiration: `/design-studio-kit:sweep <A|B|C> [project]` (the libraries first, then the web for what they lack).
- Where things stand: `/design-studio-kit:status [project]`. Retro after packaging: `/design-studio-kit:retro [project]`.

Never record a gate decision the CD did not give, and never edit the engine during a project.
