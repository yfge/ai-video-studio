from copy import deepcopy

import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_normalize_contract_canonicalizes_beat_type_aliases():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["dramatic_role"] = "conflict_escalation"
    aliases = {
        "action": "transition",
        "escalation": "conflict",
        "reaction": "transition",
        "discovery": "reveal",
        "confirmation": "reveal",
        "decision": "transition",
        "investigation": "setup",
        "revelation": "reveal",
    }
    scene["beats"] = []
    for order_index, raw_type in enumerate(aliases, start=1):
        beat = deepcopy(_valid_contract()["scenes"][0]["beats"][0])
        beat["order_index"] = order_index
        beat["beat_type"] = raw_type
        scene["beats"].append(beat)

    contract = normalize_script_beat_contract(payload)

    assert contract.scenes[0].dramatic_role == "escalation"
    assert [beat.beat_type for beat in contract.scenes[0].beats] == list(
        aliases.values()
    )


@pytest.mark.unit
def test_normalize_contract_defaults_unknown_non_empty_beat_type():
    payload = _valid_contract()
    payload["scenes"][0]["beats"][0]["beat_type"] = "vibes"

    contract = normalize_script_beat_contract(payload)

    assert contract.scenes[0].beats[0].beat_type == "conflict"


@pytest.mark.unit
def test_normalize_contract_defaults_unknown_non_empty_dramatic_role():
    payload = _valid_contract()
    payload["scenes"][0]["dramatic_role"] = "vibes"

    contract = normalize_script_beat_contract(payload)

    assert contract.scenes[0].dramatic_role == "escalation"
