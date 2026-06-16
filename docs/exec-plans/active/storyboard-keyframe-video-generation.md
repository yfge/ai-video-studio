# Storyboard Keyframe Video Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make selected Timeline clip storyboard, start/end keyframe, and provider video generation operate as one clear workflow with a shared prompt contract.

**Architecture:** Add a deterministic backend prompt builder for Timeline clip visual prompts, integrate it into keyframe and start/end video rework paths, then update the selected-clip frontend production dock to expose shared references, keyframe readiness, and reference-source availability. Keep all public API payload shapes stable and use audit-only task payload metadata for prompt provenance.

**Tech Stack:** FastAPI, SQLAlchemy repositories, Celery task payloads, pytest, Next.js 16 App Router, React Testing Library, node:test, repository docs and contract checks.

---

## Current Status

Implemented and validated on 2026-06-16. Delivery evidence is recorded in
`agent_chats/2026/06/16/2026-06-16T07-19-14Z-storyboard-keyframe-video-generation.md`.
The checklist below is preserved as the execution outline for traceability.

---

## Source Spec

Implement the approved scope from:

- `docs/design/storyboard-keyframe-video-generation.md`

Do not broaden beyond that design. In particular:

- Do not add provider integrations.
- Do not add a database migration.
- Do not revive whole-Timeline storyboard generation.
- Do not remove manual reference image control.

## File Structure

Backend:

- Create `ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py`
  - Owns deterministic prompt extraction and rendering for selected Timeline clip visual production.
  - Exposes keyframe frames, video-motion prompt, prompt source metadata, and prompt contract version.
- Create `ai-pic-backend/tests/unit/services/test_timeline_clip_visual_prompt_builder.py`
  - Unit tests for motion timeline extraction, distinct start/end prompts, override behavior, and video motion prompt constraints.
- Modify `ai-pic-backend/app/services/timeline_clip_keyframe_service.py`
  - Uses the shared prompt builder for `frames` and task prompt metadata.
- Modify `ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py`
  - Uses the shared builder for default `start_end` video prompt when no operator override is provided.
- Modify `ai-pic-backend/tests/test_timeline_clip_keyframe_api.py`
  - API-level proof that queued keyframe task payloads include prompt contract metadata and distinct motion-aware prompts.
- Modify `ai-pic-backend/tests/test_timeline_clip_video_rework_api.py`
  - API-level proof that default video rework uses the shared motion prompt and operator override still wins.

Frontend:

- Create `ai-pic-frontend/src/components/features/episode/TimelineClipSharedReferenceContext.tsx`
  - Visible shared reference summary and manual reference input for storyboard, keyframes, and video.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkModel.ts`
  - Adds selected-clip readiness helpers for start/end frames and reference-source availability.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx`
  - Computes readiness and reference availability, and passes shared reference props into cards.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx`
  - Renders shared reference context before the three generation actions.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipKeyframeCard.tsx`
  - Shows start/end readiness and recommended-use copy.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipVideoReworkCard.tsx`
  - Renames video prompt label to motion override and displays empty-state copy.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCardSections.tsx`
  - Disables unavailable video reference-source options and explains why.
- Modify `ai-pic-frontend/tests/timelineClipReworkControls.test.ts`
  - Tests visible shared references, keyframe readiness, disabled reference modes, prompt override copy, and stable payloads.

Docs and delivery:

- Modify `docs/README.md`
  - Index this active plan.
- Create the required timestamped ledger when production files under
  `ai-pic-backend/` or `ai-pic-frontend/` change. For a June 16, 2026 delivery,
  use a path such as
  `agent_chats/2026/06/16/2026-06-16T12-00-00Z-storyboard-keyframe-video-generation.md`.

## Task 1: Backend Prompt Builder Unit Tests

**Files:**

- Create: `ai-pic-backend/tests/unit/services/test_timeline_clip_visual_prompt_builder.py`
- Create in Task 2: `ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py`

- [ ] **Step 1: Write the failing unit tests**

Create `ai-pic-backend/tests/unit/services/test_timeline_clip_visual_prompt_builder.py`:

