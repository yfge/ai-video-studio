# Generated DB Schema

Snapshot summary derived from current SQLAlchemy models and Alembic history.

## Core Models

- `users`
- `virtual_ips`
- `images`
- `scripts`
- `tasks`
- `video_generation_tasks`
- `story_novel_exports`
- `story_novel_chapters`
- `story_treatments`
- `story_step_outlines`
- `scenes`
- `scene_beats`
- `shots`
- `episode_characters`
- `media_assets`
- `timelines`
- `timeline_revisions`
- `timeline_clip_assets`
- `render_jobs`

## Migration Surface

- Initial migration: `919189f166fc_initial_migration.py`
- Story structure tables: `a1b2c3d4e5f6_add_story_structure_tables.py`
- Business id / soft delete: `b9b5c7e3a8d1_add_business_id_and_soft_delete.py`
- Episode characters: `3a9af7b70877_add_episode_characters_table.py`
- Video task metadata: `b4d2c8f1a7e9_add_generation_metadata_to_video_tasks.py`
- Timeline main chain tables: `8d1b6e2a4f90_add_timeline_main_chain_tables.py`
- Timeline revisions and lifecycle state: `a4f5c6d7e8f9_add_timeline_revisions_and_lifecycle.py`
- Timeline clip asset lineage: `c5e6f7a8b9c0_add_timeline_clip_assets.py`
- Story novel adaptation chain: `e6f7a8b9c0d1_add_story_novel_adaptation_chain.py`

## Narrative lineage

- `stories.workflow_mode` selects `direct` or `novel_adaptation_v1`;
  `stories.canonical_novel_export_id` points to the current approved revision.
- `story_novel_exports` stores revision lifecycle, Story snapshot, content hash,
  continuity evidence, adaptation plan, and approval evidence.
- `story_novel_chapters` stores ordered editable chapter checkpoints.
- `episodes.source_novel_export_id`, source business ID, and
  `source_chapter_refs` freeze the approved narrative lineage used by Script.

This file is intentionally compact; regenerate or expand it when schema-first tooling is added.
