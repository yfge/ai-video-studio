"""Character Background Generator.

Uses AI to generate personality, background, and appearance descriptions
for temporary characters based on their dialogues and script context.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.script.temporary_character_extractor import TemporaryCharacterInfo


async def generate_character_background(
    *,
    character_info: TemporaryCharacterInfo,
    scene_context: Dict[str, Any],
    ai_service: Optional[Any] = None,
) -> Dict[str, str]:
    """Generate character background using AI analysis of dialogues and context.

    Args:
        character_info: Extracted character information from script
        scene_context: Scene context (e.g., setting, time, location)
        ai_service: Optional AI service instance for generation (if None, uses heuristics)

    Returns:
        Dictionary with:
        - personality: Character personality traits
        - background: Character background story
        - appearance_override: Physical appearance description
    """
    # Build AI prompt from character info
    prompt = _build_generation_prompt(character_info, scene_context)

    # Use AI service if available, otherwise fall back to heuristics
    if ai_service:
        result = await _generate_with_ai(prompt, ai_service)
    else:
        result = _generate_with_heuristics(character_info)

    return result


def _build_generation_prompt(
    character_info: TemporaryCharacterInfo,
    scene_context: Dict[str, Any],
) -> str:
    """Build AI prompt for character background generation.

    Args:
        character_info: Character information
        scene_context: Scene context

    Returns:
        Prompt string for AI generation
    """
    # Format dialogues
    dialogues_text = "\n".join(
        [f'"{dlg}"' for dlg in character_info.dialogues[:5]]  # Limit to first 5
    )

    # Format appearance hints
    appearance_hints_text = ", ".join(character_info.appearance_hints)

    # Format scene context
    setting = scene_context.get("setting_location", "")
    time_period = scene_context.get("setting_time", "")

    prompt = f"""请根据以下信息生成临时角色的详细背景资料：

角色名称：{character_info.character_name}

出场场景：第{character_info.first_appearance_scene}场景到第{character_info.last_appearance_scene}场景
对白总数：{character_info.dialogue_count}句

角色对白示例：
{dialogues_text}

外观线索：{appearance_hints_text or "无"}

场景设定：
- 地点：{setting}
- 时代：{time_period}

请生成以下三个方面的描述：

1. 性格特点（personality）：
   - 基于对白分析角色的性格特征
   - 2-3个关键词，用逗号分隔
   - 示例："热情、专业、认真负责"

2. 角色背景（background）：
   - 1-2句话描述角色的身份和背景
   - 结合场景设定和角色名称
   - 示例："快递公司员工，负责本小区的配送工作，对社区环境很熟悉"

3. 外观描述（appearance_override）：
   - 1-2句话描述角色的外观特征
   - 结合外观线索和职业特点
   - 示例："穿着快递制服，背着快递包，看起来年轻有活力"

请以JSON格式返回：
{{
  "personality": "...",
  "background": "...",
  "appearance_override": "..."
}}
"""
    return prompt


async def _generate_with_ai(
    prompt: str,
    ai_service: Any,
) -> Dict[str, str]:
    """Generate character background using AI service.

    Args:
        prompt: Generation prompt
        ai_service: AI service instance

    Returns:
        Dictionary with personality, background, appearance_override
    """
    try:
        # Call AI service
        response = await ai_service.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=500,
        )

        # Parse JSON response
        import json

        if hasattr(response, "content"):
            result = json.loads(response.content)
        elif isinstance(response, dict):
            result = response
        else:
            result = json.loads(str(response))

        # Validate required fields
        return {
            "personality": result.get("personality", ""),
            "background": result.get("background", ""),
            "appearance_override": result.get("appearance_override", ""),
        }

    except Exception as e:
        # Log error and fall back to heuristics
        import logging

        logging.warning(f"AI generation failed: {e}, falling back to heuristics")
        return _generate_with_heuristics_from_prompt(prompt)


def _generate_with_heuristics(
    character_info: TemporaryCharacterInfo,
) -> Dict[str, str]:
    """Generate character background using heuristic rules.

    Args:
        character_info: Character information

    Returns:
        Dictionary with personality, background, appearance_override
    """
    char_name = character_info.character_name

    # Infer role type from name
    role_hints = {
        "快递员": {
            "personality": "热情、负责、有耐心",
            "background": "快递公司员工，负责配送工作",
            "appearance": "穿着快递制服，背着快递包",
        },
        "医生": {
            "personality": "专业、冷静、细心",
            "background": "医疗工作者，负责诊疗工作",
            "appearance": "穿着白大褂，戴着听诊器",
        },
        "护士": {
            "personality": "温柔、体贴、认真",
            "background": "医疗护理工作者，协助医生工作",
            "appearance": "穿着护士制服，戴着护士帽",
        },
        "警察": {
            "personality": "严肃、正义、果断",
            "background": "执法人员，维护治安工作",
            "appearance": "穿着警服，佩戴警徽",
        },
        "服务员": {
            "personality": "热情、礼貌、周到",
            "background": "服务行业从业者，负责接待工作",
            "appearance": "穿着工作服，面带微笑",
        },
        "司机": {
            "personality": "稳重、熟练、负责",
            "background": "驾驶工作者，负责运输工作",
            "appearance": "穿着工作服或便装",
        },
    }

    # Try exact match
    if char_name in role_hints:
        hints = role_hints[char_name]
        return {
            "personality": hints["personality"],
            "background": hints["background"],
            "appearance_override": hints["appearance"],
        }

    # Try partial match
    for key, hints in role_hints.items():
        if key in char_name or char_name in key:
            return {
                "personality": hints["personality"],
                "background": hints["background"],
                "appearance_override": hints["appearance"],
            }

    # Use appearance hints if available
    appearance = ", ".join(character_info.appearance_hints)
    if not appearance:
        appearance = f"{char_name}的外观特征"

    # Generic fallback
    return {
        "personality": "普通、友好、礼貌",
        "background": f"{char_name}，在剧情中扮演临时角色",
        "appearance_override": appearance,
    }


def _generate_with_heuristics_from_prompt(prompt: str) -> Dict[str, str]:
    """Generate character background from prompt when AI fails.

    Args:
        prompt: Original generation prompt

    Returns:
        Dictionary with personality, background, appearance_override
    """
    # Extract character name from prompt
    import re

    name_match = re.search(r"角色名称：(.+)", prompt)
    char_name = name_match.group(1).strip() if name_match else "临时角色"

    # Extract appearance hints
    appearance_match = re.search(r"外观线索：(.+)", prompt)
    appearance = (
        appearance_match.group(1).strip()
        if appearance_match
        else f"{char_name}的外观特征"
    )

    # Generic fallback
    return {
        "personality": "友好、专业、认真",
        "background": f"{char_name}，在剧情中扮演临时角色",
        "appearance_override": appearance,
    }
