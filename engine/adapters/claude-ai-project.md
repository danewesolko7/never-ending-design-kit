# Adapter: claude.ai Project

How the neutral steps are done when the kit runs inside a claude.ai Project with code execution, without the plugin's
commands or hooks. Project files persist between chats; the sandbox does not.

- **Restore.** Keep a one-file copy of the kit in the Project (made with `pack.py --kit kit.py`). In each chat, copy it
  into the sandbox and run `python3 kit.py kit`; restore a project's one-file copy the same way into the same folder.
  Set `KIT_HOME` to that folder.
- **Run a stage.** `bash engine/tools/start.sh <project>` and follow what it prints. There are no agents: the model plays
  each stage's role in turn and stops at every gate.
- **No hooks.** Log by hand what hooks would measure: `gate.py --event image` after viewing an image. The gates are
  enforced by the prompts only, so check `start.sh`'s status line before writing.
- **Publish** a gate canvas, the Design System or the package with the publishing tool the Project offers, by file path
  (page plus its files), never by pasting HTML. Record the canvas link in `canvas.json` as `{"link": "..."}`.
- **Save a project** at every gate: `pack.py <p> <p>.py` (no photos), then save that file to the Project.
- **Save the kit** only after an approved G10, with the self-test passing. A build never saves the kit.