```python
from app.services.timeline_clip_visual_prompt_builder import (
    PROMPT_CONTRACT_VERSION,
    build_timeline_clip_keyframe_frames,
    build_timeline_clip_video_motion_prompt,
)


def clip_with_motion_plan() -> dict:
    return {
        "clip_id": "video_scene_001_beat_002_001",
        "track_type": "video",
        "text": "陈哲坐在车内，侧脸被手机屏照亮。",
        "source_refs": {
            "timeline_shot_plan": {
                "visual_prompt": "陈哲坐在雨夜车内，手机屏幕冷光照亮侧脸",
                "video_prompt": "镜头缓慢推近，雨水沿车窗滑落",
                "direction_anchor": "雨夜车内的迟疑与警觉",
                "aesthetic_reference": "live action cinema, cool neon rain",
                "shot_type": "tight medium close-up",
                "camera_movement": "slow push-in",
                "composition_geometry": "face on right third, window reflections left",
                "motion_timeline": [
                    {"at_ms": 0, "action": "他低头盯着手机屏幕"},
                    {"at_ms": 900, "action": "他的手指停在拨号键上"},
                    {"at_ms": 1800, "action": "他抬眼看向雨中的车窗"},
                ],
                "emotional_landing": "克制的怀疑落点",
            }
        },
    }


def test_keyframe_prompts_use_first_and_last_motion_points() -> None:
    frames, metadata = build_timeline_clip_keyframe_frames(clip_with_motion_plan())

    assert [frame["role"] for frame in frames] == ["start_frame", "end_frame"]
    assert "他低头盯着手机屏幕" in frames[0]["prompt"]
    assert "他抬眼看向雨中的车窗" in frames[1]["prompt"]
    assert frames[0]["prompt"] != frames[1]["prompt"]
    assert metadata["prompt_contract_version"] == PROMPT_CONTRACT_VERSION
    assert metadata["visual_prompt_source"] == "timeline_shot_plan.visual_prompt"
    assert metadata["motion_prompt_source"] == "timeline_shot_plan.video_prompt"


def test_video_motion_prompt_prefers_operator_override() -> None:
    prompt, metadata = build_timeline_clip_video_motion_prompt(
        clip_with_motion_plan(),
        override="只保留轻微呼吸和窗外雨滴，镜头固定",
    )

    assert "只保留轻微呼吸和窗外雨滴" in prompt
    assert "slow push-in" not in prompt
    assert metadata["motion_prompt_source"] == "operator_override"


def test_video_motion_prompt_without_override_keeps_motion_and_constraints() -> None:
    prompt, metadata = build_timeline_clip_video_motion_prompt(clip_with_motion_plan())

    assert "Generate only the selected Timeline clip" in prompt
    assert "slow push-in" in prompt
    assert "0ms: 他低头盯着手机屏幕" in prompt
    assert "1800ms: 他抬眼看向雨中的车窗" in prompt
    assert "No subtitles" in prompt
    assert metadata["prompt_contract_version"] == PROMPT_CONTRACT_VERSION
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.timeline_clip_visual_prompt_builder'`.

## Task 2: Backend Prompt Builder Implementation

**Files:**

- Create: `ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py`
- Test: `ai-pic-backend/tests/unit/services/test_timeline_clip_visual_prompt_builder.py`

- [ ] **Step 1: Implement the minimal prompt builder**

Create `ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py`:

