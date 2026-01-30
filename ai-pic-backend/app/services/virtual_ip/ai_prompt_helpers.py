"""
Helper utilities for Virtual IP AI generation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def generate_template_content(name: str, basic_info: Optional[str]) -> Dict[str, Any]:
    """生成模板内容（当AI不可用时使用）"""
    return {
        "description": (
            f"{name}拥有鲜明的个性与清晰的形象定位。"
            f"{basic_info or '外表与气质自洽，言行有迹可循，适合发展为长期叙事角色。'}"
        ),
        "background_story": (
            f"在一个充满无限可能的世界里，{name}的故事开始了。\n\n"
            f"{basic_info or 'Ta的成长经历与关键选择，塑造了当下的性格与处事方式。'}\n\n"
            f"每一次出现，{name}都会为观众带来新的惊喜和感动。"
            "这不仅仅是一个角色，更是一个充满生命力的叙事核心。"
        ),
        "biography": (
            f"**角色档案：{name}**\n\n"
            f"**外貌特征**：{name}拥有令人印象深刻的外貌，每一个细节都经过精心设计。\n\n"
            "**性格特点**：性格鲜明，既有亲和力又有独特的个人魅力。\n\n"
            "**兴趣爱好**：热爱生活，对世界充满好奇心。\n\n"
            "**特长技能**：在自己的领域有着出色的表现。\n\n"
            f"**背景经历**：{basic_info or '拥有丰富的人生经历，塑造了现在的个性。'}\n\n"
            "这是一个值得深入了解和喜爱的角色。"
        ),
        "tags": [],
    }


def sanitize_character_text(text: str, *, name: str) -> str:
    """尽量移除模型输出中不符合约束的元叙述词（例如“虚拟IP/虚拟角色”）。"""
    if not text:
        return ""
    cleaned = str(text)
    for token in [
        "虚拟IP",
        "虚拟角色",
        "虚拟人物",
        "虚拟人",
        "IP角色",
        "虚拟 ip",
        "virtual ip",
        "virtual character",
    ]:
        cleaned = cleaned.replace(token, "")
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = cleaned.replace(" ，", "，").replace(" 。", "。").replace(" ；", "；")
    return cleaned.strip()


def generate_template_style_prompt(
    name: str, description: str, image_category: str
) -> str:
    """生成模板风格提示词（中文）"""
    base_prompt = "高质量的二次元角色"

    if "girl" in description.lower() or "女" in description:
        base_prompt = "高质量的二次元女孩"
    elif "boy" in description.lower() or "男" in description:
        base_prompt = "高质量的二次元男孩"

    category_modifiers = {
        "portrait": "半身肖像，面部细节清晰",
        "full_body": "全身像，站姿完整",
        "scene": "人物与场景融合，环境背景",
        "action": "动态姿势，动作场景",
        "emotion": "表情丰富，情绪表达",
    }

    modifier = category_modifiers.get(image_category, "半身肖像，细节清晰")

    return f"{base_prompt}，{modifier}，细节丰富，清晰聚焦"


def build_biography_from_profile(profile: Dict[str, Any]) -> str:
    """根据 virtual_ip_creation 的各字段拼接成一段人物小传。"""
    sections: List[str] = []
    mapping = [
        ("性格特征", "personality"),
        ("技能特长", "skills"),
        ("人际关系", "relationships"),
        ("生活方式", "lifestyle"),
        ("标志性特征", "signature_traits"),
        ("发展潜力", "development_potential"),
    ]
    for title, key in mapping:
        value = profile.get(key)
        if not value:
            continue
        sections.append(f"**{title}**：{value}")
    text = "\n\n".join(sections).strip()
    if not text:
        return ""
    return text


def normalize_suggested_tags(raw: Any) -> List[str]:
    """Normalize suggested tags from AI profile output."""
    if not raw:
        return []
    if isinstance(raw, str):
        items = re.split(r"[,，、;/\n]+", raw)
    elif isinstance(raw, (list, tuple)):
        items = []
        for item in raw:
            if isinstance(item, str):
                items.append(item)
    else:
        return []

    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        tag = item.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
        if len(result) >= 10:
            break
    return result
