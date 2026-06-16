# Storyboard, Keyframe, And Video Generation Design

## Goal

Improve the selected Timeline clip production flow so storyboard generation,
start/end keyframe generation, and provider-backed video generation behave as
one coherent clip-level workflow.

The change should make the operator understand:

- which reference source will drive the video,
- whether the selected clip already has storyboard and start/end frame assets,
- which IP/environment/manual references will be sent to each generation task,
- how empty prompts are resolved from Timeline shot-plan data.

The backend should generate storyboard, keyframe, and video prompts from the
same shot-plan and motion-layer contract so the visual plan does not drift
between steps.

## Current State

Frontend production controls live under the Timeline selected-clip production
panel:

- `TimelineClipProviderReworkControls.tsx` owns shared state for prompt, model,
  reference image input, selected IPs, selected environment images, storyboard
  style, panel count, and video reference mode.
- `TimelineClipProviderGenerationPayloads.ts` builds clip storyboard and
  keyframe task payloads.
- `TimelineClipProviderReworkModel.ts` builds provider video rework payloads.
- `TimelineClipProviderReworkCards.tsx` renders the compact three-step command
  surface: storyboard, keyframes, video.

Backend generation paths are already clip scoped:

- `GridStoryboardSheetService.queue_clip_sheet()` queues a clip storyboard
  sheet task.
- `TimelineClipKeyframeService.queue_keyframes()` queues start/end frame
  generation.
- `TimelineClipVideoReworkQueueService.queue_video_rework()` queues provider
  video generation.

The main gap is that these paths share references but not a strong prompt
contract. Keyframe generation currently wraps one clip prompt into generic
opening and ending instructions, while storyboard and video prompt helpers
already know more about `timeline_shot_plan`, prompt layers, and
`motion_timeline`.

## External Constraints

External provider documentation supports treating start/end frames and reference
images as first-class video controls:

- MiniMax documents text-to-video, image-to-video, first-and-last-frame video,
  and subject-reference video as distinct generation modes.
- Google Veo 3.1 documents first/last frame generation and reference-image
  guidance for generated video.
- BytePlus Seedance documentation describes first/last frame image-to-video,
  subject consistency, smooth transitions, multi-shot narrative behavior, and
  instruction following for camera and action prompts.

Design implication: the UI should not hide start/end frames as a secondary
button, and backend prompts should explicitly describe motion start, motion end,
camera language, subject continuity, and reference constraints.

Sources:

- https://platform.minimax.io/docs/guides/video-generation
- https://ai.google.dev/gemini-api/docs/video
- https://docs.byteplus.com/en/docs/ModelArk/1587798

## Design Principles

- Timeline remains the source of truth. Storyboard is a support view for the
  selected native Timeline video clip.
- One selected clip owns the production surface. Do not revive whole-Timeline
  storyboard generation.
- Manual reference control stays visible and explicit. Backend enrichment can
  add context, but it must not replace operator-selected reference images.
- The default video path should prefer start/end frames when available.
- Prompt building should be deterministic, inspectable, and testable without
  provider calls.
- Provider-specific capability differences should be represented through
  existing payload fields and fallback paths, not a new provider abstraction.

## Frontend Interaction

Keep the selected clip dock, but make the production path read as one clip
workflow:

1. Shared Reference Context
   - Surface selected role IPs, selected IP images, selected environment images,
     and manual reference URLs as a visible shared section.
   - Make it clear these references are included in storyboard, keyframe, and
     video tasks.
   - Keep all existing auto-default behavior for first IP image and first
     environment image.

2. Storyboard Step
   - Label as clip storyboard, not whole-story storyboard.
   - Keep style and panel count in compact details.
   - Show sheet preview and ready state when available.
   - Keep payload fields unchanged: `generation_profile="clip_storyboard"`,
     `reference_images`, `character_virtual_ip_ids`,
     `character_reference_images`, and `environment_reference_images`.

3. Start/End Keyframe Step
   - Show whether start frame and end frame are ready for the current clip.
   - Explain through state text that start/end frames are the recommended
     control input for provider video generation.
   - Generate keyframes with the same shared references as storyboard and video.
   - Keep endpoint and payload shape unchanged.

4. Video Step
   - Keep the primary action as "generate/rework this clip video".
   - Rename the prompt field to "motion prompt override" in UI copy.
   - If the field is empty, show that the backend will use Timeline shot-plan
     motion context.
   - Keep the reference-source select, but disable unavailable sources:
     `start_end` is disabled when no usable start frame exists;
     `clip_storyboard_panel` is disabled when no clip storyboard panel exists;
     `manual_refs` remains available only when manual reference URLs exist or
     selected shared references exist.
   - Preserve current payload compatibility. `manual_refs` still submits
     `reference_mode="start_end"` with `use_end_frame=false` so the backend
     treats the manual image list as image-to-video references rather than
     requiring generated keyframes.

## Backend Prompt Contract

Create a small shared prompt builder for Timeline clip visual production:

- Suggested file:
  `ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py`
- Inputs:
  - Timeline clip dict.
  - Optional operator prompt override.
  - Optional role: `start_frame`, `end_frame`, or `video_motion`.
