from typing import Any
from types import SimpleNamespace

import pytest

from app.services.script_agent import ScriptLangGraphAgent


@pytest.mark.unit
def test_script_agent_character_validation_ignores_functional_roles() -> None:
    agent = ScriptLangGraphAgent(SimpleNamespace())
    content: dict[str, Any] = {
        "dialogues": [
            {"character": "AP回归角色-20260618T164912", "content": "查原始文件。"},
            {"character": "客户", "content": "解释清楚。"},
            {"character": "助理", "content": "马上投屏。"},
            {"character": "团队成员A", "content": "不是我。"},
            {"character": "录音", "content": "数据我改了。"},
        ]
    }

    result = agent._validate_script_characters(
        content,
        [
            {
                "name": "AP回归角色-20260618T164912",
                "description": "项目负责人",
            }
        ],
    )

    assert result["character_validation_passed"] is True
    assert result["unknown_names"] == []
