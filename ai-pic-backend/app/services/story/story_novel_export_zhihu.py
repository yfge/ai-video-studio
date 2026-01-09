from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.core.config import settings
from app.prompts.manager import prompt_manager
from app.utils.json_utils import extract_json_block

from .story_novel_export_ai import generate_story_novel_text
from .story_novel_export_continuity import (
    build_plan_context,
    compact_ledger_for_prompt,
    ensure_markers,
    extract_chapter_markers,
    init_continuity_ledger,
    normalize_ledger_update_payload,
    tail_text,
)
from .story_novel_export_payload import shrink_story_novel_payload_for_plan
from .story_novel_export_planner import (
    generate_zhihu_plan_compact,
    plan_intro_from_plan,
)
from .story_novel_export_utils import (
    StoryNovelExportResult,
    count_words,
    safe_join_under,
)
from .story_novel_export_zhihu_chapter import generate_zhihu_chapter_text

ProgressCallback = Callable[[str], Any]


async def export_zhihu_novel_to_file(
    *,
    story_title: str,
    story_payload: Dict[str, Any],
    target_words: int,
    chapter_total: int,
    model_id: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    progress: ProgressCallback | None = None,
) -> StoryNovelExportResult:
    ledger = init_continuity_ledger(story_payload=story_payload)
    previous_tail = ""
    previous_cliffhanger = ""
    if progress:
        progress("生成小说大纲（知乎体）…")
    json_system_prompt = prompt_manager.render_prompt("system_prompt_json_strict", {})
    novel_system_prompt = prompt_manager.render_prompt("system_prompt_novel_zhihu", {})
    plan_story_payload = shrink_story_novel_payload_for_plan(story_payload)
    plan, chapters = await generate_zhihu_plan_compact(
        story_payload=plan_story_payload,
        target_words=target_words,
        chapter_total=chapter_total,
        model_id=model_id,
        prefer_provider=prefer_provider,
        system_prompt=json_system_prompt,
    )

    question_title, question_detail, narrator_profile, running_summary = (
        plan_intro_from_plan(
            plan,
            story_title=story_title,
        )
    )
    full_text_parts: list[str] = [
        f"【问题】\n{question_title}\n\n{question_detail}\n",
        f"【回答】\n{narrator_profile}\n\n",
    ]
    total_words = 0
    produced_chapters = 0
    for idx, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            continue
        chapter_number = int(chapter.get("chapter_number") or idx)
        chapter_title = str(chapter.get("title") or f"更新 {chapter_number}")
        chapter_target = int(chapter.get("target_words") or 0) or max(
            1200, int(round(target_words / max(1, chapter_total)))
        )
        remaining_target = max(0, target_words - total_words)

        plan_context = build_plan_context(plan, chapters=chapters, index=idx - 1)
        ledger_context = compact_ledger_for_prompt(ledger)
        chapter_seed = {
            "chapter_number": chapter_number,
            "title": chapter_title,
            "target_words": chapter_target,
            "chapter_goal": str(chapter.get("chapter_goal") or "").strip(),
            "cliffhanger_hint": str(
                chapter.get("cliffhanger_hint") or chapter.get("cliffhanger") or ""
            ).strip(),
        }
        final_text = await generate_zhihu_chapter_text(
            story_payload=story_payload,
            plan_context=plan_context,
            ledger_context=ledger_context,
            previous_tail=previous_tail,
            previous_cliffhanger=previous_cliffhanger,
            chapter_seed=chapter_seed,
            running_summary=running_summary,
            remaining_target_words=remaining_target,
            total_target_words=target_words,
            model_id=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
            json_system_prompt=json_system_prompt,
            novel_system_prompt=novel_system_prompt,
            progress=progress,
            chapter_total=len(chapters),
        )
        chapter_body, extracted_summary, extracted_cliffhanger = (
            extract_chapter_markers(final_text)
        )
        if progress:
            progress(f"更新连贯性账本：更新 {chapter_number}/{len(chapters)}…")
        ledger_prompt = prompt_manager.render_prompt(
            "story_novel_zhihu_ledger_update",
            {
                "previous_ledger": ledger_context,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "chapter_text": final_text,
                "extracted_summary": extracted_summary,
                "extracted_cliffhanger": extracted_cliffhanger,
            },
        )
        ledger_payload = (
            extract_json_block(
                await generate_story_novel_text(
                    prompt=ledger_prompt,
                    system_prompt=json_system_prompt,
                    model=model_id,
                    prefer_provider=prefer_provider,
                    temperature=0.2,
                    max_tokens=1800,
                )
            )
            or {}
        )
        updated_ledger, summary_text, cliffhanger_text = (
            normalize_ledger_update_payload(ledger_payload)
        )
        if updated_ledger:
            ledger = updated_ledger
        final_summary = summary_text or extracted_summary
        final_cliffhanger = cliffhanger_text or extracted_cliffhanger

        chapter_text = ensure_markers(
            chapter_body or final_text,
            summary_text=final_summary,
            cliffhanger_text=final_cliffhanger,
        )
        words = count_words(chapter_body or chapter_text)
        total_words += words
        if final_summary:
            running_summary = (running_summary + "\n" + final_summary).strip()
        if final_cliffhanger:
            running_summary = (running_summary + "\n卡点：" + final_cliffhanger).strip()
            previous_cliffhanger = final_cliffhanger.strip()
            if len(previous_cliffhanger) > 300:
                previous_cliffhanger = previous_cliffhanger[:300].rstrip() + "…"
        previous_tail = tail_text(chapter_body or chapter_text, 900)
        full_text_parts.append(f"—— 更新 {chapter_number}：{chapter_title} ——\n")
        full_text_parts.append(chapter_text.strip() + "\n\n")
        produced_chapters += 1
    full_text = "".join(full_text_parts).strip() + "\n"
    if progress:
        progress("写入导出文件…")
    exports_dir = Path(settings.UPLOAD_DIR) / "exports" / "novels"
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_title = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", story_title).strip("_")
    filename = f"zhihu_novel_{safe_title}_{timestamp}.txt"
    relative_path = str(Path("exports") / "novels" / filename)
    file_path = safe_join_under(Path(settings.UPLOAD_DIR), relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(full_text, encoding="utf-8")
    if progress:
        progress(f"完成：约 {total_words} 字，可下载。")
    return StoryNovelExportResult(
        relative_path=relative_path,
        filename=filename,
        total_words=total_words,
        chapter_count=produced_chapters,
        content_text=full_text,
    )
