---
id: 2025-10-15T17-28-01Z-dev-workflow-hardening
date: "2025-10-15T17:28:01Z"
participants: [human, codex]
models: [gpt-5-codex]
tags: [process, tooling]
related_paths:
  - AGENTS.md
  - .pre-commit-config.yaml
  - scripts/check_agent_chats.py
  - commitlint.config.cjs
  - GEMINI.md
summary: "Apply strict agent collaboration workflow, quality gates, and commit policy from reference projects."
---

## User Prompt

User asked to replicate the strict development paradigm used in talkReplay, orion, ai-shifu, and talkreplay.com, covering agent chat logging, pre-commit hooks, and shared agent instructions.

## Goals

- Centralise assistant guidance so every tool follows the same rules.
- Enforce ledger-driven collaboration through automated checks.
- Align commit hygiene with Conventional Commits and add local quality gates.

## Changes

- Replaced the previous CLAUDE-centric guidance with a repo-wide policy covering instruction precedence, ledger expectations, testing, and delivery checklist in `AGENTS.md` (mirrored by `GEMINI.md`).
- Added `.pre-commit-config.yaml` mirroring reference repos: ruff/black/isort, prettier, new ledger validator, backend pytest, frontend lint, and commitlint hooks.
- Implemented `scripts/check_agent_chats.py` to ensure agent chat entries have the required directory structure, frontmatter, sections, and accompany code changes.
- Introduced `commitlint.config.cjs` to lock commit messages to Conventional Commits.
- Seeded `agent_chats/` with `.gitkeep` and organised timestamped log directories for future entries.

## Validation

- `python scripts/check_agent_chats.py`

## Next Steps

- Install hooks locally via `pip install pre-commit && pre-commit install && pre-commit install --hook-type commit-msg`.
- On next commits, ensure ledger entries describe validation outcomes and link to resulting commits.

## Linked Commits

- pending