```python
"""Prompt helpers for selected Timeline clip visual generation."""

from __future__ import annotations

from typing import Any, Mapping

from app.services.storyboard.grid_storyboard_prompt_layers import (
    motion_timeline_text,
    normalize_motion_timeline,
)

PROMPT_CONTRACT_VERSION = "timeline_clip_visual_prompt_v1"
INLINE_CONSTRAINTS = (
    "No subtitles, no speech bubbles, no readable UI text, no watermarks, "
    "no logos, no split-screen, no collage, no storyboard gutters."
)


def build_timeline_clip_keyframe_frames(
    clip: Mapping[str, Any],
    override: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    context = _prompt_context(clip, override)
    return [
        {"role": "start_frame", "prompt": _keyframe_prompt(context, "start_frame")},
        {"role": "end_frame", "prompt": _keyframe_prompt(context, "end_frame")},
    ], _metadata(context)


def build_timeline_clip_video_motion_prompt(
    clip: Mapping[str, Any],
    override: str | None = None,
) -> tuple[str, dict[str, str]]:
    context = _prompt_context(clip, override)
    if context["motion_prompt_source"] == "operator_override":
        prompt = context["motion_prompt"]
    else:
        prompt = _video_motion_prompt(context)
    return prompt, _metadata(context)


def _prompt_context(clip: Mapping[str, Any], override: str | None) -> dict[str, Any]:
    shot_plan = _timeline_shot_plan(clip)
    visual_prompt, visual_source = _first_text_with_source(
        ("timeline_shot_plan.visual_prompt", shot_plan.get("visual_prompt")),
        ("timeline_shot_plan.image_prompt", shot_plan.get("image_prompt")),
        *[(f"clip.{key}", clip.get(key)) for key in ("ai_prompt", "prompt", "description", "text", "label")],
    )
    override_text = _clean(override)
    if override_text:
        motion_prompt = override_text
        motion_source = "operator_override"
    else:
        motion_prompt, motion_source = _first_text_with_source(
            ("timeline_shot_plan.video_prompt", shot_plan.get("video_prompt")),
            ("timeline_shot_plan.visual_prompt", shot_plan.get("visual_prompt")),
            *[(f"clip.{key}", clip.get(key)) for key in ("video_prompt", "ai_prompt", "prompt", "description", "text", "label")],
        )
    return {
        "clip_id": _clean(clip.get("clip_id") or clip.get("id")) or "unknown",
        "visual_prompt": visual_prompt,
        "visual_prompt_source": visual_source,
        "motion_prompt": motion_prompt,
        "motion_prompt_source": motion_source,
        "direction_anchor": _clean(shot_plan.get("direction_anchor")),
        "aesthetic_reference": _clean(shot_plan.get("aesthetic_reference")),
        "shot_type": _clean(shot_plan.get("shot_type") or clip.get("shot_type")),
        "camera_movement": _clean(shot_plan.get("camera_movement") or clip.get("camera_movement")),
        "composition_geometry": _clean(shot_plan.get("composition_geometry") or clip.get("composition")),
        "motion_timeline": normalize_motion_timeline(shot_plan.get("motion_timeline")),
        "emotional_landing": _clean(shot_plan.get("emotional_landing")),
    }


def _keyframe_prompt(context: Mapping[str, Any], role: str) -> str:
    points = context.get("motion_timeline") or []
    point = points[0] if role == "start_frame" and points else points[-1] if points else {}
    label = "Opening keyframe" if role == "start_frame" else "Ending keyframe"
    state = "start state" if role == "start_frame" else "final state"
    lines = [
        f"{label} for selected Timeline clip {context['clip_id']}.",
        f"Show the {state} of the same shot, not a new scene.",
        f"Subject and visual plan: {context['visual_prompt']}",
        f"Motion intent: {context['motion_prompt']}",
    ]
    if point:
        lines.append(f"{label} motion beat: {point['at_ms']}ms: {point['action']}")
    for key, label_text in (
        ("direction_anchor", "Direction anchor"),
        ("aesthetic_reference", "Aesthetic reference"),
        ("shot_type", "Shot type"),
        ("camera_movement", "Camera movement"),
        ("composition_geometry", "Composition"),
        ("emotional_landing", "Emotional landing"),
    ):
        value = context.get(key)
        if value:
            lines.append(f"{label_text}: {value}")
    lines.append(
        "Preserve subject identity, wardrobe, environment, lens language, lighting, color temperature, and spatial direction."
    )
    lines.append(INLINE_CONSTRAINTS)
    return "\n".join(lines)


def _video_motion_prompt(context: Mapping[str, Any]) -> str:
    lines = [
        f"Generate only the selected Timeline clip {context['clip_id']}.",
        "Use reference images for identity, wardrobe, environment, composition, and lighting continuity.",
        f"Motion intent: {context['motion_prompt']}",
    ]
    if context.get("camera_movement"):
        lines.append(f"Camera movement: {context['camera_movement']}")
    motion = motion_timeline_text(context.get("motion_timeline") or [], separator=": ")
    if motion:
        lines.append(f"Motion timeline: {motion}")
    if context.get("emotional_landing"):
        lines.append(f"Ending rhythm and mood: {context['emotional_landing']}")
    lines.append("Avoid adding new characters, extra cuts, storyboard gutters, or unrelated panels.")
    lines.append(INLINE_CONSTRAINTS)
    return "\n".join(lines)


def _metadata(context: Mapping[str, Any]) -> dict[str, str]:
    return {
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "visual_prompt_source": str(context["visual_prompt_source"]),
        "motion_prompt_source": str(context["motion_prompt_source"]),
    }


def _timeline_shot_plan(clip: Mapping[str, Any]) -> Mapping[str, Any]:
    source_refs = clip.get("source_refs")
    if isinstance(source_refs, Mapping):
        shot_plan = source_refs.get("timeline_shot_plan")
        if isinstance(shot_plan, Mapping):
            return shot_plan
    return {}


def _first_text_with_source(*values: tuple[str, Any]) -> tuple[str, str]:
    for source, value in values:
        text = _clean(value)
        if text:
            return text, source
    return "", "empty"


def _clean(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""
```

