from app.services.providers.minimax_provider.video_resolution import (
    normalize_minimax_video_resolution,
)


def test_hailuo_23_maps_generic_720p_to_supported_768p():
    assert normalize_minimax_video_resolution("MiniMax-Hailuo-2.3", "720p") == ("768P")
    assert (
        normalize_minimax_video_resolution("MiniMax-Hailuo-2.3-Fast", "1280x720")
        == "768P"
    )


def test_preserves_explicit_or_other_model_resolutions():
    assert normalize_minimax_video_resolution("MiniMax-Hailuo-2.3", "1080P") == (
        "1080P"
    )
    assert normalize_minimax_video_resolution("T2V-01", "720P") == "720P"
