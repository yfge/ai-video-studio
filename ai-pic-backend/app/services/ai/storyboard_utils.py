from __future__ import annotations

from typing import Any, Dict, List, Optional


def _trim_text(value: str | None, limit: int = 160) -> str:
    if not value:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _to_int_safe(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_hook_plan(plan: Any) -> str:
    if not plan:
        return ""
    if isinstance(plan, dict):
        parts: List[str] = []
        opening = plan.get("opening_hook")
        escalation = plan.get("escalation_plan")
        payoff = plan.get("payoff_plan")
        if opening:
            parts.append(f"开场:{opening}")
        if escalation:
            parts.append(f"升级:{escalation}")
        if payoff:
            parts.append(f"回收:{payoff}")
        reversals = plan.get("key_reversals")
        if isinstance(reversals, list) and reversals:
            reversal_desc = []
            for item in reversals[:3]:
                if isinstance(item, dict):
                    desc = item.get("description") or item.get("beat")
                else:
                    desc = str(item)
                if desc:
                    reversal_desc.append(desc)
            if reversal_desc:
                parts.append("反转:" + "；".join(reversal_desc))
        return "；".join(parts) if parts else str(plan)
    return str(plan)


def _format_ad_snippets(snippets: Any) -> str:
    if not isinstance(snippets, list):
        return ""
    hooks: List[str] = []
    for item in snippets[:3]:
        if isinstance(item, dict):
            hook = item.get("hook") or item.get("visual_summary")
        else:
            hook = str(item)
        if hook:
            hooks.append(str(hook))
    return "；".join(hooks)


def _collect_scene_dialogues(
    script: Dict[str, Any], scene_number: Optional[int], limit: int = 2
) -> List[str]:
    dialogues = []
    for item in script.get("dialogues") or []:
        if isinstance(item, dict):
            sn = _to_int_safe(item.get("scene_number"))
            content = item.get("content") or item.get("text") or item.get("line")
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        dialogues.append(_trim_text(content, 80))
        if len(dialogues) >= limit:
            break
    return dialogues


def _collect_stage_notes(
    script: Dict[str, Any], scene_number: Optional[int], limit: int = 2
) -> List[str]:
    notes = []
    for item in script.get("stage_directions") or []:
        if isinstance(item, dict):
            sn = _to_int_safe(item.get("scene_number"))
            content = (
                item.get("content") or item.get("direction") or item.get("description")
            )
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        notes.append(_trim_text(content, 80))
        if len(notes) >= limit:
            break
    return notes


def build_storyboard_context(script: Dict[str, Any]) -> str:
    story = script.get("story") or {}
    episode = script.get("episode") or {}
    scenes = script.get("scenes") or []
    scene_indices = script.get("scene_indices") or []

    sections: List[str] = []
    if story:
        story_bits = []
        if story.get("title"):
            story_bits.append(str(story["title"]))
        if story.get("genre"):
            story_bits.append(f"类型:{story['genre']}")
        if story.get("market_region"):
            story_bits.append(f"市场:{story['market_region']}")
        if story.get("micro_genre"):
            story_bits.append(f"微类型:{story['micro_genre']}")
        if story.get("theme"):
            story_bits.append(f"主题:{_trim_text(story['theme'], 80)}")
        if story.get("world_building"):
            story_bits.append(f"设定:{_trim_text(story['world_building'], 100)}")
        hook_plan = _format_hook_plan(story.get("hook_plan"))
        if hook_plan:
            story_bits.append(f"钩子:{_trim_text(hook_plan, 120)}")
        if story.get("twist_density"):
            story_bits.append(f"反转密度:{story['twist_density']}")
        cliffhangers = story.get("cliffhanger_plan")
        if isinstance(cliffhangers, list) and cliffhangers:
            story_bits.append(
                "卡点:" + _trim_text("；".join(map(str, cliffhangers[:3])), 80)
            )
        ad_snippets = _format_ad_snippets(story.get("ad_snippets"))
        if ad_snippets:
            story_bits.append(f"投流:{_trim_text(ad_snippets, 100)}")
        if story_bits:
            sections.append("故事背景：" + "，".join(story_bits))

    if episode:
        epi_bits = []
        if episode.get("episode_number"):
            epi_bits.append(f"第{episode['episode_number']}集")
        if episode.get("title"):
            epi_bits.append(str(episode["title"]))
        if episode.get("micro_genre"):
            epi_bits.append(f"微类型:{episode['micro_genre']}")
        if episode.get("hook_plan"):
            epi_bits.append(
                f"钩子:{_trim_text(_format_hook_plan(episode.get('hook_plan')), 100)}"
            )
        epi_cliffs = episode.get("cliffhanger_plan")
        if isinstance(epi_cliffs, list) and epi_cliffs:
            epi_bits.append(
                "卡点:" + _trim_text("；".join(map(str, epi_cliffs[:3])), 60)
            )
        elif isinstance(epi_cliffs, str) and epi_cliffs:
            epi_bits.append("卡点:" + _trim_text(epi_cliffs, 60))
        if episode.get("summary"):
            epi_bits.append(f"概要:{_trim_text(episode['summary'], 120)}")
        if episode.get("duration_minutes"):
            epi_bits.append(f"时长:{episode['duration_minutes']}分钟")
        if episode.get("scene_count"):
            epi_bits.append(f"场景数:{episode['scene_count']}")
        if epi_bits:
            sections.append("剧集信息：" + "，".join(epi_bits))

    for idx, raw_scene in enumerate(scenes):
        if isinstance(raw_scene, dict):
            scene_dict = raw_scene
            description = scene_dict.get("description")
            location = scene_dict.get("location") or scene_dict.get("place")
            time = scene_dict.get("time") or scene_dict.get("period")
            characters = scene_dict.get("characters") or scene_dict.get("cast")
            notes = scene_dict.get("notes")
        else:
            scene_dict = {}
            description = str(raw_scene)
            location = time = characters = notes = None

        scene_no = scene_indices[idx] if idx < len(scene_indices) else idx + 1
        heading = f"场景 {scene_no}"
        details: List[str] = []
        if location:
            details.append(f"地点:{_trim_text(location, 50)}")
        if time:
            details.append(f"时间:{_trim_text(time, 40)}")
        if characters:
            if isinstance(characters, list):
                details.append(
                    f"角色:{_trim_text(', '.join(map(str, characters)), 80)}"
                )
            else:
                details.append(f"角色:{_trim_text(str(characters), 80)}")
        if notes:
            details.append(f"备注:{_trim_text(notes, 80)}")
        details.append(f"描述:{_trim_text(description, 120)}")

        dialogues = _collect_scene_dialogues(script, scene_no)
        if dialogues:
            details.append("对白:" + " / ".join(dialogues))
        stage_notes = _collect_stage_notes(script, scene_no)
        if stage_notes:
            details.append("舞台:" + " / ".join(stage_notes))

        sections.append(f"{heading} -> " + "；".join(details))

    content_excerpt = _trim_text(script.get("content"), 400)
    if content_excerpt:
        sections.append(f"剧本文本片段：{content_excerpt}")

    context = "\n".join(sections)
    return context[:4000]
