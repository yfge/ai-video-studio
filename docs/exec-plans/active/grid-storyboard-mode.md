# Grid Storyboard Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional grid-storyboard mode that generates a multi-panel storyboard sheet from Timeline video clips and uses that sheet as a reference source for clip video generation, while preserving Timeline Spec v1 as the source of truth.

**Architecture:** Keep `Timeline` as the playable-output SSOT. The grid storyboard is a support-view artifact generated from Timeline video clips and their `timeline_shot_plan` prompt bundle. Store the sheet as a generated `media_assets` image, link each panel back to stable `clip_id`, and let provider-backed video generation use the sheet as a reference image with panel-specific prompts.

**Tech Stack:** FastAPI, SQLAlchemy repositories, Celery tasks, shared image generation normalization, provider-backed video task dispatch, Next.js episode workspace, pytest, Vitest/React tests, browser harness.

---

## Research Summary

External references checked on 2026-06-01:

- OpenAI Sora release notes say Storyboards let users build a video frame-by-frame or describe a scene and let Sora generate an editable storyboard. This validates an editable storyboard support layer instead of only free-form text.
  Source: https://help.openai.com/en/articles/12593142
- Runway Story Panels generates panel-style outputs from a starting image plus a prompt, specifically for filmmakers and storyboard artists. It outputs panels that carry a visual world forward.
  Source: https://help.runwayml.com/hc/en-us/articles/50985233945747-Story-Panels
- Runway's Image-to-Video guide frames the image as the first frame and recommends prompts focused on motion, camera work, and temporal progression. It also recommends continuing longer sequences by using the last frame of one generation as the next input.
  Source: https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide
- Kling's Start/End Frames guide confirms the common first/last-frame control pattern and warns that large start/end differences may trigger a shot switch.
  Source: https://kling.ai/quickstart/ai-video-start-end-frames
- Runway's Seedance 2.0 guide documents image/video/audio references, a References mode, a Start/End frames mode, and an explicit "Animating a storyboard" example using an image as a storyboard to guide scenes.
  Source: https://help.runwayml.com/hc/en-us/articles/50488490233363-Creating-with-Seedance-2-0
- Runway API docs for Seedance 2 state that text-to-video supports up to 9 reference images and video references for motion and continuity.
  Source: https://docs.dev.runwayml.com/guides/seedance/
- DreamShot and DrawVideo research both support the same architecture direction: split long video into controllable shots/keyframes, keep reference and prompt conditioning explicit, and synthesize clips between keyframes rather than relying on one unconstrained long prompt.
  Sources: https://arxiv.org/abs/2604.17195 and https://arxiv.org/abs/2605.23508

Design conclusion:

- Implement this as a new optional support mode, not as the primary story source.
- Generate one grid sheet from Timeline clips, but keep per-panel metadata and per-clip prompts in JSON.
- Use the grid sheet as provider reference input only when the selected provider/model supports references or storyboard-style inputs.
- Keep the existing per-clip start/end keyframe path as the fallback and quality baseline.

## Current Repo Facts

- Current main chain is Timeline-first; Storyboard is a support view. See `docs/timeline-rendering-pipeline.md`.
- Timeline shot plans live on video clips under `clip.source_refs.timeline_shot_plan`.
- Existing prompt split:
  - `timeline_shot_plan.visual_prompt` is close to still-image prompt intent.
  - `timeline_shot_plan.video_prompt` is close to image-to-video motion prompt intent.
  - storyboard support frames mirror these into `prompt_description` and `ai_prompt`.
- Existing media paths:
  - `storyboard_image_generation.py` already normalizes storyboard image generation through shared image-gen code.
  - `video_task_submission_helpers.py` already accepts `reference_images`.
  - `VideoTaskDispatcher` forwards unknown kwargs to providers, so provider-specific `reference_images` can be used if provider implementations support it.
  - Timeline clip rework does not yet expose `reference_images` or grid sheet references in `TimelineClipVideoReworkTaskRequest`.
- Existing UI:
  - `/episodes/{id}/workspace?tab=storyboard` is the support-view route.
  - `WorkspaceStoryboardTabContent.tsx` is currently read-only summary/list UI.

## Non-Goals

- Do not replace Timeline ordering, duration, render, export, or clip identity with storyboard frame order.
- Do not make a storyboard sheet the only video source. It is an optional reference mode.
- Do not revive the deleted standalone `/episodes/{id}/storyboard` route.
- Do not remove current start/end keyframe generation or per-clip video rework.
- Do not use one grid sheet blindly for all providers; gate it through model capability and fallback behavior.

## Data Contract

Add this support-view shape under `timeline.spec.support_views.storyboard_grid`:

