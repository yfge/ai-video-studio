import json
from types import SimpleNamespace

from app.services.storyboard.clip_storyboard_approved_style_anchor import (
    apply_approved_3d_style_anchor,
)
from app.services.storyboard.clip_storyboard_context import ClipStoryboardContext


def test_approved_sheet_replaces_photoreal_refs_for_matching_3d_cast(monkeypatch):
    module = __import__(
        "app.services.storyboard.clip_storyboard_approved_style_anchor",
        fromlist=["unused"],
    )
    link = SimpleNamespace(
        asset_role="generated_video",
        source_ref={
            "reference_mode": "clip_storyboard_sheet",
            "clip_storyboard": {"sheet_media_asset_id": 513},
        },
    )
    sheet = SimpleNamespace(
        id=513,
        is_deleted=False,
        file_url="https://example.com/approved-grid.png",
        file_path=None,
        extra_metadata={"task_id": 6360},
    )
    task = SimpleNamespace(
        parameters=json.dumps(
            {
                "style": "3d_cartoon",
                "bound_context": {"characters": [{"name": "老拐"}, {"name": "阿盖儿"}]},
            },
            ensure_ascii=False,
        )
    )
    monkeypatch.setattr(
        module,
        "TimelineClipAssetRepository",
        lambda db: SimpleNamespace(list_for_timeline=lambda **kwargs: [link]),
    )
    monkeypatch.setattr(
        module,
        "MediaAssetRepository",
        lambda db: SimpleNamespace(get_by_id=lambda asset_id: sheet),
    )
    monkeypatch.setattr(
        module,
        "TaskRepository",
        lambda db: SimpleNamespace(get_by_id=lambda task_id: task),
    )
    context = ClipStoryboardContext(
        bound_context={"characters": [{"name": "阿盖儿"}]},
        reference_images=["https://example.com/photoreal-person.png"],
        panels=[{"panel_index": 1, "bound_context": {}}],
    )

    result = apply_approved_3d_style_anchor(
        object(),
        timeline_id=69,
        style="3d_cartoon",
        context=context,
    )

    assert result.reference_images == ["https://example.com/approved-grid.png"]
    assert result.bound_context["approved_style_anchor"] == {
        "media_asset_id": 513,
        "character_names": ["老拐", "阿盖儿"],
    }
    assert result.panels[0]["bound_context"] == result.bound_context
