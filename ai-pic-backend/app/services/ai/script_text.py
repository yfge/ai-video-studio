from __future__ import annotations

from typing import Any, Dict, List


def build_script_text(
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    format_type: str,
    language: str,
) -> str:
    lines: List[str] = [
        f"# {format_type} ({language})",
        "【音效】砰！画面直接切入冲突现场。",
    ]
    if scenes:
        lines.append("## 场景")
        for scene in scenes:
            scene_no = scene.get("scene_number") or "-"
            slug = scene.get("slug_line") or f"Scene {scene.get('scene_number')}"
            summary = scene.get("summary") or scene.get("description") or ""
            lines.append(f"- [场景 {scene_no}] {slug}: {summary}")
            if summary:
                lines.append(f"【快】【情绪目的：推进冲突】{summary}")
    if dialogues:
        lines.append("\n## 对白")
        for dialogue in dialogues[:200]:
            scene_no = dialogue.get("scene_number") or "-"
            character = dialogue.get("character") or "旁白"
            content = (
                dialogue.get("content")
                or dialogue.get("line")
                or dialogue.get("text")
                or ""
            )
            lines.append(f"[场景 {scene_no}] {character}: {content}")
    if stage_directions:
        lines.append("\n## 舞台指示")
        for direction in stage_directions[:200]:
            scene_no = direction.get("scene_number") or "-"
            content = (
                direction.get("content")
                or direction.get("direction")
                or direction.get("description")
                or ""
            )
            timing = direction.get("timing") or ""
            lines.append(f"[场景 {scene_no}][{timing}] {content}")
    if not _ends_with_question(lines):
        lines.append(
            "【慢】【情绪目的：留下悬念】镜头停在关键线索上：接下来会发生什么？"
        )
    return "\n".join(lines)


def _ends_with_question(lines: List[str]) -> bool:
    for line in reversed(lines):
        text = line.strip()
        if text:
            return "?" in text or "？" in text
    return False
