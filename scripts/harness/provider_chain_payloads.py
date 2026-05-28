"""Payload helpers for provider chain regression."""

from __future__ import annotations

import json
import re
from typing import Any

TEXT_MODEL = "deepseek-v4-flash"
IMAGE_MODEL = "openai:chatgpt-img-2"
VIDEO_MODEL = "seedance-2.0-i2v"
SEEDANCE_CANONICAL = "doubao-seedance-2-0-260128"


def scene_durations(mode: str) -> list[int]:
    return [4] if mode == "smoke" else [15, 15]


def build_script_prompt(
    mode: str, premise: str | None = None, repair_notes: list[str] | None = None
) -> str:
    durations = scene_durations(mode)
    premise_text = (
        f" Story premise to follow: {premise.strip()}. "
        if isinstance(premise, str) and premise.strip()
        else " "
    )
    repair_text = _repair_text(repair_notes)
    return (
        "Return only valid JSON. Write a compact Chinese short-drama script for a "
        "non-real 3D cartoon robot character. No live-action human, no celebrity, "
        "no photorealistic face."
        f"{premise_text}"
        "The JSON schema is: "
        '{"title":str,"logline":str,"characters":[{"name":str,"role":str,'
        '"appearance_prompt":str,"consistency_anchor":str}],'
        '"scenes":[{"scene_id":str,"duration_seconds":int,"question":str,'
        '"stakes":str,"opposition":str,"turn":str,"plot":str,'
        '"dialogue":[{"speaker":str,"line":str}],'
        '"beats":[{"order_index":int,"beat_type":str,"dramatic_purpose":str,'
        '"visible_event":str,"action":[str],"dialogue":[{"speaker":str,"line":str}],'
        '"duration_seconds":number,"hook_tag":str,"payoff_tag":str,'
        '"cliffhanger_tag":str}],"image_prompt":str,'
        '"video_prompt":str}]}. '
        f"Create exactly {len(durations)} scene(s) with durations {durations}. "
        "Before writing, satisfy the ScriptScore pass rubric: "
        "conflict_intensity >= 4, character_recognizability >= 4, "
        "clip_ability >= 4, and logic_coherence >= 4. "
        "角色标签 must be concrete: characters[0].role must combine a personality, "
        "job, and motivation such as 急脾气剪辑师要保住客户验收证据; do not write only 主角. "
        "For character_recognizability, give the protagonist one repeated signature "
        "behavior or catchphrase and make supporting characters visually and verbally "
        "different. Supporting characters must use a different color/material/silhouette "
        "from the protagonist, and their motive must be visible in dialogue or plot. "
        "For logic_coherence, write a because/therefore chain: every reveal "
        "must be seeded by an earlier visible clue, and you must seed every hidden "
        "code, password, account, or backdoor before it is used as a solution. "
        "Do not use hidden code, password, account, or backdoor as the solution "
        "unless a previous beat shows who created it, why it exists, and what limitation it has. "
        "The protagonist must solve each scene through a visible choice or action; "
        "the secondary character cannot simply reveal the answer. "
        "The opposition motive must be planted before confrontation; do not make an antagonist confess "
        "or appear without prior visible proof, benefit, or pressure. "
        "Any unknown operator must be seeded in scene 1 as a partial ID, shadow trace, "
        "voice print, log mismatch, or unexplained remote cursor before it becomes the final threat. "
        "Every permission or account action must name the access rule: read-only access, "
        "write lock, audit token, expired key, remote control, or approval queue. "
        "For the final beat, do not put 删除完成, 已上传, 已修复, or 任务完成 as the final state; "
        "use 正在删除, 第二倒计时, 未知操作者, or a new active threat instead. "
        "Each scene must contain at least one non-screen physical action or high-impact "
        "visual state change beyond typing, reading, or pointing at a panel. "
        "For clip_ability, every scene needs at least two ad-hook moments, each with "
        "visual shock + subtitle-friendly dialogue. opposition must literally include "
        "one marker from 系统, 权限, 客户, 内鬼, 审核, 锁定, 删除, 篡改, 修改者, 操作者. "
        "The opening hook visible_event, action, or dialogue must literally include "
        "one marker from 警报, 警告, 倒计时, 清零, 删除, 丢失, 锁定, 错误, 失败, 危机, "
        "威胁, 证据, 真相, 反转, or 必须. "
        f"{repair_text}"
        "Every scene must include a concrete question, stakes, opposition, and turn: "
        "question names the scene's story problem; stakes names a concrete loss, "
        "deadline, object, customer, money, asset, file, or proof; opposition names "
        "the blocking source such as a system, permission, customer, supplier, black "
        "shadow, log, file, interface, or deletion; turn names the changed clue, "
        "threat, choice, or result. Do not use generic wording like 推进剧情, "
        "压力变大, 混乱局面, or 出现转折. "
        "Use one stable protagonist across every scene; keep the protagonist's "
        "consistency_anchor as a visual descriptor, not just a name. Supporting "
        "characters, if any, must stay secondary and must not replace the protagonist. "
        "Do not use generic speaker names like 主角, 角色, 男主, 女主, or 旁白; "
        "reuse the same named protagonist in scene dialogue and beat dialogue. "
        "Each scene's beat visible_event or action must show that named protagonist "
        "performing a visible action, movement, operation, or reaction. "
        "Within the same scene, every beat visible_event plus action must create a "
        "distinct screen state or new information; do not repeat the same button, alarm, or action. "
        "Every scene must include 3 to 5 beats. The first beat of scene 1 must "
        "be hook, must have duration_seconds <= 3, and its visible_event, action, "
        "or dialogue must show an immediate anomaly, loss, countdown, threat, "
        "evidence, reversal, or urgent question; do not merely introduce arrival "
        "or setting. At least one beat across the script must be payoff. The final "
        "beat must be cliffhanger. Each beat dramatic_purpose must name the specific "
        "story turn, clue, choice, threat, or result; do not write generic purposes "
        "like 推进剧情, 制造悬念, 制造冲突, or 出现转折. Each beat must include duration_seconds > 0, "
        "and the beat duration sum for a scene must match that scene duration. "
        "Beat visible_event and action must describe visible or audible screen behavior; "
        "do not write internal states such as 意识到, 明白, 感到, 内心, 命运, or 关系变化. "
        "Every dialogue line must be <= 15 visible Chinese/English characters. "
        "Dialogue must carry story information; do not use filler-only lines like 好的, 嗯, 知道了, 是的, or 怎么会这样, "
        "and do not repeat the same dialogue line within one scene. Scene-level dialogue must not copy any beat dialogue; "
        "every beat dialogue line in the same scene must be unique. "
        "Scene 1 must open with an immediate conflict or countdown hook. The final "
        "scene must end on an unresolved reversal or question, not a full resolution; "
        "do not end with task complete, crisis solved, all rewards recovered, all alarms off, or system restored. "
        "The final beat must not say the loss already completed, data already lost, "
        "the countdown reached 100%, or the protagonist says 来不及了; after any partial payoff, "
        "reveal a new unresolved threat, unknown operator, hidden file, second countdown, or open question. "
        "Every scene must have question, turn, plot, one or two short dialogue lines, and a Seedance-ready "
        "video prompt that includes the same character anchor and the dialogue source."
    )


