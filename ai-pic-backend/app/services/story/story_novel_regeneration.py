"""Version-specific suffix invalidation for explicit chapter regeneration."""

from .story_novel_memory_context import mark_revision_ledger_stale
from .story_novel_plan_versions import is_v5_plan


def mark_regeneration_stale(revision, position, plan):
    if is_v5_plan(plan):
        from .story_novel_v5_resume import mark_v5_suffix_stale

        mark_v5_suffix_stale(revision, position)
        return
    mark_revision_ledger_stale(
        revision,
        from_position=position,
        archive_generation_calls=True,
    )