- [ ] **Step 2: Run the unit tests and verify GREEN**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py -v
```

Expected: PASS.

## Task 3: Keyframe Queue Integration

**Files:**

- Modify: `ai-pic-backend/tests/test_timeline_clip_keyframe_api.py`
- Modify: `ai-pic-backend/app/services/timeline_clip_keyframe_service.py`
- Test: `ai-pic-backend/tests/test_timeline_clip_keyframe_api.py`

- [ ] **Step 1: Extend the API test for motion-aware task payloads**

In `test_timeline_clip_keyframes_creates_generation_task_for_selected_clip`, update the second video clip fixture so `source_refs.timeline_shot_plan` includes a motion plan:

```python
"source_refs": {
    "timeline_shot_plan": {
        "visual_prompt": "陈哲坐在雨夜车内，手机屏幕冷光照亮侧脸",
        "video_prompt": "镜头缓慢推近，雨水沿车窗滑落",
        "camera_movement": "slow push-in",
        "motion_timeline": [
            {"at_ms": 0, "action": "他低头盯着手机屏幕"},
            {"at_ms": 1200, "action": "他抬眼看向雨中的车窗"},
        ],
        "emotional_landing": "克制的怀疑落点",
    }
},
```

Add assertions after `params["frames"]` is read:

```python
assert params["prompt_contract_version"] == "timeline_clip_visual_prompt_v1"
assert params["visual_prompt_source"] == "timeline_shot_plan.visual_prompt"
assert params["motion_prompt_source"] == "operator_override"
assert "他低头盯着手机屏幕" in params["frames"][0]["prompt"]
assert "他抬眼看向雨中的车窗" in params["frames"][1]["prompt"]
assert params["frames"][0]["prompt"] != params["frames"][1]["prompt"]
```

Because the request currently sends `"prompt": "雨夜车内对峙"`, the expected motion source is `operator_override`.

- [ ] **Step 2: Run the API test and verify RED**

Run:

```bash
cd ai-pic-backend && pytest tests/test_timeline_clip_keyframe_api.py::test_timeline_clip_keyframes_creates_generation_task_for_selected_clip -v
```

Expected: FAIL because prompt metadata is absent and start/end prompts do not include the motion timeline beats.

- [ ] **Step 3: Integrate the prompt builder into keyframe service**

Modify imports in `ai-pic-backend/app/services/timeline_clip_keyframe_service.py`:

```python
from app.services.timeline_clip_visual_prompt_builder import (
    build_timeline_clip_keyframe_frames,
)
```

Replace local prompt construction inside `_task_payload`:

```python
frames, prompt_metadata = build_timeline_clip_keyframe_frames(
    clip,
    payload.prompt,
)
prompt = frames[0]["prompt"] if frames else None
if not prompt:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="clip keyframes require a prompt",
    )
```

Add metadata into the returned task payload:

```python
task_payload = {
    "kind": "timeline_clip_keyframes",
    "timeline_id": timeline.id,
    "timeline_business_id": timeline.business_id,
    "timeline_version": timeline.version,
    "expected_version": payload.expected_version,
    "clip_id": clip_id,
    "prompt": prompt,
    "model": payload.model,
    "generation_profile": payload.generation_profile,
    "size": payload.size,
    "aspect_ratio": payload.aspect_ratio,
    "width": payload.width,
    "height": payload.height,
    "reference_images": context.reference_images,
    "character_virtual_ip_ids": _dedupe_ints(payload.character_virtual_ip_ids or []),
    "character_reference_images": dedupe_strings(payload.character_reference_images or []),
    "environment_reference_images": dedupe_strings(payload.environment_reference_images or []),
    "bound_context": context.bound_context,
    "keyframe_roles": [frame["role"] for frame in frames],
    "frames": frames,
    **prompt_metadata,
}
return task_payload
```

Remove `_clip_keyframe_prompt()` and `_keyframe_prompts()` only after the test is green and no call sites remain.

- [ ] **Step 4: Run keyframe API and unit tests**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py tests/test_timeline_clip_keyframe_api.py -v
```

Expected: PASS.

## Task 4: Video Rework Start/End Prompt Integration

**Files:**

- Modify: `ai-pic-backend/tests/test_timeline_clip_video_rework_api.py`
- Modify: `ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py`
- Test: `ai-pic-backend/tests/test_timeline_clip_video_rework_api.py`

- [ ] **Step 1: Add RED test for default start/end video prompt**

In `_append_video_clip`, add a `timeline_shot_plan` source ref to the video clip:

```python
"source_refs": {
    "scene_beat_id": "beat_001",
    "audio_timeline_version": 1,
    "timeline_shot_plan": {
        "visual_prompt": "A rainy close-up of the lead character in a car.",
        "video_prompt": "The camera slowly pushes in while rain slides down the window.",
        "camera_movement": "slow push-in",
        "motion_timeline": [
            {"at_ms": 0, "action": "the lead looks down at a phone"},
            {"at_ms": 1200, "action": "the lead looks up toward the rain"},
        ],
        "emotional_landing": "quiet suspicion",
    },
},
```

Add a new test:

```python
def test_timeline_clip_video_rework_uses_shared_motion_prompt_without_override(
    client, db_session, monkeypatch
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["payload"] = payload

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_queue_service."
        "dispatch_timeline_clip_video_rework_task",
        fake_dispatch,
    )
    episode, script = _bootstrap_episode(db_session)
    start_asset = _media_asset(
        db_session,
        asset_type="image",
        origin="upload",
        file_url="https://example.com/start.png",
        mime_type="image/png",
    )
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clip(
            _timeline_spec(episode, script),
            clip_id=clip_id,
            start_asset=start_asset,
        ),
    )

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "resolution": "720p",
        },
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["prompt_contract_version"] == "timeline_clip_visual_prompt_v1"
    assert params["motion_prompt_source"] == "timeline_shot_plan.video_prompt"
    assert "Generate only the selected Timeline clip" in params["prompt"]
    assert "the lead looks down at a phone" in params["prompt"]
    assert "the lead looks up toward the rain" in params["prompt"]
    assert dispatched["payload"]["prompt"] == params["prompt"]
```

- [ ] **Step 2: Add test proving operator override still wins**

Extend `test_timeline_clip_video_rework_queues_provider_task`:

```python
assert params["motion_prompt_source"] == "operator_override"
assert params["prompt"] == "Regenerate the rainy close-up with steadier motion."
```

- [ ] **Step 3: Run video rework tests and verify RED**

Run:

```bash
cd ai-pic-backend && pytest tests/test_timeline_clip_video_rework_api.py -v
```

Expected: FAIL because prompt metadata is absent and default prompt still uses `clip_prompt`.

- [ ] **Step 4: Integrate the prompt builder into start/end video path**

Modify imports in `ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py`:

```python
from app.services.timeline_clip_visual_prompt_builder import (
    build_timeline_clip_video_motion_prompt,
)
```

Inside `_task_payload`, replace only the default `start_end` branch prompt calculation:

```python
else:
    prompt, prompt_metadata = build_timeline_clip_video_motion_prompt(
        clip,
        payload.prompt,
    )
    start_url = self._start_frame_url(clip)
    end_url = self._end_frame_url(clip) if payload.use_end_frame else None
```

Initialize `prompt_metadata = {}` before the branch, and add it to `task_payload`:

```python
task_payload = {
    "timeline_id": timeline.id,
    "timeline_business_id": timeline.business_id,
    "timeline_version": timeline.version,
    "clip_id": clip_id,
    "action": payload.action,
    "asset_role": payload.asset_role or "generated_video",
    "reason": payload.reason,
    "prompt": prompt,
    "image_url": start_url,
    "end_image_url": end_url,
    "duration": payload.duration or clip_duration_seconds(clip),
    "model": payload.model,
    "fps": payload.fps,
    "resolution": payload.resolution,
    "ratio": payload.ratio,
    "return_last_frame": payload.return_last_frame,
    "auto_render": True,
    "render_type": "final",
    "render_preset": render_preset(timeline),
    **prompt_metadata,
}
```

Do not apply this builder to `clip_storyboard_panel` or `storyboard_grid_panel`; those branches already render panel-specific prompts.