- Data sources, in priority order:
  - operator prompt override,
  - `clip.source_refs.timeline_shot_plan`,
  - clip text fields (`ai_prompt`, `prompt`, `description`, `text`, `label`).

The builder should extract:

- `visual_prompt`,
- `video_prompt`,
- `direction_anchor`,
- `aesthetic_reference`,
- `shot_type`,
- `camera_movement`,
- `composition_geometry`,
- normalized `motion_timeline`,
- `emotional_landing`.

For start frames:

- emphasize the first motion point when available,
- preserve subject, wardrobe, environment, lens, lighting, and spatial direction,
- forbid text, subtitles, UI, logos, split screens, and multi-panel layouts.

For end frames:

- emphasize the final motion point and emotional landing when available,
- preserve the same continuity constraints as the start frame,
- state that this is the final state of the same shot, not a new scene.

For video motion:

- describe only the selected Timeline clip,
- include camera movement, motion timeline, and ending rhythm,
- tell the model to use reference images for identity, wardrobe, environment,
  composition, and lighting,
- forbid adding new characters, text overlays, extra cuts, storyboard gutters,
  or unrelated panels.

## Backend Integration

`TimelineClipKeyframeService`:

- Replace `_clip_keyframe_prompt()` and `_keyframe_prompts()` internals with the
  shared builder.
- Keep the public request and task payload shape unchanged.
- Add prompt metadata to the task payload for auditability:
  `visual_prompt_source`, `motion_prompt_source`, and
  `prompt_contract_version`.

`TimelineClipVideoReworkQueueService`:

- In the `start_end` path, use the shared video-motion prompt when no operator
  override is present.
- Continue to use clip storyboard panel prompts for
  `reference_mode="clip_storyboard_panel"`.
- Continue to use grid panel prompts only for legacy
  `reference_mode="storyboard_grid_panel"`.
- Keep `image_url`, `end_image_url`, `reference_images`, and
  `bound_context` behavior unchanged.

`timeline_clip_video_grid_reference.py`:

- Keep panel-specific prompts for storyboard panel reference modes.
- Do not broaden panel references into the default start/end frame path.

## Data And API Compatibility

No database migration is required.

No new API endpoint is required.

No request field needs to be removed. The frontend may add clearer UI state, but
it should keep the existing payload contracts:

- `TimelineClipStoryboardGenerateRequest`
- `TimelineClipKeyframeGenerateRequest`
- `TimelineClipVideoReworkTaskRequest`

Task payloads may add audit-only fields. Existing workers must ignore unknown
task payload keys unless explicitly consumed.

## Error Handling

- Missing Timeline context keeps the existing frontend warning.
- Invalid duration keeps the existing frontend warning.
- Stale Timeline version keeps backend `409 timeline version conflict`.
- Non-video clip keeps backend `400` responses.
- If `start_end` is selected but start frame is missing, frontend should disable
  the option when it can infer that state. Backend should retain the existing
  fallback requirement: video rework requires a prompt or start frame.
- If storyboard panel reference is selected but no sheet/panel exists, backend
  keeps `timeline clip missing clip storyboard panel`.

## Testing

Frontend tests:

- Update `ai-pic-frontend/tests/timelineClipReworkControls.test.ts`.
- Verify the shared reference section is visible outside collapsed parameter
  menus.
- Verify storyboard, keyframe, and video payloads carry the same selected IP,
  character image, environment image, and manual reference data.
- Verify video reference choices expose disabled or ready state for start/end
  and clip storyboard panel references.
- Verify the video prompt override label and empty-state copy.

Backend tests:

- Update `ai-pic-backend/tests/test_timeline_clip_keyframe_api.py`.
- Add a fixture clip with `timeline_shot_plan.motion_timeline`.
- Assert start and end frame prompts are different and include first/final
  motion points.
- Assert task payload includes prompt contract metadata.
- Update existing video rework tests to assert the default start/end path uses
  the shared motion prompt when no operator override is provided.
- Keep clip storyboard panel and legacy grid panel tests proving those reference
  modes still use panel-specific prompts.

Repository checks:

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `cd ai-pic-backend && pytest tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_grid_rework_api.py -v`
- `cd ai-pic-frontend && npm run lint`
- `cd ai-pic-frontend && npm run test -- timelineClipReworkControls.test.ts`

Browser validation:

- Required after implementation because the change affects visible media
  generation workflow.
- Preferred path is Chrome DevTools through the harness.
- Store evidence under `artifacts/runs/<run_id>/`.
- If Chrome transport fails, record the fallback engine explicitly.

## Non-Goals

- Do not add a new provider integration.
- Do not replace provider capability resolution.
- Do not remove manual reference image input.
- Do not make Storyboard the main orchestration center.
- Do not revive whole-Timeline storyboard generation.
- Do not alter render/export behavior.
- Do not change database schema.

## Rollout

Implement in small slices:

1. Backend prompt builder and tests.
2. Backend keyframe integration.
3. Backend video start/end prompt integration.
4. Frontend shared reference/status UI.
5. Frontend payload and behavior tests.
6. Browser workflow validation and ledger entry.

This order keeps the prompt contract testable before changing the visible UI.
