---
description: Start a new website project in the studio kit and run stage S0 (the brief), ending at gate G0.
argument-hint: <project-name>
---

Start the studio project `$ARGUMENTS` and run stage S0 here in the main conversation (S0 asks the creative director
questions, so it is never delegated).

1. Run `KIT_PROJECT=$ARGUMENTS studio start $ARGUMENTS`. It installs the pinned tools on first use, checks the kit,
   creates the studio from `studio.example/` if this workspace has none, opens the project, and prints the paths and
   the files to read. If it fails, show its output and stop.
2. Read the files it lists, in order (engine paths are under the engine folder it prints; `studio/` under the studio).
3. Follow `prompts/S0.md`: one AskUserQuestion round, then `brief.json` and `brief.md` in the project folder.
4. Write the hand-off to `docs/stages/0.md` (template in `prompts/templates.md`) and run
   `KIT_PROJECT=$ARGUMENTS studio gate --ready`.
5. Show the creative director the packet it printed and STOP. They answer with `/design-studio-kit:decide G0 approve` (or
   `fixes "..."`), then `/design-studio-kit:next` continues.
