import re
from typing import Any, Dict

from .json_utils import extract_json_block


CHINESE_KEY_MAP = {
    "故事前提": "premise",
    "前提": "premise",
    "详细概要": "synopsis",
    "故事概要": "synopsis",
    "梗概": "synopsis",
    "主要冲突": "main_conflict",
    "冲突": "main_conflict",
    "解决方案": "resolution",
    "结局": "resolution",
    "角色关系": "character_relationships",
    "主角信息": "main_characters",
    "主要角色": "main_characters",
}


def normalize_story_json_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将包含中文键名的故事概念JSON映射到标准键：
    premise, synopsis, main_conflict, resolution, character_relationships, main_characters
    其他键保留原样，便于存入 extra_metadata。
    """
    if not isinstance(data, dict):
        return {}

    normalized: Dict[str, Any] = dict(data)

    # 映射中文键
    for zh_key, std_key in CHINESE_KEY_MAP.items():
        if zh_key in data and std_key not in normalized:
            normalized[std_key] = data.get(zh_key)

    return normalized


def extract_outline_from_text(text: str) -> Dict[str, Any]:
    """
    从自由文本中抽取故事概要关键字段（启发式）。
    支持识别类似：
    "故事前提：..."、"详细概要：..."、"主要冲突：..."、"解决方案：..."、"角色关系：..." 等段落。
    """
    fields = {
        "premise": None,
        "synopsis": None,
        "main_conflict": None,
        "resolution": None,
        "character_relationships": None,
        "main_characters": None,
    }

    # 以常见标题做分段
    sections = {
        "premise": [r"故事前提", r"前提"],
        "synopsis": [r"详细概要", r"故事概要", r"梗概"],
        "main_conflict": [r"主要冲突", r"冲突"],
        "resolution": [r"解决方案", r"结局"],
        "character_relationships": [r"角色关系"],
        "main_characters": [r"主角信息", r"主要角色"],
    }

    # 构造正则，找出每个段落
    for key, titles in sections.items():
        pattern = re.compile(
            r"(?:^|\n)\s*(?:"
            + "|".join(titles)
            + r")[：:]\s*(.+?)(?=\n\s*(?:"
            + "|".join(sum(sections.values(), []))
            + r")[：:]|\Z)",
            re.S,
        )
        m = pattern.search(text)
        if m:
            fields[key] = m.group(1).strip()

    # 若 synopsis 仍为空，用全文兜底
    if not fields["synopsis"]:
        fields["synopsis"] = text.strip()

    return fields
