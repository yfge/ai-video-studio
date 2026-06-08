"""Tests for video capabilities registry."""

from app.services.video.video_capabilities import (
    DEFAULT_CAPABILITY,
    CapabilityMatch,
    find_capability,
    get_allowed_durations,
    get_capability_summary,
    resolve_video_duration,
)


class TestFindCapability:
    """Test capability lookup."""

    def test_google_veo_31(self):
        """Test finding Veo 3.1 capability."""
        cap = find_capability(provider="google", model="veo-3.1-generate-preview")
        assert cap.provider == "google"
        assert "veo-3.1" in cap.model_pattern
        assert 4 in cap.allowed_durations
        assert 8 in cap.allowed_durations

    def test_google_veo_30(self):
        """Test finding Veo 3.0 capability."""
        cap = find_capability(provider="google", model="veo-3.0")
        assert cap.provider == "google"
        assert cap.allowed_durations == (8,)

    def test_google_veo_20(self):
        """Test finding Veo 2.0 capability."""
        cap = find_capability(provider="google", model="veo-2.0")
        assert cap.allowed_durations == (5, 6, 8)

    def test_keling(self):
        """Test finding Keling capability."""
        cap = find_capability(provider="keling", model="kling-v2-1")
        assert cap.provider == "keling"
        assert cap.allowed_durations == (5, 10)

    def test_minimax_hailuo(self):
        """Test finding MiniMax Hailuo capability."""
        cap = find_capability(provider="minimax", model="MiniMax-Hailuo-2.3")
        assert cap.provider == "minimax"
        assert cap.allowed_durations == (6, 10)

    def test_default_fallback(self):
        """Test default capability for unknown provider."""
        cap = find_capability(provider="unknown", model="some-model")
        assert cap == DEFAULT_CAPABILITY
        assert cap.allowed_durations == (4, 6, 8)

    def test_case_insensitive_provider(self):
        """Test provider matching is case-insensitive."""
        cap = find_capability(provider="GOOGLE", model="veo-3.1")
        assert cap.provider == "google"

    def test_case_insensitive_model(self):
        """Test model matching is case-insensitive."""
        cap = find_capability(provider="keling", model="KLING-V2-1")
        assert cap.provider == "keling"


class TestGetAllowedDurations:
    """Test allowed durations retrieval."""

    def test_basic_durations(self):
        """Test basic duration retrieval."""
        durations = get_allowed_durations(provider="keling", model="kling-v2")
        assert durations == [5, 10]

    def test_resolution_constraint(self):
        """Test Veo 3.1 at 1080p only supports 8s."""
        durations = get_allowed_durations(
            provider="google",
            model="veo-3.1-generate",
            resolution="1080p",
        )
        assert durations == [8]

    def test_resolution_without_constraint(self):
        """Test Veo 3.1 at 720p supports multiple durations."""
        durations = get_allowed_durations(
            provider="google",
            model="veo-3.1-generate",
            resolution="720p",
        )
        assert durations == [4, 6, 8]

    def test_resolution_normalization_from_wxh(self):
        """Test resolution normalization from WxH format."""
        durations = get_allowed_durations(
            provider="google",
            model="veo-3.1-generate",
            resolution="1920x1080",
        )
        assert durations == [8]


class TestResolveVideoDuration:
    """Test duration resolution with audit."""

    def test_exact_match(self):
        """Test when target matches allowed exactly."""
        result = resolve_video_duration(
            provider="keling",
            model="kling-v2",
            target_duration_seconds=5.0,
        )
        assert result.provider_duration_seconds == 5
        assert not result.needs_split
        assert result.capability_source == "keling/kling"

    def test_ceil_to_next_allowed(self):
        """Test ceiling to next allowed duration."""
        result = resolve_video_duration(
            provider="keling",
            model="kling-v2",
            target_duration_seconds=7.0,
        )
        assert result.provider_duration_seconds == 10
        assert not result.needs_split

    def test_below_minimum(self):
        """Test target below minimum is bumped to minimum."""
        result = resolve_video_duration(
            provider="minimax",
            model="hailuo-2.3",
            target_duration_seconds=3.0,
        )
        assert result.provider_duration_seconds == 6  # MiniMax min is 6

    def test_above_maximum_needs_split(self):
        """Test target above maximum marks needs_split."""
        result = resolve_video_duration(
            provider="keling",
            model="kling-v2",
            target_duration_seconds=15.0,
        )
        assert result.provider_duration_seconds == 10  # Max is 10
        assert result.needs_split

    def test_audit_notes_populated(self):
        """Test audit notes are populated."""
        result = resolve_video_duration(
            provider="google",
            model="veo-3.1",
            target_duration_seconds=5.0,
        )
        assert len(result.audit_notes) > 0

    def test_capability_source_with_resolution(self):
        """Test capability source includes resolution when constrained."""
        result = resolve_video_duration(
            provider="google",
            model="veo-3.1",
            target_duration_seconds=4.0,
            resolution="1080p",
        )
        assert "@1080p" in result.capability_source

    def test_returns_capability_match(self):
        """Test returns CapabilityMatch with all fields."""
        result = resolve_video_duration(
            provider="google",
            model="veo-3.1",
            target_duration_seconds=5.5,
        )
        assert isinstance(result, CapabilityMatch)
        assert result.provider == "google"
        assert result.model == "veo-3.1"
        assert result.target_duration_seconds == 5.5
        assert isinstance(result.allowed_durations, list)

    def test_invalid_target_defaults(self):
        """Test invalid target duration defaults to 5.0."""
        result = resolve_video_duration(
            provider="google",
            model="veo-3.1",
            target_duration_seconds="invalid",
        )
        assert result.target_duration_seconds == 5.0

    def test_negative_target_defaults(self):
        """Test negative target duration defaults to 5.0."""
        result = resolve_video_duration(
            provider="google",
            model="veo-3.1",
            target_duration_seconds=-5.0,
        )
        assert result.target_duration_seconds == 5.0


class TestGetCapabilitySummary:
    """Test capability summary."""

    def test_returns_all_providers(self):
        """Test summary includes all providers."""
        summary = get_capability_summary()
        assert "providers" in summary
        assert "google" in summary["providers"]
        assert "keling" in summary["providers"]
        assert "minimax" in summary["providers"]
        assert "volcengine" in summary["providers"]
        assert "default" in summary

    def test_google_has_multiple_entries(self):
        """Test Google has multiple capability entries."""
        summary = get_capability_summary()
        google = summary["providers"]["google"]
        assert len(google) >= 3  # veo-3.1, veo-3.0, veo-2.0

    def test_entries_have_required_fields(self):
        """Test each entry has required fields."""
        summary = get_capability_summary()
        for provider, entries in summary["providers"].items():
            for entry in entries:
                assert "pattern" in entry
                assert "durations" in entry


class TestEdgeCases:
    """Test edge cases."""

    def test_none_provider(self):
        """Test None provider uses default."""
        cap = find_capability(provider=None, model="any")
        assert cap == DEFAULT_CAPABILITY

    def test_empty_model(self):
        """Test empty model string."""
        cap = find_capability(provider="google", model="")
        # Should still match google but not any specific model
        assert cap.provider == "google" or cap == DEFAULT_CAPABILITY

    def test_whitespace_handling(self):
        """Test whitespace in provider/model is handled."""
        cap = find_capability(provider="  google  ", model="  veo-3.1  ")
        assert cap.provider == "google"
