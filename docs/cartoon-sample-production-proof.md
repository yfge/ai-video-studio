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

Run evidence: `artifacts/runs/cartoon-production-proof-20260525T153900Z/production-proof.json`.

| #   | Sample ID             | Hook                                                             | Target Length | Status   | Script | Timeline | Render Job | Final Export                                                                      | Models                                            | Cost                  | Time  | Failures | Manual Fixes |
| --- | --------------------- | ---------------------------------------------------------------- | ------------- | -------- | ------ | -------- | ---------- | --------------------------------------------------------------------------------- | ------------------------------------------------- | --------------------- | ----- | -------- | ------------ |
| 1   | cartoon-workplace-001 | A timeline shows a delivery before it was ordered.               | 30s           | Exported | 132    | 3 v1     | 4          | https://resource.lets-gpt.com/timeline-renders/video/20260525/234333/a38091b3.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 4.11s | None     | 0            |
| 2   | cartoon-workplace-002 | Momo flags a clip whose voice belongs to the wrong character.    | 30s           | Exported | 133    | 4 v1     | 5          | https://resource.lets-gpt.com/timeline-renders/video/20260525/234335/5e250d2c.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.03s | None     | 0            |
| 3   | cartoon-workplace-003 | Kai demands a realistic ad; Lin Xia redirects to cartoon safety. | 30s           | Exported | 134    | 5 v1     | 6          | https://resource.lets-gpt.com/timeline-renders/video/20260525/234337/07c90b54.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.04s | None     | 0            |
| 4   | cartoon-workplace-004 | A storyboard keyframe predicts the final reversal too early.     | 30s           | Exported | 135    | 6 v1     | 7          | https://resource.lets-gpt.com/timeline-renders/video/20260525/234339/5b70d0b3.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.08s | None     | 0            |
| 5   | cartoon-workplace-005 | A generated clip looks good but breaks the stable clip id.       | 30s           | Exported | 136    | 7 v1     | 8          | https://resource.lets-gpt.com/timeline-renders/video/20260525/234341/cc453499.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 1.99s | None     | 0            |
| 6   | cartoon-workplace-006 | The export succeeds, but one beat has no video asset.            | 30s           | Exported | 137    | 8 v1     | 9          | https://resource.lets-gpt.com/timeline-renders/video/20260525/234343/ae12a0b0.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.02s | None     | 0            |
| 7   | cartoon-workplace-007 | Momo catches a cost spike before final render.                   | 30s           | Exported | 138    | 9 v1     | 10         | https://resource.lets-gpt.com/timeline-renders/video/20260525/234345/c242a4fe.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.07s | None     | 0            |
| 8   | cartoon-workplace-008 | A re-render fixes motion but damages continuity.                 | 30s           | Exported | 139    | 10 v1    | 11         | https://resource.lets-gpt.com/timeline-renders/video/20260525/234347/8bd40bdd.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.13s | None     | 0            |
| 9   | cartoon-workplace-009 | Lin Xia must choose speed or a cleaner timeline rollback.        | 30s           | Exported | 140    | 11 v1    | 12         | https://resource.lets-gpt.com/timeline-renders/video/20260525/234349/e747ca28.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.0s  | None     | 0            |
| 10  | cartoon-workplace-010 | The team exports a final cut seconds before the deadline.        | 30s           | Exported | 141    | 12 v1    | 13         | https://resource.lets-gpt.com/timeline-renders/video/20260525/234352/cea34e3f.mp4 | local-template / ffmpeg-cartoon / timeline-render | $0.00 local synthetic | 2.04s | None     | 0            |

## Validation Evidence

- Path exercised: `Episode -> Timeline -> clip assets -> render -> export`.
- Each sample uses 5 source video clip assets and 5 source audio clip assets,
  with video timing aligned to the dialogue/source-audio track in Timeline Spec.
- Render jobs `4` through `13` reached `succeeded`, each with `progress=100`,
  `duration_ms=30000`, and 5 render-output lineage links.
- Browser validation opened sample 1 final export and found an HTML video element
  with `readyState=4`, `duration=30.02322`, `videoWidth=360`, and
  `videoHeight=640`. Screenshot evidence:
  `artifacts/runs/cartoon-production-proof-20260525T153900Z/browser-first-export.png`.
- Network spot check: sample 1 and sample 10 final export URLs returned
  `200 video/mp4`.
- Provider spend was not exercised in this run. The proof intentionally used
  local 2D cartoon synthetic assets to avoid live-action human safety limits and
  to isolate Timeline/render/export repeatability.

## Completion Rule

Do not mark the production proof complete until all 10 sample rows have:

- a final export URL or local artifact path;
- selected text/image/video model names;
- elapsed time from first generation request to final export;
- approximate provider cost or token/credit basis;
- failure points, including provider safety refusals or retries;
- manual fixes, including prompt edits, replacement assets, rollback, re-dub,
  re-render, or re-export actions.
