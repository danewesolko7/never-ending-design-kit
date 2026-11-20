## 1. Measure (scripts first)
| Stage | Run |
|---|---|
| S3 Structure | `greek.py` (no WARN left), `pass.py --rough` |
| S4 Direction | `fontcheck.py tokens-d<n>.json`, then `pass.py --page <key>` after the pick |
| S6, S7, S8 | `fontcheck.py`, `pass.py --page <id>` / `--all` / `--system`, `uniq.py --pages`, `comply.py` |

pass.py now also runs the impeccable detector (slop:<rule>, 62 rules at 1440 and 390), the copy tells
(copy:<id>), worst-case content (stress), WCAG text spacing (spacing) and a keyboard pass (keyboard). For a manual
look at states and keyboard order: `studio browse page <id>`, then `press Tab`, `snapshot`, `screenshot`.

The scripts are reports, not quotas: judge every flag by eye.