- [ ] **Step 5: Run backend prompt and video tests**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_grid_rework_api.py -v
```

Expected: PASS.

## Task 5: Frontend Shared Reference And Readiness Model Tests

**Files:**

- Modify: `ai-pic-frontend/tests/timelineClipReworkControls.test.ts`
- Modify during Task 6: `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkModel.ts`
- Create during Task 6: `ai-pic-frontend/src/components/features/episode/TimelineClipSharedReferenceContext.tsx`

- [ ] **Step 1: Add failing test for visible shared reference context**

Add a test near the existing reference visibility tests:

```typescript
it("shows shared references as a visible clip production context", async () => {
  const utils = render(
    React.createElement(TimelineClipProviderReworkControls, {
      timelineId: 8,
      timelineVersion: 3,
      clipId: "video_scene_1_beat_1_001",
      item: videoClipWithStoryboardPanel(),
      episodeCharacters: [episodeCharacter("快递员", 32)],
      storyboardCharacterImageOptions: {
        32: [{ url: "https://cdn.example/courier-pose.png", label: "快递员 正面" }],
      },
      storyboardEnvironmentImageOptions: [
        { url: "https://cdn.example/interior-env.png", label: "室内环境" },
      ],
    }),
    { container: dom.window.document.body },
  );

  await waitFor(() => assert.ok(utils.getByLabelText("片段共享参考上下文")));
  assert.equal(
    utils.getByLabelText("片段共享参考上下文").closest("[data-clip-parameter-details]"),
    null,
  );
  assert.ok(utils.getByText("会用于分镜、首尾帧和视频任务"));
  assert.ok(utils.getByText("角色 IP：快递员"));
  assert.ok(utils.getByText("IP 图：1 张"));
  assert.ok(utils.getByText("环境图：1 张"));
});
```

- [ ] **Step 2: Add failing test for keyframe readiness and disabled reference source**

Add a fixture:

```typescript
function videoClipWithoutStartEndFrames() {
  return {
    ...videoClipWithStoryboardPanel(),
    meta: {
      ...videoClipWithStoryboardPanel().meta,
      start_frame_asset_ref: undefined,
      end_frame_asset_ref: undefined,
    },
  };
}
```

Add a test:

```typescript
it("disables start-end video reference when keyframes are missing", () => {
  const utils = render(
    React.createElement(TimelineClipProviderReworkControls, {
      timelineId: 8,
      timelineVersion: 3,
      clipId: "video_scene_1_beat_1_001",
      item: videoClipWithoutStartEndFrames(),
    }),
    { container: dom.window.document.body },
  );

  assert.ok(utils.getByText("首尾帧待生成"));
  assert.equal(
    (utils.getByRole("option", { name: /首尾帧/ }) as HTMLOptionElement).disabled,
    true,
  );
});
```

- [ ] **Step 3: Add failing test for motion prompt override copy**

Add assertions in `renders storyboard reference and clip video as two separate cards`:

```typescript
assert.ok(utils.getByLabelText("运动提示词覆盖"));
assert.ok(utils.getByText("留空则使用 Timeline 镜头运动规划"));
```

- [ ] **Step 4: Run frontend test and verify RED**

Run:

```bash
cd ai-pic-frontend && npm run test -- timelineClipReworkControls.test.ts
```

Expected: FAIL because the shared context, readiness copy, disabled option, and renamed label do not exist yet.

## Task 6: Frontend Shared Reference And Readiness Implementation

**Files:**

- Create: `ai-pic-frontend/src/components/features/episode/TimelineClipSharedReferenceContext.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkModel.ts`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipKeyframeCard.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipVideoReworkCard.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCardSections.tsx`
- Test: `ai-pic-frontend/tests/timelineClipReworkControls.test.ts`

- [ ] **Step 1: Add selected-clip readiness helpers**

In `TimelineClipProviderReworkModel.ts`, add:

```typescript
export function timelineClipStartEndFrameStatus(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const startReady = hasAssetLocator(meta.start_frame_asset_ref) || Boolean(getString(meta.start_frame_url));
  const endReady = hasAssetLocator(meta.end_frame_asset_ref) || Boolean(getString(meta.end_frame_url));
  if (startReady && endReady) return { startReady, endReady, label: "首尾帧已生成" };
  if (startReady) return { startReady, endReady, label: "已有首帧" };
  if (endReady) return { startReady, endReady, label: "已有尾帧" };
  return { startReady, endReady, label: "首尾帧待生成" };
}

export function hasTimelineClipReferenceImages({
  manualReferenceImages,
  characterReferenceImages,
  environmentReferenceImages,
}: {
  manualReferenceImages: string[];
  characterReferenceImages: string[];
  environmentReferenceImages: string[];
}) {
  return (
    manualReferenceImages.length > 0 ||
    characterReferenceImages.length > 0 ||
    environmentReferenceImages.length > 0
  );
}
```

Add private `hasAssetLocator` using the same locator keys already used elsewhere:

```typescript
function hasAssetLocator(value: unknown) {
  const record = asRecord(value);
  return Boolean(
    getString(record?.file_url) ||
      getString(record?.url) ||
      getString(record?.image_url) ||
      getString(record?.file_path) ||
      typeof record?.media_asset_id === "number"
  );
}
```

- [ ] **Step 2: Create the shared reference context component**

Create `TimelineClipSharedReferenceContext.tsx`:

