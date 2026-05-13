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


def _performance_for_intent(intent: str | None, *, voiceover: bool) -> dict[str, str]:
    if voiceover:
        return {
            "expression": "压抑的眼神和细微呼吸变化",
            "gesture": "身体停在原位，手指轻微收紧或停顿",
            "shot_goal": "用沉默反应承接旁白情绪，不表现开口说话",
        }
    if intent == "疑问/追问":
        return {
            "expression": "眉头微皱，眼神追问对方",
            "gesture": "上身轻微前倾，手部有克制的追问动作",
            "shot_goal": "突出人物试探和信息压力",
        }
    if intent == "情绪激烈":
        return {
            "expression": "眼眶紧绷，嘴角用力，情绪外露",
            "gesture": "肩颈绷紧，手部动作更明显但不过度夸张",
            "shot_goal": "放大冲突爆点和短剧节奏",
        }
    if intent == "解释/辩解":
        return {
            "expression": "神情急切又克制，目光闪避后重新看向对方",
            "gesture": "手掌轻抬做解释动作，身体保持防御姿态",
            "shot_goal": "表现人物被误解后的辩解压力",
        }
    if intent == "质问/指控":
        return {
            "expression": "目光锐利，表情冷硬，压迫感增强",
            "gesture": "身体定住，手部指向或压低动作形成对峙",
            "shot_goal": "形成对峙关系和悬念压迫",
        }
    return {
        "expression": "自然口型和微表情变化",
        "gesture": "头部和手部有细小反应，动作贴合说话节奏",
        "shot_goal": "交代人物情绪和关系推进",
    }


def build_visual_prompt_description(
    *,
    beat_type: str,
    speaker_name: str | None,
    text: str | None,
    dialogue_action: Any = None,
) -> str:
    """Build a visual-only description for storyboard prompt generation."""
    raw_text = text or ""
    clean_text = _compact(_strip_file_like_tokens(_strip_quoted_text(raw_text)))

    if beat_type == "pause":
        rendered = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_AUDIO_VISUAL_PAUSE.value, {}
        )
        return _compact(rendered)

    if beat_type == "action":
        base = clean_text or "动作镜头"
        rendered = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_AUDIO_VISUAL_ACTION.value,
            {
                "action": base,
                "performance": "动作有明确目的和反应节奏，人物情绪通过姿态体现",
            },
        )
        return _compact(rendered)

    # dialogue beat
    speaker = (speaker_name or "").strip() or "人物"
    action_str = str(dialogue_action or "").strip()
    is_voiceover = any(k in action_str for k in ("内心独白", "心声", "OS", "旁白"))

    if _looks_like_document_read(raw_text) or _looks_like_document_read(clean_text):
        rendered = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_AUDIO_VISUAL_DIALOGUE_READ_TEXT.value,
            {
                "speaker": speaker,
                "reaction": "读到关键信息后的眼神骤变和手部停顿",
            },
        )
        return _compact(rendered)

    intent = _infer_dialogue_intent(clean_text)
    performance = _performance_for_intent(intent, voiceover=is_voiceover)
    template_name = (
        PromptTemplate.STORYBOARD_AUDIO_VISUAL_DIALOGUE_VOICEOVER.value
        if is_voiceover
        else PromptTemplate.STORYBOARD_AUDIO_VISUAL_DIALOGUE_SPOKEN.value
    )
    rendered = prompt_manager.render_prompt(
        template_name,
        {
            "speaker": speaker,
            "intent": intent,
            "expression": performance["expression"],
            "gesture": performance["gesture"],
            "shot_goal": performance["shot_goal"],
        },
    )
    return _compact(rendered)
