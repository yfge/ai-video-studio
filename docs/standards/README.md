# Standard Engine

The standard engine turns durable judgement into versioned repository artifacts.
It is not a new service. It is the combination of standard documents, mechanical
checks, harness evidence, and ledger entries that make quality decisions
traceable.

## Standard Object Shape

Every standard should answer:

- `id`: stable handle used in reports and ledger entries.
- `intent`: the human judgement the standard protects.
- `scope`: files, workflows, or runtime paths covered by the standard.
- `automatic enforcement`: deterministic check, test, harness, or pre-commit
  hook.
- `evidence`: command output, browser run, artifact, or review signal that
  proves the standard.
- `repair path`: how an agent should fix a failure instead of routing around it.
- `revision trigger`: what kind of production failure or review comment should
  update the standard.

## Active Standards

- `docs/standards/STD-ARCH-001.md` - source files stay below size limits.
- `docs/standards/STD-ARCH-002.md` - API route handlers stay thin.
- `docs/standards/STD-DATA-001.md` - SQLAlchemy queries stay inside
  repositories.
- `docs/standards/STD-ARCH-003.md` - legacy choke points are not expansion
  points.
- `docs/standards/STD-DOCS-001.md` - repository docs and agent mirrors stay
  synchronized.
- `docs/standards/STD-EVIDENCE-001.md` - agent changes include durable
  validation evidence.
- `docs/standards/STD-SCRIPT-001.md` - production scripts satisfy beat-level
  quality gates.
- `docs/standards/STD-TIMELINE-001.md` - Timeline-first provider chains
  preserve media lineage.

## Runtime Entry Points

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `python scripts/check_repo_contracts.py --mode audit`
- `python scripts/check_agent_chats.py`

`check_repo_contracts.py` reports include `standard_id`, `standard_doc`,
evidence fields, and a suggested repair direction for every mechanical
violation.