```json
{
  "mode": "grid_storyboard.v1",
  "sheet": {
    "media_asset_id": 501,
    "file_url": "https://resource.example/storyboard-grid.png",
    "asset_role": "storyboard_grid_sheet",
    "panel_count": 9,
    "columns": 3,
    "rows": 3,
    "prompt_sha256": "..."
  },
  "panels": [
    {
      "panel_id": "grid_panel_001",
      "panel_index": 1,
      "row": 1,
      "column": 1,
      "clip_id": "video_scene_1_beat_1_001",
      "start_ms": 0,
      "end_ms": 5000,
      "visual_prompt": "...",
      "storyboard_panel_prompt": "...",
      "video_prompt": "..."
    }
  ],
  "generated_at": "2026-06-01T00:00:00Z",
  "source": "timeline_spec",
  "source_timeline_version": 2
}
```

Also add a clip-local reference for quick lookup:

```json
{
  "source_refs": {
    "grid_storyboard_panel": {
      "panel_id": "grid_panel_001",
      "panel_index": 1,
      "sheet_media_asset_id": 501,
      "source_timeline_version": 2
    }
  }
}
```

## File Structure

- Create `ai-pic-backend/app/services/storyboard/grid_storyboard_prompt_bridge.py`
  - Builds panel prompts from Timeline clips and `timeline_shot_plan`.
  - Produces a sheet prompt for image generation.
  - Produces a panel-specific video prompt for provider video generation.
- Create `ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_service.py`
  - Loads an accessible Timeline, validates version, generates the grid sheet image, persists it as `media_assets`, writes `support_views.storyboard_grid`, and records revisions.
- Create `ai-pic-backend/app/services/task_worker_grid_storyboard.py`
  - Celery task entrypoint for grid sheet generation.
- Modify `ai-pic-backend/app/services/task_worker.py`
  - Export/import the new task registration module.
- Modify `ai-pic-backend/app/schemas/timeline.py`
  - Add request/response schemas for grid sheet generation and grid-referenced clip video rework.
- Modify `ai-pic-backend/app/api/v1/endpoints/timelines.py`
  - Add `POST /api/v1/timelines/{timeline_id}/storyboard-grid/generate`.
  - Extend provider-backed clip video rework to accept grid storyboard reference fields.
- Modify `ai-pic-backend/app/services/timeline_clip_asset_candidates.py`
  - Recognize `storyboard_grid_sheet_asset_ref` as a non-render asset role.
- Modify `ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py`
  - Add grid reference payload construction.
- Modify `ai-pic-backend/app/services/video/video_task_timeline_rework_updater.py`
  - Preserve grid storyboard reference metadata on success lineage.
- Modify `ai-pic-backend/app/prompts/templates.py`
  - Register `STORYBOARD_GRID_SHEET` and `STORYBOARD_GRID_VIDEO`.
- Create `ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.txt`
  - Dedicated prompt template that allows a grid/contact-sheet output.
- Create `ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.yaml`
  - Prompt metadata.
- Create `ai-pic-backend/app/prompts/templates/storyboard_grid_video.txt`
  - Dedicated clip video prompt wrapper that tells the provider which panel to use.
- Create `ai-pic-backend/app/prompts/templates/storyboard_grid_video.yaml`
  - Prompt metadata.
- Modify `ai-pic-frontend/src/utils/api/types/timeline.types.ts`
  - Add grid storyboard API types.
- Modify `ai-pic-frontend/src/utils/api/endpoints/timeline.endpoints.ts`
  - Add `generateTimelineStoryboardGrid`.
- Modify `ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportModel.ts`
  - Parse grid sheet and panel metadata.
- Modify `ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx`
  - Add mode switch, grid sheet card, generate button, and per-panel video action.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx`
  - Add "use grid storyboard panel" option for selected clip rework when a sheet exists.
- Modify `ai-pic-frontend/src/components/features/episode/TimelineClipAssetAuditPanel.tsx`
  - Label `storyboard_grid_sheet`.
- Modify `scripts/harness/provider_chain_timeline.py`
  - Add optional grid storyboard generation step for provider-chain evidence.
- Modify `scripts/harness/provider_chain_media.py`
  - Add optional grid-reference video generation mode.
- Modify `scripts/harness/scenarios.py`
  - Strengthen `episode_workspace_storyboard_smoke` to check the grid mode controls.
- Create backend tests listed below.
- Create frontend tests listed below.
- Modify `docs/timeline-rendering-pipeline.md`
  - Document grid storyboard as optional support-view mode.
- Modify `docs/README.md`
  - Register this active plan.
- Create `agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-grid-storyboard-mode.md`
  - Required when implementation starts because backend/frontend/scripts code will change.

## Task 1: Prompt Bridge From Image Prompt To Storyboard Prompt

**Files:**

- Create: `ai-pic-backend/app/services/storyboard/grid_storyboard_prompt_bridge.py`
- Test: `ai-pic-backend/tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove a Timeline clip with `timeline_shot_plan` yields three linked prompt forms:

