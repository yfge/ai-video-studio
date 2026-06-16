# STD-EVIDENCE-001: Agent Changes Include Durable Validation Evidence

## Intent

Code changes should leave enough evidence for another agent or reviewer to
understand the prompt, scope, validation, residual risk, and linked commit.

## Scope

Meaningful changes under:

- `ai-pic-backend/`
- `ai-pic-frontend/`
- `scripts/`
- `docker/`
- `infrastructure/`
- `AGENTS.md`

## Automatic Enforcement

`python scripts/check_agent_chats.py` enforces the required ledger file shape for
staged code changes. Browser and harness evidence requirements are enforced by
review, the testing policy, and harness summaries that carry
`STD-EVIDENCE-001` standard references.

## Evidence

An `agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-topic.md` file with the required
frontmatter and sections. For browser or harness work, include entry URL,
scenario, engine, decisive network or console evidence, and artifact run ID.
`browser_flow.json`, `golden_path.json`, and `summary.json` should include
`standard_ids` and `standard_refs` when they are the durable validation artifact.

## Repair Path

Create or update the ledger entry in the same change. If validation is skipped
or downgraded, document the reason and the remaining risk.

## Revision Trigger

Update this standard when the ledger schema changes or when repeated review
findings show that the current evidence fields are not enough to reproduce a
decision.
