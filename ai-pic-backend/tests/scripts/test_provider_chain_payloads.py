import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from tests.scripts.provider_chain_fixtures import provider_payload  # noqa: E402

from scripts.harness.provider_chain_payloads import (  # noqa: E402
    extract_structured_script,
)


def _fixture_script() -> dict:
    payload = provider_payload()
    return json.loads(payload["key_artifacts"]["script"]["raw_content"])


@pytest.mark.parametrize("field", ["question", "stakes", "opposition", "turn"])
def test_extract_structured_script_requires_scene_conflict_fields(field: str) -> None:
    script = _fixture_script()
    script["scenes"][0][field] = "  "

    with pytest.raises(ValueError, match=f"script_scene_1_missing_{field}"):
        extract_structured_script(json.dumps(script, ensure_ascii=False), 2)
