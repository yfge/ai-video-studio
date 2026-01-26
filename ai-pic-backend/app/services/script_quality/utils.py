from __future__ import annotations

import re

from app.services.script_quality.constants import DIALOGUE_RE, TAG_RE


def estimate_visible_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]", text))


def is_dialogue(line: str) -> tuple[bool, str | None, str | None]:
    m = DIALOGUE_RE.match(line.strip())
    if not m:
        return False, None, None
    speaker = m.group(1).strip()
    content = m.group(2).strip()
    return True, speaker, content


def collect_tags(line: str) -> list[str]:
    return [m.group(1).strip() for m in TAG_RE.finditer(line)]

