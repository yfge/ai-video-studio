from types import SimpleNamespace

from app.services import ai_manager_provider_selection as provider_selection


def _weight(
    *,
    weight: float = 1.0,
    priority: int = 2,
    current_requests: int = 0,
    max_requests_per_minute: int = 60,
    last_reset_time: float = 0.0,
):
    return SimpleNamespace(
        weight=weight,
        priority=SimpleNamespace(value=priority),
        current_requests=current_requests,
        max_requests_per_minute=max_requests_per_minute,
        last_reset_time=last_reset_time,
    )


def test_select_provider_prefers_explicit_provider():
    selected = provider_selection.select_provider(
        ["a", "b"],
        {},
        enable_load_balancing=True,
        default_priority_value=2,
        prefer_provider="b",
    )

    assert selected == "b"


def test_select_provider_uses_priority_when_load_balancing_disabled(monkeypatch):
    monkeypatch.setattr(provider_selection.random, "choice", lambda items: items[0])

    selected = provider_selection.select_provider(
        ["low", "high"],
        {"low": _weight(priority=3), "high": _weight(priority=1)},
        enable_load_balancing=False,
        default_priority_value=2,
    )

    assert selected == "high"


def test_select_by_weight_uses_weighted_cursor(monkeypatch):
    monkeypatch.setattr(provider_selection.random, "uniform", lambda _start, _end: 1.5)

    selected = provider_selection.select_by_weight(
        ["a", "b"],
        {"a": _weight(weight=1.0), "b": _weight(weight=2.0)},
    )

    assert selected == "b"


def test_check_rate_limit_resets_window(monkeypatch):
    monkeypatch.setattr(provider_selection.time, "time", lambda: 120.0)
    weights = {
        "a": _weight(
            current_requests=60,
            max_requests_per_minute=60,
            last_reset_time=0.0,
        )
    }

    assert provider_selection.check_rate_limit(weights, "a") is True
    assert weights["a"].current_requests == 0
    assert weights["a"].last_reset_time == 120.0


def test_update_request_count_increments_existing_provider():
    weights = {"a": _weight(current_requests=2)}

    provider_selection.update_request_count(weights, "a")
    provider_selection.update_request_count(weights, "missing")

    assert weights["a"].current_requests == 3
