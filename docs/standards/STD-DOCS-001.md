# STD-DOCS-001: Repository Docs And Agent Mirrors Stay Synchronized

## Intent

Agents and humans need the same source of truth. Durable workflow and
architecture rules belong in repository docs, and the agent entrypoint mirrors
must not drift.

## Scope

- Root docs required by `scripts/check_repo_docs.py`
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`
- `docs/README.md`
- Harness command documentation in `README.md` or `docker/README.md`

## Automatic Enforcement

`python scripts/check_repo_docs.py` and `python scripts/check_repo_contracts.py`
report docs drift under `standard_id=STD-DOCS-001`.

## Evidence

Reports include docs drift errors and the owning standard document.

## Repair Path

Update the repository source-of-truth doc, keep mirrors exact, and add new docs
to `docs/README.md` in the same change.

## Revision Trigger

Update this standard when the required root docs, mirror policy, or docs index
rules change.
