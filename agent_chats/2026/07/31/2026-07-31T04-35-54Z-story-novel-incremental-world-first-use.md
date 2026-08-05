## User Prompt

Long-form web fiction should permit planned and sequentially introduced characters, places, organizations, concepts, and progressively larger activity or time scales. Growth may be evaluated across cognition, capability, resources, and scale, but must not become a per-chapter numeric KPI.

## Goals

- Ensure a persistent Canon entity is visible to just-in-time chapter planning at its first outline-authorized use, including conservative wording variants.
- Require a typed creation transition when an explicitly absent entity first becomes usable, without forcing an upgrade in every chapter.
- Keep future entities isolated and reject broad suffix-only matches.

## Changes

- Extracted conservative Canon entity mention matching into a focused service.
- Bound an entity when its exact name/alias appears, or when a label of at least four characters differs only in its final noun character; generic shared suffixes do not bind.
- Updated the chapter-package prompt so an explicitly absent visible entity must receive one limited first-use status transition, while later milestone outcomes remain protected.
- Added regressions for first-use wording variation, unrelated market suffixes, and the prompt lifecycle contract.

## Validation

- Real product evidence: Task `6892`, Revision `2bec7fa903c94b5d80a71259b77b08dc`, Canon hash `2e90bffdccb5b48a657d868142f6be430712e197a00929430014528dfd110f7f`.
- The task was cancelled through the product UI after the accepted plan showed `obj-joint-ledger` as `not_created`, while chapter 5 already established the shared account and chapter 9 used it without a typed creation transition. Task `6892` is `CANCELLED`; one chapter remains `review_required`, zero are ready.
- Targeted tests: `7 passed`.
- Full Story Novel unit suite: `864 passed, 1 skipped`.
- Exact-path isort and black hooks: passed.
- Repository docs, contracts, and diff checks are recorded after this ledger is added.

## Next Steps

- Restart backend and worker after the validated commit.
- Resume the same fresh v3 Revision through the official UI once; verify the rebuilt chapter 5 package binds and creates the shared ledger before allowing the run to continue.
- Continue the required two-ready-chapter cancel/resume hash proof, 48/48 generation, continuity review, GPT-5.6 review, DOCX export, and approval only after all hard gates pass.

## Linked Commits

- Pending.
