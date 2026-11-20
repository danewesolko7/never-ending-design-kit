# Security policy

## Supported versions
The kit is one working copy: `main` is supported. Projects built from it ship `consent.js` and the security headers
in their own sites, so a fix to either reaches existing sites only when they are rebuilt.

## Reporting a vulnerability
Report privately through GitHub: the repository's **Security** tab, then **Report a vulnerability** (private
vulnerability reporting). Do not open a public issue for a security problem.

Include what is affected (an engine tool, a hook, `bin/studio`, the consent banner or the headers the kit generates
for client sites), how to reproduce it, and the impact you see.

You can expect an acknowledgement within 5 working days and a first assessment within 10. Fixes land on `main`
with the self-test passing and a dated line in `engine/MANIFEST`; the advisory is published once a fix is out.

## In scope
- Code execution, path traversal or file writes outside the workspace by the engine tools, hooks or launcher.
- The kit's hooks failing to refuse a write they are meant to refuse.
- Consent bypass: anything in `engine/primitives/consent.js` that loads a gated script before a choice, or ignores a
  Global Privacy Control signal.
- Weaknesses in the Content Security Policy or other headers `tools/policy.py` generates.
- Secrets or client data reaching a pack (`tools/pack.py`) or the repository.

## Out of scope
- The third-party tools the kit installs (axe-core, Playwright, Fontsource): report those upstream.
- Legal sufficiency of policy wording. The kit checks that required pages exist and cover their topics; a lawyer
  approves the words.
