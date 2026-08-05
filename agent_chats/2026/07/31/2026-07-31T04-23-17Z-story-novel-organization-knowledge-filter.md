## User Prompt

Implement the chapter-planning-driven long-form novel quality pipeline, then use the real product chain to generate and review a fresh 48-chapter novel. Growth may span cognition, capability, resources, and activity/time scale, but these dimensions must not become per-chapter numeric KPIs.

## Goals

- Preserve strict Canon validation while improving model-output adaptation for scalable long-outline planning.
- Prevent organizations, locations, groups, or concepts from receiving character-only `knowledge` milestone outcomes.
- Resume the fresh v3 Revision only after focused and full Story Novel validation passes.

## Changes

- Updated Canon and Canon-repair prompts to state that `knowledge contains` outcomes may target only `kind=character`; organization trust or awareness must be represented as an actual organization state.
- Fixed the deterministic milestone filter so character-only knowledge validation still runs when the scalable Canon contract intentionally omits the full chapter array.
- Kept chapter-dependent location filtering conditional on chapter availability and left raw `normalize_canon` validation strict.
- Added a regression covering the exact long-outline production shape and prompt contract.

## Validation

- Real product evidence: Task `6891`, Revision `2bec7fa903c94b5d80a71259b77b08dc`, Canon invocations `3517` and `3518`; repair remained fail-closed with zero chapters because organization IDs were used as knowledge subjects.
- Targeted Canon tests: `15 passed`.
- Full Story Novel unit suite: `861 passed, 1 skipped`.
- Exact-path isort and black hooks: passed.
- Repository contracts, documentation checks, and diff checks are recorded after this ledger is added.

## Next Steps

- Restart the mounted backend and worker to load filter version 7.
- Resume the same fresh v3 Revision through the official product route and inspect the regenerated Canon and entity lifecycle plan before prose generation.
- Continue the required cancel/resume hash proof, 48/48 generation, continuity review, GPT-5.6 batch/global review, DOCX export, and approval only if all hard gates pass.

## Linked Commits

- Pending.
