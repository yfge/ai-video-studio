# STD-DATA-001: SQLAlchemy Queries Stay Inside Repositories

## Intent

Direct ORM access outside repositories makes data rules hard to audit and
bypasses the backend layering contract: `api -> services -> repositories ->
models`.

## Scope

Backend application code under `ai-pic-backend/app/`, excluding
`ai-pic-backend/app/repositories/`.

## Automatic Enforcement

`python scripts/check_repo_contracts.py --mode diff <changed files>` fails on
new `session.query(...)`, `db.query(...)`, `self.db.query(...)`, or
`self.session.query(...)` access outside repositories.

## Evidence

Contract reports include `standard_id=STD-DATA-001`, `query_hits`,
`baseline_exemption`, and the affected path.

## Repair Path

Add or reuse a repository method. Services should call the repository and keep
business policy outside the model layer.

## Revision Trigger

Update this standard if the repository abstraction changes, if SQLAlchemy 2.0
query APIs require a new detector, or if audit evidence shows another direct
data-access pattern bypassing repositories.