```python
def test_grid_panel_prompt_uses_timeline_shot_plan_prompt_bundle():
    spec = {
        "timeline_id": 9,
        "version": 2,
        "tracks": [
            {
                "track_type": "video",
                "clips": [
                    {
                        "clip_id": "video_scene_1_beat_1_001",
                        "track_type": "video",
                        "scene_id": 1,
                        "beat_id": "beat-1",
                        "start_ms": 0,
                        "end_ms": 5000,
                        "duration_ms": 5000,
                        "source_refs": {
                            "timeline_shot_plan": {
                                "plot": "女孩冲进雨夜巷口。",
                                "dialogue_source": "我必须找到他。",
                                "visual_prompt": "雨夜巷口，女孩握着手机奔跑，霓虹反光。",
                                "video_prompt": "手持镜头跟拍女孩冲进巷口，雨水溅起。",
                                "character_anchor": "短发女孩，蓝色外套",
                                "camera": "handheld tracking",
                                "action": "runs into the alley"
                            }
                        },
                    }
                ],
            }
        ],
    }

    panels = build_grid_storyboard_panels(spec, panel_count=4)

    assert panels[0]["clip_id"] == "video_scene_1_beat_1_001"
    assert panels[0]["visual_prompt"] == "雨夜巷口，女孩握着手机奔跑，霓虹反光。"
    assert "Panel 1" in panels[0]["storyboard_panel_prompt"]
    assert "video_scene_1_beat_1_001" in panels[0]["storyboard_panel_prompt"]
    assert panels[0]["video_prompt"] == "手持镜头跟拍女孩冲进巷口，雨水溅起。"
```

Add a fallback test for clips without `timeline_shot_plan`:

```python
def test_grid_panel_prompt_falls_back_to_clip_text_without_losing_clip_id():
    spec = {
        "tracks": [
            {
                "track_type": "video",
                "clips": [
                    {
                        "clip_id": "video_scene_1_beat_2_001",
                        "start_ms": 5000,
                        "end_ms": 9000,
                        "duration_ms": 4000,
                        "text": "男主推开仓库门。",
                    }
                ],
            }
        ]
    }

    panels = build_grid_storyboard_panels(spec, panel_count=4)

    assert panels[0]["clip_id"] == "video_scene_1_beat_2_001"
    assert "男主推开仓库门" in panels[0]["visual_prompt"]
    assert "Panel 1" in panels[0]["storyboard_panel_prompt"]
```

