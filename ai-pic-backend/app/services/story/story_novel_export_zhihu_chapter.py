from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.prompts.manager import prompt_manager

from .story_novel_export_ai import generate_story_novel_text
from .story_novel_export_planner import generate_zhihu_chapter_beats
from .story_novel_export_utils import ZH_CLIFFHANGER_MARKER, ZH_SUMMARY_MARKER, clip_text

ProgressCallback = Callable[[str], Any]


def chapter_max_tokens(target_words: int) -> int:
    """Per-chapter token budget with headroom for正文+小结+卡点."""
    if target_words <= 0:
        return 1800
    budget = int(target_words * 1.3) + 900
    return max(1600, min(5200, budget))


async def generate_zhihu_chapter_text(
    *,
    story_payload: Dict[str, Any],
    plan_context: Dict[str, Any],
    ledger_context: Dict[str, Any],
    previous_tail: str,
    previous_cliffhanger: str,
    chapter_seed: Dict[str, Any],
    running_summary: str,
    remaining_target_words: int,
    total_target_words: int,
    model_id: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    json_system_prompt: str,
    novel_system_prompt: str,
    progress: ProgressCallback | None = None,
    chapter_total: int = 0,
) -> str:
    chapter_number = int(chapter_seed.get("chapter_number") or 0) or 1
    chapter_target = int(chapter_seed.get("target_words") or 0) or 0
    chapter_title = str(chapter_seed.get("title") or f"更新 {chapter_number}")

    beats = await generate_zhihu_chapter_beats(
        story_payload=story_payload,
        plan_context=plan_context,
        ledger=ledger_context,
        previous_tail=previous_tail,
        previous_cliffhanger=previous_cliffhanger,
        chapter=chapter_seed,
        running_summary=clip_text(running_summary, 1200) or "",
        model_id=model_id,
        prefer_provider=prefer_provider,
        system_prompt=json_system_prompt,
    )
    chapter_payload = {
        "chapter_number": chapter_number,
        "title": chapter_title,
        "target_words": chapter_target,
        "key_beats": beats,
        "cliffhanger_hint": str(chapter_seed.get("cliffhanger_hint") or "").strip(),
    }

    if progress:
        suffix = f"/{chapter_total}" if chapter_total else ""
        progress(f"生成正文草稿：更新 {chapter_number}{suffix}（目标≈{chapter_target}字）…")
    chapter_prompt = prompt_manager.render_prompt(
        "story_novel_zhihu_chapter",
        {
            "story": story_payload,
            "plan": plan_context,
            "ledger": ledger_context,
            "previous_tail": previous_tail,
            "previous_cliffhanger": previous_cliffhanger,
            "chapter": chapter_payload,
            "running_summary": clip_text(running_summary, 1200) or "",
            "remaining_target_words": remaining_target_words,
            "total_target_words": total_target_words,
        },
    )
    draft_text = await generate_story_novel_text(
        prompt=chapter_prompt,
        system_prompt=novel_system_prompt,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=temperature,
        max_tokens=chapter_max_tokens(chapter_target),
    )

    if progress:
        suffix = f"/{chapter_total}" if chapter_total else ""
        progress(f"润色与一致性检查：更新 {chapter_number}{suffix}…")
    rewrite_prompt = prompt_manager.render_prompt(
        "story_novel_zhihu_chapter_rewrite",
        {
            "story": story_payload,
            "plan": plan_context,
            "ledger": ledger_context,
            "previous_tail": previous_tail,
            "previous_cliffhanger": previous_cliffhanger,
            "running_summary": clip_text(running_summary, 1200) or "",
            "chapter": chapter_payload,
            "draft": draft_text,
            "remaining_target_words": remaining_target_words,
            "total_target_words": total_target_words,
        },
    )
    final_text = await generate_story_novel_text(
        prompt=rewrite_prompt,
        system_prompt=novel_system_prompt,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=min(temperature, 0.5),
        max_tokens=chapter_max_tokens(chapter_target),
    )

    if (ZH_SUMMARY_MARKER not in final_text) or (ZH_CLIFFHANGER_MARKER not in final_text):
        if progress:
            suffix = f"/{chapter_total}" if chapter_total else ""
            progress(f"补全章节收尾：更新 {chapter_number}{suffix}…")
        finalize_prompt = prompt_manager.render_prompt(
            "story_novel_zhihu_chapter_finalize",
            {
                "story": story_payload,
                "plan": plan_context,
                "ledger": ledger_context,
                "previous_tail": previous_tail,
                "previous_cliffhanger": previous_cliffhanger,
                "chapter": chapter_payload,
                "running_summary": clip_text(running_summary, 1200) or "",
                "draft": final_text,
                "remaining_target_words": remaining_target_words,
                "total_target_words": total_target_words,
            },
        )
        final_text = await generate_story_novel_text(
            prompt=finalize_prompt,
            system_prompt=novel_system_prompt,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=min(temperature, 0.5),
            max_tokens=min(6000, chapter_max_tokens(chapter_target) + 900),
        )

    return final_text

