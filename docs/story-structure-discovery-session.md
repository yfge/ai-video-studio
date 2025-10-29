# Story → Episode → Script Discovery Session

## Session Overview
- **Proposed slot:** 2025-10-30 09:00-10:00 CST (adjust once participant availability is confirmed)
- **Facilitator:** Backend/Architecture lead (proposed: Codex acting as scribe)
- **Objectives:**
  1. Align on how the existing Story → Episode → Script payloads map onto industrial Treatment / Step Outline / Scene / Shot layers.
  2. Lock required fields, enumerations, and versioning needs for each layer before schema work begins.
  3. Resolve sequencing and compatibility questions so migration and service refactors can start without blocking decisions.

## Participants & Roles
- Product owner / narrative director – confirms creative workflow requirements.
- Backend lead – validates data model and migration constraints.
- Frontend lead – ensures UI implications (script editor, storyboard tooling) are captured.
- Data/ML representative – covers prompt generation dependencies.
- QA / Ops – highlights testing and rollout considerations.

## Pre-Reads & Artifacts
- `docs/story-structure-gap-analysis.md` – current vs. target model comparison.
- `ai-pic-backend/app/models/script.py` & `app/models/story_structure.py` – existing SQLAlchemy models.
- `ai-pic-backend/scripts/prototype_story_structure_migration.py` – JSON extraction reference.
- Backlog reference: `task.md` → Feature “叙事结构与数据模型对齐”.

## Timeboxed Agenda (60 minutes)
1. **Context & Goals (0-10 min)** – Restate feature background, success metrics, and blocked decisions.
2. **Current Data Walkthrough (10-20 min)** – Review Story/Episode/Script JSON payloads and outstanding data quality issues.
3. **Target Layer Deep-Dive (20-35 min)** – For each of Treatment, Step Outline, Scene, Shot agree on mandatory fields, enumerations, and version hooks.
4. **Sequencing & Compatibility Decisions (35-50 min)** – Finalize migration phases, legacy API fallback strategy, and sequencing of backend/frontend updates.
5. **Action Items & Owners (50-60 min)** – Capture follow-ups, doc updates, and engineering start criteria.

## Required Field Checklist (Draft)
### Treatment
- `revision_number` (int, monotonic)
- `status` (enum: draft/review/approved/retired)
- `title`, `logline`, `theme_summary`
- `act_structure` (JSON: act-level beats)
- `target_audience_notes`, `tone_reference`
- `created_by`, `approved_by`, timestamps, soft-delete flag.

### Step Outline
- `sequence_number`, `act_label`
- `beat_title`, `beat_summary`, `dramatic_question`
- `characters_involved` (ordered list of story character IDs)
- `location_hint`, `duration_estimate_minutes`
- `status`, audit fields (`created_by`, `updated_by`).

### Scene
- `scene_number` (script scope unique), `slug_line` (INT/EXT + location + time)
- `environment_type` (enum), `location`, `time_of_day`
- `summary`, `page_length_eighths`
- `primary_characters` (ordered list with prominence weights)
- `conflict_notes`, `ai_prompt_snapshot`, `status`.

### Shot
- `shot_number` (scene scope unique), `shot_type` (enum), `camera_movement` (enum)
- `camera_setup`, `framing`, `focus_subject`
- `duration_seconds`, `lighting_notes`, `audio_notes`
- Optional FKs: `scene_beat_id`, `storyboard_frame_asset_id`
- `status`, audit timestamps, metadata JSON.

## Decisions & Recommendations (Pre-Session Draft)
- **Sequencing/Phasing:** roll out in three increments – (1) introduce Treatment + Step Outline tables with compatibility serializers, (2) migrate Scene/SceneBeat data with read/write dual-path, (3) add Shot planning + storyboard linkage. Each phase keeps legacy JSON columns readable for one release cycle.
- **API Compatibility:** expose normalized responses behind `?view=normalized` query flag while keeping existing JSON payloads; flag to default to normalized once frontend completes adoption.
- **Migration Backfill:** reuse `scripts/prototype_story_structure_migration.py` extraction paths; store original JSON snapshot in `extra_metadata` for audit and potential rollback.
- **Shared Scene/Shot Strategy:** prefer duplication with cross-reference metadata (`source_scene_id`) during MVP; investigate true reuse once governance/performance requirements are clear.

## Next Actions
- Circulate session invite (owner: product) and confirm attendees/slot.
- Prepare sample payloads from staging for walkthrough (owner: backend).
- Draft ER diagram updates ahead of session (owner: data architecture).
- Record all decisions in `docs/story-structure-gap-analysis.md` post-session and open tasks for migration/implementation.