- [ ] **Step 2: Run and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py -q
```

Expected: import failure because `grid_storyboard_prompt_bridge.py` does not exist.

- [ ] **Step 3: Implement prompt bridge**

Create:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GridLayout:
    panel_count: int
    columns: int
    rows: int


def grid_layout(panel_count: int) -> GridLayout:
    if panel_count <= 2:
        return GridLayout(panel_count=2, columns=2, rows=1)
    if panel_count <= 4:
        return GridLayout(panel_count=4, columns=2, rows=2)
    if panel_count <= 6:
        return GridLayout(panel_count=6, columns=3, rows=2)
    return GridLayout(panel_count=9, columns=3, rows=3)


def build_grid_storyboard_panels(
    timeline_spec: dict[str, Any],
    *,
    panel_count: int,
) -> list[dict[str, Any]]:
    layout = grid_layout(panel_count)
    clips = _video_clips(timeline_spec)[: layout.panel_count]
    panels: list[dict[str, Any]] = []
    for index, clip in enumerate(clips, start=1):
        shot_plan = _shot_plan(clip)
        visual_prompt = _visual_prompt(clip, shot_plan)
        video_prompt = _video_prompt(clip, shot_plan, visual_prompt)
        panel = {
            "panel_id": f"grid_panel_{index:03d}",
            "panel_index": index,
            "row": ((index - 1) // layout.columns) + 1,
            "column": ((index - 1) % layout.columns) + 1,
            "clip_id": str(clip.get("clip_id") or ""),
            "start_ms": clip.get("start_ms"),
            "end_ms": clip.get("end_ms"),
            "duration_ms": clip.get("duration_ms"),
            "visual_prompt": visual_prompt,
            "storyboard_panel_prompt": (
                f"Panel {index}: clip_id={clip.get('clip_id')}. "
                f"{visual_prompt}"
            ),
            "video_prompt": video_prompt,
        }
        panels.append(panel)
    return panels


def build_grid_storyboard_sheet_prompt(
    panels: list[dict[str, Any]],
    *,
    style: str,
) -> str:
    layout = grid_layout(len(panels))
    panel_lines = "\n".join(
        f"{panel['panel_index']}. {panel['storyboard_panel_prompt']}"
        for panel in panels
    )
    return (
        f"Create a {layout.columns}x{layout.rows} vertical short-drama storyboard "
        f"sheet in {style}. Use clear gutters and left-to-right, top-to-bottom "
        "narrative order. Small panel numbers are allowed only in the panel border. "
        "No subtitles, speech bubbles, logos, watermarks, UI, or extra text inside "
        f"the images.\nPanels:\n{panel_lines}"
    )


def build_grid_storyboard_video_prompt(panel: dict[str, Any]) -> str:
    return (
        f"Use panel {panel['panel_index']} from the storyboard sheet as the visual "
        f"reference for clip_id={panel['clip_id']}. Generate only this shot. "
        f"{panel['video_prompt']}"
    )


def _video_clips(timeline_spec: dict[str, Any]) -> list[dict[str, Any]]:
    for track in timeline_spec.get("tracks") or []:
        if isinstance(track, dict) and (track.get("track_type") or track.get("type")) == "video":
            return [clip for clip in track.get("clips") or [] if isinstance(clip, dict)]
    return []


def _shot_plan(clip: dict[str, Any]) -> dict[str, Any]:
    refs = clip.get("source_refs") if isinstance(clip.get("source_refs"), dict) else {}
    plan = refs.get("timeline_shot_plan") if isinstance(refs, dict) else None
    return plan if isinstance(plan, dict) else {}


def _visual_prompt(clip: dict[str, Any], shot_plan: dict[str, Any]) -> str:
    return str(
        shot_plan.get("visual_prompt")
        or clip.get("ai_prompt")
        or clip.get("prompt")
        or clip.get("text")
        or clip.get("label")
        or ""
    ).strip()


def _video_prompt(
    clip: dict[str, Any],
    shot_plan: dict[str, Any],
    visual_prompt: str,
) -> str:
    return str(
        shot_plan.get("video_prompt")
        or clip.get("video_prompt")
        or visual_prompt
    ).strip()
```

- [ ] **Step 4: Run tests green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py -q
```

Expected: pass.

## Task 2: Dedicated Grid Storyboard Prompt Templates

**Files:**

- Modify: `ai-pic-backend/app/prompts/templates.py`
- Create: `ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.txt`
- Create: `ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.yaml`
- Create: `ai-pic-backend/app/prompts/templates/storyboard_grid_video.txt`
- Create: `ai-pic-backend/app/prompts/templates/storyboard_grid_video.yaml`
- Test: `ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py`

- [ ] **Step 1: Add prompt template tests**

Add:

```python
def test_storyboard_grid_sheet_template_allows_grid_but_limits_text():
    prompt = prompt_manager.render_prompt(
        "storyboard_grid_sheet",
        {
            "columns": 3,
            "rows": 3,
            "style": "3d_cartoon",
            "panel_lines": "1. Panel 1: clip_id=video_1. Girl runs.",
        },
    )

    assert "3x3" in prompt
    assert "panel numbers" in prompt.lower()
    assert "No subtitles" in prompt
    assert "contact sheet" in prompt.lower() or "storyboard sheet" in prompt.lower()


def test_storyboard_grid_video_template_points_to_one_panel():
    prompt = prompt_manager.render_prompt(
        "storyboard_grid_video",
        {
            "panel_index": 4,
            "clip_id": "video_scene_1_beat_4_001",
            "video_prompt": "Camera pushes in as the subject turns.",
        },
    )

    assert "panel 4" in prompt.lower()
    assert "video_scene_1_beat_4_001" in prompt
    assert "Generate only this shot" in prompt
```

- [ ] **Step 2: Run and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/test_storyboard_prompt_templates.py::test_storyboard_grid_sheet_template_allows_grid_but_limits_text tests/unit/test_storyboard_prompt_templates.py::test_storyboard_grid_video_template_points_to_one_panel -q
```

Expected: prompt template not found.

- [ ] **Step 3: Register templates**

Add enum values to `PromptTemplate`:

```python
STORYBOARD_GRID_SHEET = "storyboard_grid_sheet"
STORYBOARD_GRID_VIDEO = "storyboard_grid_video"
```

Create `storyboard_grid_sheet.txt`:

```jinja
Create a {{ columns }}x{{ rows }} storyboard sheet / contact sheet for a vertical short-drama production.
Style: {{ style }}.
Layout requirements:
- Use clear gutters between panels.
- Arrange panels left-to-right, top-to-bottom.
- Keep character identity, wardrobe, environment lighting, and spatial direction consistent.
- Small panel numbers are allowed only in the panel border.
- No subtitles, speech bubbles, logos, watermarks, UI, or extra text inside the images.

Panels:
{{ panel_lines }}
```