def _repair_text(repair_notes: list[str] | None) -> str:
    notes = [str(note).strip() for note in repair_notes or [] if str(note).strip()]
    if not notes:
        return ""
    joined = " | ".join(notes[:8])
    return (
        "Rewrite the previous failed script using these failure notes: "
        f"{joined}. Do not repeat the same plot structure, repeated helper reveal, "
        "or unexplained hidden-code solution. "
    )


def extract_structured_script(
    content: str, expected_scene_count: int
) -> dict[str, Any]:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    elif not text.startswith("{"):
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            text = match.group(0)

    data = json.loads(text)
    scenes = data.get("scenes")
    characters = data.get("characters")
    if not isinstance(characters, list) or not characters:
        raise ValueError("script_missing_characters")
    if not isinstance(scenes, list) or len(scenes) != expected_scene_count:
        raise ValueError("script_scene_count_mismatch")

    for index, scene in enumerate(scenes, start=1):
        dialogue = scene.get("dialogue")
        for field in ("question", "stakes", "opposition", "turn"):
            if not str(scene.get(field) or "").strip():
                raise ValueError(f"script_scene_{index}_missing_{field}")
        if not scene.get("plot") or not scene.get("video_prompt"):
            raise ValueError(f"script_scene_{index}_missing_plot_or_video_prompt")
        if not isinstance(dialogue, list) or not dialogue:
            raise ValueError(f"script_scene_{index}_missing_dialogue")
        for line in dialogue:
            if (
                not isinstance(line, dict)
                or not line.get("speaker")
                or not line.get("line")
            ):
                raise ValueError(f"script_scene_{index}_invalid_dialogue")
        beats = scene.get("beats")
        if not isinstance(beats, list) or len(beats) < 3:
            raise ValueError(f"script_scene_{index}_missing_beats")
        for beat_index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict) or not beat.get("visible_event"):
                raise ValueError(f"script_scene_{index}_beat_{beat_index}_invalid")
    return data


def character_image_prompt(script: dict[str, Any]) -> str:
    character = script["characters"][0]
    return (
        f"{character.get('appearance_prompt', '')}. "
        f"{character.get('consistency_anchor', '')}. "
        "High quality 3D cartoon character reference sheet, expressive LED eyes, "
        "cinematic lighting, clean silhouette, non-real robot, no photorealistic human."
    )


def video_prompt(scene: dict[str, Any], character: dict[str, Any]) -> str:
    dialogue = " / ".join(f"{d['speaker']}: {d['line']}" for d in scene["dialogue"])
    return (
        f"{scene.get('video_prompt')}. "
        f"Character anchor: {character.get('consistency_anchor')}. "
        f"Plot: {scene.get('plot')}. Dialogue source: {dialogue}. "
        "3D cartoon style, non-real robot character, clear acting, readable story beat."
    )
