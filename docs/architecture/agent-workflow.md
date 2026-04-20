# Agent Workflow

This document defines how agents should leave traceable, reviewable changes behind.

## Knowledge Discipline

- Keep durable decisions in repository files, not chat-only context.
- Use `AGENTS.md` as the entrypoint and linked docs as the source of truth.
- When a repeated review comment becomes a rule, promote it into docs or automation.

## Ledger Contract

Every meaningful code change under `ai-pic-backend/`, `ai-pic-frontend/`, `scripts/`, or `AGENTS.md` must ship with an `agent_chats` entry in the same commit.

Path format:

- `agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-topic.md`

Required frontmatter fields:

- `id`
- `date`
- `participants`
- `models`
- `tags`
- `related_paths`
- `summary`

Required body sections, in order:

1. `## User Prompt`
2. `## Goals`
3. `## Changes`
4. `## Validation`
5. `## Next Steps`
6. `## Linked Commits`

## Validation Recording

For backend, frontend, and harness work, `## Validation` should include:

- exact command or scenario name
- scope of the check
- pass/fail outcome
- decisive evidence

For browser checks, record:

- entry URL
- actual user path
- console observations
- decisive network request or response
- final result

If a fallback engine was used, state why Chrome could not continue.

## Commit Discipline

- Keep commits atomic and focused.
- Pair each commit with its matching ledger entry.
- Use Conventional Commit subjects.
- Before commit:
  - relevant tests pass
  - `pre-commit run --all-files` is clean or skips are documented
  - `./docker/build_prod_images.sh` succeeds

## Conflict Signals

When logs, requests, browser output, or user evidence contradict your first guess:

- explicitly acknowledge the uncertainty
- reproduce with a real request or browser path
- record the wrong assumption
- record the contradicting evidence
- rerun after the fix

Do not insist that the code is correct while the evidence says otherwise.