Create `storyboard_grid_video.txt`:

```jinja
Use panel {{ panel_index }} from the storyboard sheet as the visual reference for clip_id={{ clip_id }}.
Generate only this shot, not the whole storyboard sheet.
Use the panel for composition, character pose, wardrobe, lighting, and scene continuity.
Motion prompt:
{{ video_prompt }}
```

- [ ] **Step 4: Run tests green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/test_storyboard_prompt_templates.py -q
```

Expected: pass.

## Task 3: Backend Grid Sheet Generation Service

**Files:**

- Create: `ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_service.py`
- Modify: `ai-pic-backend/app/schemas/timeline.py`
- Modify: `ai-pic-backend/app/api/v1/endpoints/timelines.py`
- Create: `ai-pic-backend/tests/test_timeline_storyboard_grid_api.py`

- [ ] **Step 1: Add failing API tests**

Cover:

- rejects stale `expected_version`;
- rejects timelines without video clips;
- creates a task with `TaskType.STORYBOARD_IMAGE_GENERATION`;
- builds task payload with `timeline_id`, `timeline_version`, `panel_count`, `style`, and `sheet_prompt`;
- after the processor returns a fake image URL, persists `support_views.storyboard_grid` and increments Timeline version.

Run:

```bash
cd ai-pic-backend && pytest tests/test_timeline_storyboard_grid_api.py -q
```

Expected: route not found.

- [ ] **Step 2: Add request/response schemas**

Add to `timeline.py`:

```python
TimelineStoryboardGridStyle = Literal["2d_cartoon", "3d_cartoon", "live_action"]


class TimelineStoryboardGridGenerateRequest(TimelineVersionRequest):
    panel_count: int = Field(9, ge=2, le=9)
    style: TimelineStoryboardGridStyle = "3d_cartoon"
    model: Optional[str] = Field(None, max_length=128)
    generation_profile: Optional[str] = Field(None, max_length=128)
    size: Optional[str] = Field("1536x1536", max_length=32)
    aspect_ratio: Optional[str] = Field("1:1", max_length=32)
    reference_images: Optional[List[str]] = None


class TimelineStoryboardGridGenerateResponse(BaseModel):
    task_id: int
    status: str
