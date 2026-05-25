# Cartoon Sample Production Proof

This document is the fixed tracker for the 10-sample production proof in
`tasks.md` and `docs/exec-plans/active/main-chain-commercial-readiness.md`.
It is intentionally narrow: prove repeatable Timeline-first output before
expanding product scope.

## Validation Scope

- Vertical: stylized 2D or 3D cartoon short-drama clips, 9:16, 30-60 seconds.
- Micro-genre: workplace fantasy reversal with light suspense.
- Audience promise: each episode has one clear conflict, one visual hook, and
  one reversal.
- Visual safety guard: non-photorealistic, animated, no live-action, no
  realistic human skin texture, no celebrity likeness, no real-person identity.
- Production path: `Episode -> Timeline -> clip assets -> render -> export`.
- Acceptance evidence: every sample row must link to a final export and record
  cost, elapsed generation time, failure points, and manual fixes.

## Reusable Cast

| Character | Role                                                          | Visual Guard                                                    |
| --------- | ------------------------------------------------------------- | --------------------------------------------------------------- |
| Lin Xia   | new producer who spots impossible delivery constraints        | stylized 3D cartoon, simplified face, expressive silhouette     |
| Kai       | skeptical operations lead who pressures the deadline          | 2D cartoon office rival, bold shape language, no realistic skin |
| Momo      | floating studio assistant that exposes hidden timeline errors | small robot mascot, non-human, glowing screen face              |

## Prompt Guardrail

Use this guardrail in storyboard image/video prompts and provider rework prompts:

```text
Non-photorealistic 2D animation or stylized 3D cartoon, vertical 9:16 short-drama frame, clean expressive character shapes, no live-action, no realistic human skin texture, no celebrity likeness, no real-person identity.
```

## Sample Tracker

| #   | Sample ID             | Hook                                                             | Target Length | Status  | Script | Timeline | Render Job | Final Export | Cost | Time | Failures | Manual Fixes |
| --- | --------------------- | ---------------------------------------------------------------- | ------------- | ------- | ------ | -------- | ---------- | ------------ | ---- | ---- | -------- | ------------ |
| 1   | cartoon-workplace-001 | A timeline shows a delivery before it was ordered.               | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 2   | cartoon-workplace-002 | Momo flags a clip whose voice belongs to the wrong character.    | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 3   | cartoon-workplace-003 | Kai demands a realistic ad; Lin Xia redirects to cartoon safety. | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 4   | cartoon-workplace-004 | A storyboard keyframe predicts the final reversal too early.     | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 5   | cartoon-workplace-005 | A generated clip looks good but breaks the stable clip id.       | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 6   | cartoon-workplace-006 | The export succeeds, but one beat has no video asset.            | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 7   | cartoon-workplace-007 | Momo catches a cost spike before final render.                   | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 8   | cartoon-workplace-008 | A re-render fixes motion but damages continuity.                 | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 9   | cartoon-workplace-009 | Lin Xia must choose speed or a cleaner timeline rollback.        | 30-45s        | Pending |        |          |            |              |      |      |          |              |
| 10  | cartoon-workplace-010 | The team exports a final cut seconds before the deadline.        | 30-45s        | Pending |        |          |            |              |      |      |          |              |

## Completion Rule

Do not mark the production proof complete until all 10 sample rows have:

- a final export URL or local artifact path;
- selected text/image/video model names;
- elapsed time from first generation request to final export;
- approximate provider cost or token/credit basis;
- failure points, including provider safety refusals or retries;
- manual fixes, including prompt edits, replacement assets, rollback, re-dub,
  re-render, or re-export actions.
