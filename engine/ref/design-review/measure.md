## 1. Measure (scripts first)
| Stage | Run |
|---|---|
| S3 Structure | `greek.py` (no WARN left), `pass.py --rough` |
| S4 Direction | `fontcheck.py tokens-d<n>.json`, then `pass.py --page <key>` after the pick |
| S6, S7, S8 | `fontcheck.py`, `pass.py --page <id>` / `--all` / `--system`, `uniq.py --pages` |

The scripts are reports, not quotas: judge every flag by eye.