```

- [ ] **Step 3: Add route**

Add:

```python
@router.post(
    "/timelines/{timeline_id}/storyboard-grid/generate",
    response_model=TimelineStoryboardGridGenerateResponse,
    summary="Queue grid storyboard sheet generation from Timeline clips",
)
def queue_timeline_storyboard_grid(
    timeline_id: int,
    payload: TimelineStoryboardGridGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineStoryboardGridGenerateResponse:
    service = TimelineStoryboardGridService(db)
    return service.queue_grid_sheet(timeline_id, payload, current_user)
```

- [ ] **Step 4: Implement service**

Implementation requirements:

- Use `TimelineRepository.get_accessible`.
- Enforce `timeline.version == payload.expected_version`.
- Use `build_grid_storyboard_panels()` and `build_grid_storyboard_sheet_prompt()`.
- Create a task with `TaskType.STORYBOARD_IMAGE_GENERATION`.
- Store parameters JSON:

```json
{
  "kind": "timeline_storyboard_grid",
  "timeline_id": 1,
  "timeline_version": 2,
  "expected_version": 2,
  "panel_count": 9,
  "style": "3d_cartoon",
  "model": "openai:gpt-image-2",
  "generation_profile": "storyboard_grid",
  "size": "1536x1536",
  "aspect_ratio": "1:1",
  "panels": [],
  "sheet_prompt": "..."
}
```

- Return `task_id` and status.

- [ ] **Step 5: Run route tests green**

Run:

```bash
cd ai-pic-backend && pytest tests/test_timeline_storyboard_grid_api.py -q
```

Expected: pass.

## Task 4: Celery Processor, Persistence, And Lineage

**Files:**

- Create: `ai-pic-backend/app/services/task_worker_grid_storyboard.py`
- Modify: `ai-pic-backend/app/services/task_worker.py`
- Modify: `ai-pic-backend/app/services/timeline_clip_asset_candidates.py`
- Modify: `ai-pic-backend/app/services/timeline_responses.py`
- Test: `ai-pic-backend/tests/unit/services/storyboard/test_grid_storyboard_sheet_processor.py`
- Test: `ai-pic-backend/tests/test_timeline_clip_asset_grid_storyboard.py`

- [ ] **Step 1: Add failing processor tests**

Assert the processor:

- calls the shared image generation path with the dedicated sheet prompt;
- persists the generated sheet as `media_assets(asset_type="image", origin="generated")`;
- writes `timeline.spec.support_views.storyboard_grid`;
- increments Timeline version;
- adds `source_refs.grid_storyboard_panel` to each mapped video clip;
- creates `timeline_clip_assets` rows with `asset_role="storyboard_grid_sheet"` and `source="grid_storyboard"`.

- [ ] **Step 2: Run and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_sheet_processor.py tests/test_timeline_clip_asset_grid_storyboard.py -q
```

Expected: import failure or missing asset role.

- [ ] **Step 3: Implement processor**

Processor behavior:

1. Load task and timeline.
2. Re-check expected version before mutation.
3. Call image generation using existing `generate_storyboard_image_urls()` or shared `normalize_image_gen_request()`.
4. Persist the selected sheet URL to `media_assets`.
5. Update Timeline spec and version through `TimelineRevisionService`.
6. Call `TimelineClipAssetLineageService.sync_timeline_assets`.
7. Mark task complete or failed.

Use this asset ref shape on clips:

```json
{
  "storyboard_grid_sheet_asset_ref": {
    "media_asset_id": 501,
    "file_url": "https://resource.example/storyboard-grid.png",
    "panel_id": "grid_panel_001",
    "panel_index": 1,
    "role": "storyboard_grid_sheet"
  }
}
```

- [ ] **Step 4: Extend candidate extraction**

In `timeline_clip_asset_candidates.py`, add:

```python
("storyboard_grid_sheet_asset_ref", "storyboard_grid_sheet")
```

This role must not be consumed as a renderable video or start frame by render code.

- [ ] **Step 5: Run tests green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/storyboard/test_grid_storyboard_sheet_processor.py tests/test_timeline_clip_asset_grid_storyboard.py -q
```

Expected: pass.

## Task 5: Use Grid Sheet In Clip Video Generation

**Files:**

- Modify: `ai-pic-backend/app/schemas/timeline.py`
- Modify: `ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py`
- Modify: `ai-pic-backend/app/services/video/video_task_timeline_rework_updater.py`
- Test: `ai-pic-backend/tests/test_timeline_clip_video_rework_api.py`
- Test: `ai-pic-backend/tests/unit/services/video/test_timeline_clip_video_rework_grid_reference.py`

- [ ] **Step 1: Add failing tests**

Add coverage for a request:

```json
{
  "expected_version": 3,
  "action": "re_cut",
  "reference_mode": "storyboard_grid_panel",
  "use_storyboard_grid": true,
  "model": "volcengine:doubao-seedance-2-0-260128"
}
```

Expected task payload:

```json
{
  "reference_mode": "storyboard_grid_panel",
  "reference_images": ["https://resource.example/storyboard-grid.png"],
  "storyboard_grid": {
    "panel_index": 4,
    "panel_id": "grid_panel_004",
    "sheet_media_asset_id": 501
  },
  "prompt": "Use panel 4 from the storyboard sheet as the visual reference..."
}
```

- [ ] **Step 2: Run and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/test_timeline_clip_video_rework_api.py tests/unit/services/video/test_timeline_clip_video_rework_grid_reference.py -q
```

Expected: schema rejects new fields.

- [ ] **Step 3: Extend schema**

Add to `TimelineClipVideoReworkTaskRequest`:

```python
reference_mode: Optional[Literal["start_end", "storyboard_grid_panel"]] = "start_end"
use_storyboard_grid: bool = False
reference_images: Optional[List[str]] = None
```

- [ ] **Step 4: Build grid reference payload**

In `TimelineClipVideoReworkQueueService._task_payload`:

- If `payload.use_storyboard_grid` is true:
  - load `clip.source_refs.grid_storyboard_panel`;
  - load `clip.storyboard_grid_sheet_asset_ref`;
  - set `reference_images=[sheet_url]`;
  - do not set `image_url` unless provider mode requires it;
  - wrap prompt through `build_grid_storyboard_video_prompt(panel)`.
- If grid metadata is missing, return HTTP 400 `timeline clip missing storyboard grid panel`.
- Keep existing start/end behavior as default.

- [ ] **Step 5: Preserve success metadata**

In the timeline rework updater, include:

```json
{
  "reference_mode": "storyboard_grid_panel",
  "storyboard_grid": {
    "panel_index": 4,
    "sheet_media_asset_id": 501
  }
}
```

inside the generated video media asset metadata and `timeline_clip_assets.source_ref`.

- [ ] **Step 6: Run tests green**

Run:

```bash
cd ai-pic-backend && pytest tests/test_timeline_clip_video_rework_api.py tests/unit/services/video/test_timeline_clip_video_rework_grid_reference.py -q
```

Expected: pass.

## Task 6: Frontend Workspace Mode

**Files:**

- Modify: `ai-pic-frontend/src/utils/api/types/timeline.types.ts`
- Modify: `ai-pic-frontend/src/utils/api/endpoints/timeline.endpoints.ts`
- Modify: `ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportModel.ts`
- Modify: `ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx`
- Modify: `ai-pic-frontend/src/components/features/episode/TimelineClipAssetAuditPanel.tsx`
- Test: `ai-pic-frontend/src/components/features/episode/__tests__/WorkspaceStoryboardSupportModel.test.ts`
- Test: `ai-pic-frontend/src/components/features/episode/__tests__/WorkspaceStoryboardTabContent.test.tsx`

- [ ] **Step 1: Add model tests**

Assert `buildStoryboardSupportSummary()` returns grid metadata:

```ts
expect(summary.gridSheetUrl).toBe("https://resource.example/grid.png");
expect(summary.gridPanelCount).toBe(9);
expect(frames[0].gridPanelIndex).toBe(1);
```

- [ ] **Step 2: Add API client types**

Add:

```ts
export type TimelineStoryboardGridGenerateRequest = {
  expected_version: number;
  panel_count?: number;
  style?: "2d_cartoon" | "3d_cartoon" | "live_action";
  model?: string;
  generation_profile?: string;
  size?: string;
  aspect_ratio?: string;
  reference_images?: string[];
};

export type TimelineStoryboardGridGenerateResponse = {
  task_id: number;
  status: string;
};
```

Add endpoint:

```ts
export async function generateTimelineStoryboardGrid(
  timelineId: number | string,
  payload: TimelineStoryboardGridGenerateRequest,
): Promise<ApiResponse<TimelineStoryboardGridGenerateResponse>> {
  return httpClient<TimelineStoryboardGridGenerateResponse>(
    `/api/v1/timelines/${timelineId}/storyboard-grid/generate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
```

- [ ] **Step 3: Add UI controls**

In the storyboard workspace:

- Add a segmented control: `逐镜头` / `宫格故事板`.
- Show current grid sheet preview if present.
- Add `生成宫格图` button when a selected Timeline exists.
- Show panel list with `clip_id`, timecode, and prompt preview.
- Disable generate if no Timeline or no video clips.
- After task creation, show `task_id` and link to `/tasks`.

- [ ] **Step 4: Add clip video rework option**

In `TimelineClipProviderReworkControls.tsx`:

- If selected clip has `source_refs.grid_storyboard_panel`, show checkbox `使用宫格故事板 Panel N`.
- When enabled, send `use_storyboard_grid: true` and `reference_mode: "storyboard_grid_panel"`.

- [ ] **Step 5: Run frontend tests**

Run:

```bash
cd ai-pic-frontend && npm run test -- WorkspaceStoryboardSupportModel WorkspaceStoryboardTabContent
```

Expected: pass.

## Task 7: Harness And Evidence

**Files:**

- Modify: `scripts/harness/provider_chain_timeline.py`
- Modify: `scripts/harness/provider_chain_media.py`
- Modify: `scripts/harness/provider_chain_regression.py`
- Modify: `scripts/harness/scenarios.py`
- Test: `ai-pic-backend/tests/scripts/test_provider_chain_regression.py`
- Test: `ai-pic-backend/tests/scripts/test_provider_chain_media.py`

- [ ] **Step 1: Add harness flags**

Add:

```text
--storyboard-mode per-clip|grid
--storyboard-grid-panel-count 2|4|6|9
--storyboard-grid-model <provider:model>
```

- [ ] **Step 2: Add grid chain evidence fields**

Provider chain JSON must include:

```json
{
  "key_artifacts": {
    "storyboard_grid": {
      "timeline_id": 1,
      "timeline_version": 3,
      "sheet_media_asset_id": 501,
      "sheet_url": "https://...",
      "panel_count": 9,
      "clip_ids": ["video_scene_1_beat_1_001"]
    }
  },
  "videos": [
    {
      "prompt_source": "storyboard_grid.panel.video_prompt",
      "reference_mode": "storyboard_grid_panel",
      "storyboard_grid_panel_index": 1
    }
  ]
}
```

- [ ] **Step 3: Add browser smoke coverage**

Update `episode_workspace_storyboard_smoke` required text to include the grid mode label once the UI lands.

- [ ] **Step 4: Run script tests**

Run:

```bash
cd ai-pic-backend && pytest tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_media.py -q
```

Expected: pass.

## Task 8: Docs And Task State

**Files:**

- Modify: `docs/timeline-rendering-pipeline.md`
- Modify: `docs/README.md`
- Modify: `tasks.md` only if this becomes part of the active 6-week product board.
- Create: `agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-grid-storyboard-mode.md`

- [ ] **Step 1: Document support-view contract**

Add a `Grid Storyboard Support Mode` subsection to `docs/timeline-rendering-pipeline.md`:

- grid sheet is optional support view;
- sheet is generated from Timeline video clips;
- sheet can guide provider video generation;
- Timeline remains final source for order, duration, asset selection, render, and export;
- provider fallback must preserve existing per-clip start/end mode.

- [ ] **Step 2: Register implementation notes**

Update `docs/README.md` if the active plan path changes or if a durable design doc is added.

- [ ] **Step 3: Add ledger**

Use the required sections:

```markdown
## User Prompt
## Goals
## Changes
## Validation
## Next Steps
## Linked Commits
```

Record external research URLs, commands, and any browser/provider evidence.

## Validation Matrix

Backend targeted:

```bash
cd ai-pic-backend && pytest \
  tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py \
  tests/unit/services/storyboard/test_grid_storyboard_sheet_processor.py \
  tests/test_timeline_storyboard_grid_api.py \
  tests/test_timeline_clip_asset_grid_storyboard.py \
  tests/unit/services/video/test_timeline_clip_video_rework_grid_reference.py \
  tests/test_timeline_clip_video_rework_api.py -q
```

Backend policy:

```bash
python scripts/check_repo_contracts.py --mode diff \
  ai-pic-backend/app/services/storyboard/grid_storyboard_prompt_bridge.py \
  ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_service.py \
  ai-pic-backend/app/services/task_worker_grid_storyboard.py \
  ai-pic-backend/app/schemas/timeline.py \
  ai-pic-backend/app/api/v1/endpoints/timelines.py
```

Frontend targeted:

```bash
cd ai-pic-frontend && npm run lint
cd ai-pic-frontend && npm run test -- WorkspaceStoryboardSupportModel WorkspaceStoryboardTabContent
```

Harness/browser:

```bash
python scripts/harness/browser_flow.py \
  --scenario episode_workspace_storyboard_smoke \
  --run-id grid-storyboard-smoke-<timestamp> \
  --base-url http://localhost:8089 \
  --episode-id <episode_id>
```

Provider-backed low-frequency proof:

```bash
python scripts/harness/provider_chain_regression.py \
  --mode smoke \
  --storyboard-mode grid \
  --storyboard-grid-panel-count 4 \
  --run-id provider-chain-grid-storyboard-smoke-<timestamp> \
  --api-url http://localhost:8000 \
  --episode-id <episode_id> \
  --script-id <script_id> \
  --timeout-seconds 1200
```

## Acceptance Criteria

- A user can generate a grid storyboard sheet from Timeline video clips.
- The generated sheet is stored as a `media_assets` image and linked to stable `clip_id` panels.
- The prompt path is connected:
  - Timeline clip / `timeline_shot_plan.visual_prompt`
  - grid panel prompt
  - sheet image prompt
  - grid-referenced video prompt
  - provider video request metadata
- A selected video clip can queue provider-backed video generation using its grid panel as reference.
- Existing per-clip start/end frame generation still works and remains the fallback.
- Render/export still reads Timeline video assets and does not use storyboard frame order as the source of truth.
- Frontend exposes the mode only inside the episode workspace support view.
- Provider-chain evidence records whether video generation used `storyboard_grid_panel` or `start_end`.

## Risks And Mitigations

- Provider may animate the whole sheet instead of one panel.
  - Mitigation: panel-specific prompt wrapper, explicit `Generate only this shot`, provider allowlist, and fallback to per-clip start/end mode.
- Grid sheet text can pollute video output.
  - Mitigation: allow only small border panel numbers; prohibit subtitles, speech bubbles, logos, UI, and in-image labels.
- Same sheet asset linked to many clips may confuse render readiness.
  - Mitigation: use separate `storyboard_grid_sheet` role that render code ignores.
- Large panel count can reduce panel fidelity.
  - Mitigation: support 2/4/6/9 panels and default to 4 for provider proof; 9 is for planning/reference only.
- Real provider cost and moderation can block live validation.
  - Mitigation: unit/API tests with mocked providers first; live proof remains a low-frequency harness gate and records provider-blocked separately.

## Commit Plan

1. `docs: plan grid storyboard mode`
   - This plan and docs index only.
2. `feat(backend): add grid storyboard prompt bridge`
   - Task 1 and Task 2.
3. `feat(backend): generate timeline grid storyboard sheets`
   - Task 3 and Task 4.
4. `feat(backend): support grid storyboard video references`
   - Task 5.
5. `feat(frontend): expose grid storyboard workspace mode`
   - Task 6.
6. `test(harness): add grid storyboard provider evidence`
   - Task 7 and docs/ledger updates.
