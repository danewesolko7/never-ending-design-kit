# Contributing

The kit is a clean starting point that every build copies and never changes. A change to it is a change to every
future project, so each one goes through the same path.

## Making a change
1. Start Claude Code with `KIT_DEV=1` (the hooks refuse engine edits otherwise) and work on a branch.
2. Make the change in the narrowest place that solves it: a check before a constraint, a constraint before a step.
3. Run `bash engine/tools/setup.sh` once, then `bash engine/tools/selftest.sh`. Every step must pass. CI runs the
   self-test on macOS and Linux, and a supply-chain job (dependency audits and an SBOM).
4. Add a dated line under `[changes]` in `engine/MANIFEST`, saying what changed and why.
5. Open a pull request. `claude plugin validate .` checks the plugin manifest.

## House style
- Stage prompts stay under 250 words; reference sections are short, named and listed in their topic's `INDEX.md`.
- Write terse, plain English. Name sources; never copy third-party text.
- The engine holds no studio or project value: no client names, no colours in `engine/ref/` or `engine/rules/` text,
  no images. `kitcheck.sh` enforces this.
- Every new check has a self-test step that shows it passing on the fixture and failing on a planted fault.

## Adding a jurisdiction or a compliance rule
Rules are data in `engine/ref/compliance/jurisdictions.json`:
- a jurisdiction: code, name, consent model, laws (and `parent` when it sits inside another);
- a requirement: a page, a topic a page must cover (an English pattern), or a feature, with the `when` it applies;
- a manual item for the handover checklist.
Cite the law by its official name and article. Keep the reading at the level of pages, links and behaviour the
kit can check; leave legal interpretation to the client's lawyer. Add a self-test step when a rule needs new code.

## Licences
Code is under Apache 2.0 (`LICENSE`); prompts, rules, reference text, agents and commands are under CC BY 4.0
(`LICENSE-CONTENT`). `NOTICE` says which folders are which. By contributing you agree your contribution is offered
under the licence of the folder it lands in.

## Conduct
Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md).