```tsx
"use client";

import type { EpisodeCharacter } from "@/utils/api/types";
import { episodeCharacterDisplayName } from "./episodeCharacterDisplay";

export function TimelineClipSharedReferenceContext({
  episodeCharacters,
  selectedCharacterVirtualIpIds,
  selectedCharacterReferenceUrls,
  selectedEnvironmentReferenceUrls,
  manualReferenceImages,
  onManualReferenceImagesChange,
}: {
  episodeCharacters: EpisodeCharacter[];
  selectedCharacterVirtualIpIds: number[];
  selectedCharacterReferenceUrls: string[];
  selectedEnvironmentReferenceUrls: string[];
  manualReferenceImages: string;
  onManualReferenceImagesChange: (value: string) => void;
}) {
  const labels = selectedCharacterVirtualIpIds.map((virtualIpId) => {
    const character = episodeCharacters.find((item) => item.virtual_ip_id === virtualIpId);
    return character ? episodeCharacterDisplayName(character) : `IP ${virtualIpId}`;
  });
  return (
    <section
      aria-label="片段共享参考上下文"
      className="mb-2 grid gap-2 rounded-md border border-slate-200 bg-white p-2 text-[11px] text-slate-700"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-slate-900">片段共享参考上下文</span>
        <span className="text-slate-500">会用于分镜、首尾帧和视频任务</span>
      </div>
      <div className="grid gap-1 min-[720px]:grid-cols-3">
        <span>角色 IP：{labels.length ? labels.join("、") : "未绑定"}</span>
        <span>IP 图：{selectedCharacterReferenceUrls.length} 张</span>
        <span>环境图：{selectedEnvironmentReferenceUrls.length} 张</span>
      </div>
      <label className="grid gap-1 text-xs text-slate-700">
        <span>手动参考图 URL（可选，一行一个）</span>
        <textarea
          aria-label="手动参考图 URL"
          value={manualReferenceImages}
          onChange={(event) => onManualReferenceImagesChange(event.currentTarget.value)}
          rows={2}
          className="resize-none rounded-md border border-slate-200 px-2 py-1.5 text-xs outline-none focus:border-slate-400"
          placeholder="https://..."
        />
      </label>
    </section>
  );
}
```

- [ ] **Step 3: Wire shared context and readiness through controls/cards**

In `TimelineClipProviderReworkControls.tsx`:

```typescript
const keyframeStatus = timelineClipStartEndFrameStatus(item);
const hasManualOrSharedReferences = hasTimelineClipReferenceImages({
  manualReferenceImages: referenceImages,
  characterReferenceImages: selectedCharacterReferenceImages,
  environmentReferenceImages: selectedEnvironmentReferenceImages,
});
const effectiveReferenceChoice =
  videoReferenceChoice === "clip_storyboard_panel" && !storyboardPanelIndex
    ? "start_end"
    : videoReferenceChoice === "start_end" && !keyframeStatus.startReady
      ? hasManualOrSharedReferences
        ? "manual_refs"
        : "start_end"
      : videoReferenceChoice;
```

Pass `keyframeStatus` and `hasManualOrSharedReferences` into `TimelineClipProviderReworkCards`.

- [ ] **Step 4: Render shared context and remove duplicate manual refs from storyboard card**

In `TimelineClipProviderReworkCards.tsx`, render `TimelineClipSharedReferenceContext` above the command grid and remove manual reference props from `StoryboardReferenceCard`.

Keep `StoryboardReferenceImageSelectors` visible in the storyboard reference card so IP/environment thumbnail selection remains near storyboard context.

- [ ] **Step 5: Show readiness in keyframe card**

In `TimelineClipKeyframeCard.tsx`, add props:

```typescript
keyframeStatus: { startReady: boolean; endReady: boolean; label: string };
```

Render:

```tsx
<div className="mt-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-slate-600">
  {keyframeStatus.label} · 推荐作为视频生成的首尾帧控制
</div>
```

- [ ] **Step 6: Rename video prompt label and disable unavailable reference sources**

In `TimelineClipVideoReworkCard.tsx`, change:

```tsx
<span>生成提示词</span>
```

to:

```tsx
<span>运动提示词覆盖</span>
```

Add helper copy below the textarea:

```tsx
<span className="text-[11px] text-slate-400">
  留空则使用 Timeline 镜头运动规划
</span>
```

In `VideoReferenceSelect`, accept:

```typescript
startEndAvailable: boolean;
manualRefsAvailable: boolean;
```

Disable options:

```tsx
<option value="start_end" disabled={!startEndAvailable}>首尾帧</option>
<option value="manual_refs" disabled={!manualRefsAvailable}>手动/共享参考图</option>
```

- [ ] **Step 7: Run frontend test**

Run:

```bash
cd ai-pic-frontend && npm run test -- timelineClipReworkControls.test.ts
```

Expected: PASS.

## Task 7: Full Focused Validation

**Files:**

