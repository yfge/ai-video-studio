# Repository Contracts

This document defines the mechanical contracts that keep ai-video-studio legible for humans and agents.

## Enforcement Entry Points

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `python scripts/check_repo_contracts.py --mode audit`

## `check_repo_docs.py`

This check validates:

- required root docs exist
- `AGENTS.md` mirrors stay in sync
- `docs/README.md` indexes repository docs
- harness commands remain documented in `README.md` or `docker/README.md`
- stale frontend-testing claims do not drift from actual package/test state

## `check_repo_contracts.py`

The contract checker has two modes:

- `diff`: PR and pre-commit gate for changed files
- `audit`: full repository scan that writes machine-readable debt reports

Standard audit outputs:

- `artifacts/repo_audit/latest/contracts-report.json`
- `artifacts/repo_audit/latest/contracts-summary.md`

## Contract Categories

The report must track:

- oversized files
- route handlers over 50 lines
- direct SQLAlchemy access outside repositories
- legacy choke-point imports or references
- docs drift

## Choke-Point Policy

Known legacy hotspots are tolerated as debt, not as expansion points:

- `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`
- `ai-pic-backend/app/services/dialogue_audio_service.py`
- `ai-pic-backend/app/services/ai_service_manager.py`
- `ai-pic-backend/app/services/script_agent.py`

New work must not add fresh dependencies on these files unless the change is reducing or splitting the file itself.

## Audit Expectations

- `diff` mode should fail on newly introduced contract violations in changed files.
- `audit` mode should always produce a report, even when the repository still contains baseline debt.
- Use audit mode to track debt over time, not to hide it.

## Reporting Expectations

The JSON report should be stable enough for scripts to consume. At minimum it must contain:

- `mode`
- `generated_at`
- `summary`
- `violations`
- `docs_drift`

The Markdown summary should include:

- top-line violation counts
- highest-risk offenders
- whether docs drift is present
- report paths for follow-up automation
