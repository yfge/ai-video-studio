"""Audio timeline -> storyboard visual prompt helpers.

Goal:
- Keep storyboard `description` suitable for UI (may include dialogue text).
- Generate a separate, *visual-only* prompt description for AI generation:
  - No literal dialogue lines (avoid subtitles/reading).
  - No readable screen text (avoid model hallucinated UI text).
  - Dialogue beats should explicitly describe speaking/lip movement.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate


_QUOTED_TEXT_RE = re.compile(r"[\"“”‘’「」『』](?P<body>.{1,120}?)[\"“”‘’「」『』]")
_FILE_LIKE_RE = re.compile(
    r"(?P<name>[\w\u4e00-\u9fff\-\_]{1,60})\.(?:pdf|docx?|txt|pptx?|xlsx?|png|jpe?g|webp|mp3|mp4)",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r"\s+")


def _compact(text: str) -> str:
    return _MULTI_SPACE_RE.sub(" ", (text or "").strip())


def _strip_quoted_text(text: str) -> str:
    """Replace quoted/screen text with a generic placeholder."""
    if not text:
        return ""
    return _QUOTED_TEXT_RE.sub("（内容模糊不可读）", text)


def _strip_file_like_tokens(text: str) -> str:
    if not text:
        return ""
    return _FILE_LIKE_RE.sub("（文件/附件）", text)


def _looks_like_document_read(text: str) -> bool:
    if not isinstance(text, str):
        return False
    t = text.strip()
    if not t:
        return False
    if "_" in t:
        return True
    lowered = t.lower()
    if ".pdf" in lowered or ".doc" in lowered:
        return True
    keywords = ("离婚协议", "草案", "条款", "净身出户", "虚构债务", "附件")
    return any(k in t for k in keywords)


def _infer_dialogue_intent(text: str) -> Optional[str]:
    t = (text or "").strip()
    if not t:
        return None
    if "？" in t or "?" in t:
        return "疑问/追问"
    if "！" in t or "!" in t:
        return "情绪激烈"
    if any(k in t for k in ("不是", "没有", "别误会")):
        return "解释/辩解"
    if any(k in t for k in ("你从什么时候", "你到底", "算计")):
        return "质问/指控"
    return None


def build_visual_prompt_description(
    *,
    beat_type: str,
    speaker_name: str | None,
    text: str | None,
    dialogue_action: Any = None,
) -> str:
    """Build a visual-only description for storyboard prompt generation."""
    clean_text = _compact(_strip_file_like_tokens(_strip_quoted_text(text or "")))

    if beat_type == "pause":
        rendered = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_AUDIO_VISUAL_PAUSE.value, {}
        )
        return _compact(rendered)

    if beat_type == "action":
        base = clean_text or "动作镜头"
        rendered = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_AUDIO_VISUAL_ACTION.value, {"action": base}
        )
        return _compact(rendered)

    # dialogue beat
    speaker = (speaker_name or "").strip() or "人物"
    action_str = str(dialogue_action or "").strip()
    is_voiceover = any(k in action_str for k in ("内心独白", "心声", "OS", "旁白"))

    if _looks_like_document_read(clean_text):
        rendered = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_AUDIO_VISUAL_DIALOGUE_READ_TEXT.value,
            {"speaker": speaker},
        )
        return _compact(rendered)

    intent = _infer_dialogue_intent(clean_text)
    template_name = (
        PromptTemplate.STORYBOARD_AUDIO_VISUAL_DIALOGUE_VOICEOVER.value
        if is_voiceover
        else PromptTemplate.STORYBOARD_AUDIO_VISUAL_DIALOGUE_SPOKEN.value
    )
    rendered = prompt_manager.render_prompt(
        template_name,
        {"speaker": speaker, "intent": intent},
    )
    return _compact(rendered)
