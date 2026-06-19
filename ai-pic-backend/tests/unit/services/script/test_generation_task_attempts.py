import pytest

from app.services.script.generation_attempt_contract import attempt_temperature


@pytest.mark.unit
def test_attempt_temperature_preserves_first_attempt_and_cools_rewrites():
    assert attempt_temperature(1, 0.7) == 0.7
    assert attempt_temperature(2, 0.7) == 0.35
    assert attempt_temperature(3, 0.2) == 0.2
    assert attempt_temperature(2, "bad") == 0.35
