# Adapter: Claude Code

How the neutral steps the tools print ("save", "publish") are done in Claude Code, with the studio plugin installed.

- **Workspace.** Open Claude Code in the studio's workspace: the folder holding `studio/` (a private repository) and
  `projects/`. That folder is `KIT_HOME`; the `studio` command on PATH finds the engine inside the plugin.
- **Commands.** `/design-studio-kit:new`, `/design-studio-kit:next`, `/design-studio-kit:decide`, `/design-studio-kit:status`, `/design-studio-kit:sweep`, `/design-studio-kit:retro`.
- **Hooks** enforce the gates, rebuild after page edits, and log every Read, so words read and images viewed are
  measured, not reported. Nothing to log by hand.
- **Publish a gate canvas.** milestone.py prints a page and its files. Publish `out/canvas/index.html` with the Artifact
  tool, passing each listed file under `files` at the same name. The first time, write the artifact's link to the
  project's `canvas.json` as `{"link": "..."}`; later gates republish to that link.
- **Publish the Design System (G7) and the package (stage 9)** the same way: the specimen page with `out/site/site.css`
  and its fonts; `out/package/index.html` with its images and notes.
- **Save a project.** The project folder is its own record. Keep `projects/<p>/` in a private repository (or the
  studio's), committing at each gate; `pack.py <p> <out.py>` makes a one-file copy without photos when one is needed.
- **Save the kit.** Never during a project. Kit changes go through G10 on a branch of the kit repository.
