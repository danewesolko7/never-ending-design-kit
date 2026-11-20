---
description: Run one inspiration sweep (A subject, B structure, C aesthetic) for a studio project: the libraries first, then the web.
argument-hint: <A|B|C> [project-name]
---

Read `$ARGUMENTS`: the first word is the sweep letter (A, B or C), the second, if any, the project (else the current
project). Run the `inspiration-scout` agent with the project name and the sweep letter. When it returns, show the
references it recorded (title, link, technique), the library sections still thin, and the result of
`KIT_PROJECT=<project> studio tool refs.py --check --sweep <letter>`.
