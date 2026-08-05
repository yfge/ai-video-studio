## User Prompt

Complete the v3 long-form generation chain with a real 48-chapter web novel. The chain should favor engaging plot and reliable generation rather than repeatedly rewriting otherwise valid chapters.

## Goals

- Reduce the observed 100% local-repair rate caused by systematic prose-model length overshoot.
- Preserve the immutable 2,000–3,000 acceptance contract and all existing chapter/hash evidence.
- Keep old persisted length-control versions replayable while applying stronger calibration only to subsequent prose calls.

## Changes

- Added prose length-control contract version 5.
- Removed the acceptance-range lower clamp from the model-facing target for v5, allowing the feedback controller to compensate for a provider that consistently emits about 1.55 times the requested characters.
- Kept the public acceptance interval separate and unchanged; v5 exposes one internally calibrated 90%–110% request band to the prose model.
- Preserved v1–v4 reconstruction behavior for existing invocation and approval evidence.
- Added regression coverage for a 1.6x provider bias and updated exact historical/control expectations.

## Validation

- Real product evidence: Revision `38a8d8eee1744c2689eabaf29a5cc2ba` generated five ready chapters; all five initial prose calls overshot 3,000 characters and required local compression, for a 100% observed repair rate.
- Task `6895` was cancelled through the product UI after chapter 5 became ready; chapters 1–5 and their hashes were preserved.
- Targeted length-control tests: `15 passed`.
- Full Story Novel unit suite: `865 passed, 1 skipped`.
- Exact-path isort and black hooks: passed; the largest changed test file is 249 lines.
- Repository docs, contracts, and diff checks are recorded after this ledger is added.

## Next Steps

- Restart backend and worker, then resume the same Revision through the official product route.
- Compare chapter 6+ initial prose length and local-repair rate with chapters 1–5; keep the acceptance contract at 2,000–3,000.
- Continue to 48/48 only while hard gates remain fail-closed, then run continuity, GPT-5.6 batch/global review, DOCX export, and approval.

## Linked Commits

- Pending.