- All files changed in Tasks 1-6.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_grid_rework_api.py -v
```

Expected: PASS.

- [ ] **Step 2: Run focused frontend tests**

Run:

```bash
cd ai-pic-frontend && npm run test -- timelineClipReworkControls.test.ts
```

Expected: PASS.

- [ ] **Step 3: Run frontend lint**

Run:

```bash
cd ai-pic-frontend && npm run lint
```

Expected: PASS.

- [ ] **Step 4: Run repo docs and contract checks**

Run:

```bash
python scripts/check_repo_docs.py
python scripts/check_repo_contracts.py --mode diff $(git diff --name-only -- docs ai-pic-backend ai-pic-frontend agent_chats)
git diff --check
```

Expected: PASS. If contract diff reports no changed-file rules, record that exact output in the ledger.

## Task 8: Browser Validation And Ledger

**Files:**

- Create: a UTC timestamped ledger path such as
  `agent_chats/2026/06/16/2026-06-16T12-00-00Z-storyboard-keyframe-video-generation.md`
  when the implementation is delivered on June 16, 2026.

- [ ] **Step 1: Run browser or harness validation**

Use the repo browser evidence policy. Preferred command:

```bash
RUN_ID="storyboard-keyframe-video-generation-$(date -u +%Y%m%dT%H%M%SZ)"
python scripts/harness/browser_flow.py --scenario episode_timeline_smoke --run-id "$RUN_ID"
```

`episode_timeline_smoke` is the closest current browser scenario for this UI
surface. It opens `/episodes/{episode_id}/workspace?tab=timeline` and validates
the Timeline workspace. Record the scenario gap if the harness cannot click
through selected-clip generation controls, and store evidence under
`artifacts/runs/$RUN_ID/`.

- [ ] **Step 2: Create the ledger entry**

Create an `agent_chats` entry with the required sections:

```markdown
---
id: storyboard-keyframe-video-generation
date: 2026-06-16T12:00:00Z
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - timeline
  - storyboard
  - keyframes
  - video-generation
related_paths:
  - ai-pic-backend/app/services/timeline_clip_visual_prompt_builder.py
  - ai-pic-backend/app/services/timeline_clip_keyframe_service.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
summary: Clip storyboard, start/end keyframe, and video generation interaction and prompt contract improvements.
---

## User Prompt

优化故事板，视频首尾帧，以及视频生成的交互，和相应的提示词生成逻辑 必要时上网查询相关内容

## Goals

- Clarify selected-clip storyboard, start/end keyframe, and video generation interaction.
- Build a shared backend prompt contract for keyframe and start/end video generation.
- Preserve existing API payload compatibility and manual reference control.

## Changes

- Added a backend prompt builder and integrated it into keyframe and start/end video rework queueing.
- Updated selected-clip frontend controls to show shared references, keyframe readiness, and reference-source availability.
- Added focused backend and frontend regression tests.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/test_timeline_clip_visual_prompt_builder.py tests/test_timeline_clip_keyframe_api.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_video_grid_rework_api.py -v`
- `cd ai-pic-frontend && npm run test -- timelineClipReworkControls.test.ts`
- `cd ai-pic-frontend && npm run lint`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only -- docs ai-pic-backend ai-pic-frontend agent_chats)`
- `git diff --check`
- `RUN_ID=storyboard-keyframe-video-generation-20260616T120000Z python scripts/harness/browser_flow.py --scenario episode_timeline_smoke --run-id "$RUN_ID"`

## Next Steps

- Review generated clips in a real provider-backed run when provider credentials and sample episode data are available.

## Linked Commits

- Pending
```

- [ ] **Step 3: Run final diff checks after ledger**

Run:

```bash
python scripts/check_repo_docs.py
python scripts/check_repo_contracts.py --mode diff $(git diff --name-only -- docs ai-pic-backend ai-pic-frontend agent_chats)
git diff --check
```

Expected: PASS.

## Completion Criteria

The implementation is complete only when all of the following are true:

- Backend keyframe tasks contain distinct, motion-aware start/end prompts.
- Backend video start/end rework uses the same motion prompt contract when no operator override is provided.
- Clip storyboard panel and legacy grid panel video reference modes still use panel-specific prompts.
- Frontend selected-clip production UI shows shared references, keyframe readiness, reference-source availability, and motion override copy.
- Existing payload contracts remain compatible.
- Focused backend tests pass.
- Focused frontend tests pass.
- Frontend lint passes.
- Repo docs, contract diff, and diff whitespace checks pass.
- Browser validation evidence is recorded or a documented fallback/gap is recorded.
- `agent_chats` ledger entry exists for the code changes.
