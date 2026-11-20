## Record every reference
One row per reference in the project's `references.jsonl` (schema in `tools/refs.py --help`): sweep, library section,
title, link, date seen, the one technique borrowed, when to use it. `tools/refs.py --check --sweep <A|B|C>` must pass.
Set `"used": true` when the build uses a technique; at packaging (S9) `refs.py --promote` adds those to
`studio/library.md` (technique only, no project details). The engine library (`ref/library.md`) changes only at G10.
