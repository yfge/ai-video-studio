# Outline-driven Long-form Novel Execution Plan

**Goal:** Generate a chaptered long novel whose size is determined only by the
confirmed StorySeed outline, while preserving reproducible continuity evidence
and revision-local memory.

**Architecture:** Reuse `story_novel_exports.generation_plan`,
`continuity_ledger`, chapter checkpoints, Narrative Event, and Character Memory.
One Celery task plans once, generates sequentially, extracts after every
checkpoint, and resumes from the last valid body/context/extraction boundary.

## Delivery slices

- [x] Make prose request length/chapter fields optional and ignored.
- [x] Persist `planning -> ready|failed` and validate one repaired dynamic plan.
- [x] Add 3000–5000 non-whitespace-character chapter gate with one repair.
- [x] Add bounded 32K context packs with prior plot/fact/memory ID/hash evidence.
- [x] Add chapter extraction checkpoints and extraction-only resume.
- [x] Invalidate edited/regenerated sources and successor continuity state.
- [x] Promote only current source-hash candidates at whole-novel approval.
- [x] Split continuity review into adjacent full-text windows and global synthesis.
- [x] Remove prose length/chapter controls and refresh revisions while polling.
- [x] Complete focused/full repository gates and real-browser verification.
- [x] Generate a complete real-model novel and save GPT-5.6 layered review evidence.

## Acceptance evidence

- Dynamic plans may contain more than 24 chapters; invalid/truncated output gets
  exactly one repair and fails before prose if still invalid.
- Every completed chapter contains 3000–5000 non-whitespace characters.
- Chapter N evidence lists prior chapter, event, and memory IDs/hashes and all
  context truncations.
- Resume never rewrites a matching body merely because extraction failed.
- Approval verifies every body/source hash and continuity coverage before
  promoting revision-local candidates.
- Real-model artifacts live under a dedicated `artifacts/runs/<run_id>/`.

## Completion evidence

- DeepSeek V4 Flash planned and generated 48 chapters with 198,691 actual
  non-whitespace characters; every chapter passed the 3,000–5,000 gate and all
  48 extraction checkpoints were ready.
- Final continuity task covered every chapter ID/hash, used a 16,000-token
  output budget, and correctly blocked approval on 65 blocking issues.
- Playwright/System Chrome fallback completed the UI path with zero console
  errors after Chrome DevTools transport returned HTTP Not Found.
- GPT-5.6 completed eight six-chapter reads plus a global 66/100 review under
  `artifacts/runs/story-novel-longform-real-20260723/`.
