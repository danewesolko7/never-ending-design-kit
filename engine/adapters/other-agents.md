# Adapter: any other agent or a person at a terminal

- **Workspace.** A folder with `engine/` (this kit), `studio/` and `projects/`, or set `KIT_HOME` to the folder holding
  `studio/` and `projects/` and run the engine from wherever it is installed. `bin/studio` works from any shell.
- **Run a stage.** `studio start <project>`, read what it prints, follow the stage prompt, end with
  `studio gate --ready`, and stop for the creative director, who records `studio gate --decide ...`.
- **No hooks.** Run `gate.py --event read <words>` and `gate.py --event image` when you can, so usage stays measured;
  otherwise the planned reads are counted.
- **Publish** the canvas, Design System and package as static files from `out/canvas/`, `out/site/` and
  `out/package/` (any static host). **Save** projects and the studio in private repositories.
