from __future__ import annotations

import re
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.ai_service import ai_service
from app.services.audio.dialogue_processing.prose_dialogue_splitter import (
    repair_scene_dialogues_for_audio,
    sanitize_stage_directions_for_audio,
)
from app.services.audio.dialogue_processor import plan_scene_segments_intelligent

# Re-export episode timeline helpers from the historical service module.
from app.services.audio.episode_audio_builder import (  # noqa: F401
    generate_episode_audio_timeline,
)
from app.services.audio.episode_timeline_beats import (  # noqa: F401
    build_episode_timeline_beats,
)
from app.services.audio.scene_audio_persistence import (
    persist_beats,
    update_scene_metadata,
    validate_duration,
)

# Re-export storyboard timeline helpers from the historical service module.
from app.services.audio.storyboard_from_timeline import (  # noqa: F401
    build_storyboard_frames_from_audio_timeline,
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.audio.time_stretch import time_stretch_wav_ffmpeg_args
from app.services.script.script_character_policy import build_story_alias_map
from app.services.storage.oss_service import oss_service
from app.services.voice_binding_service import (
    ensure_derived_character_voice_binding,
    ensure_virtual_ip_voice_config,
    get_story_character_map,
)
from sqlalchemy.orm import Session

logger = get_logger(__name__)

_ALLOWED_TTS_EMOTIONS = {
    "happy",
    "sad",
    "angry",
    "fearful",
    "disgusted",
    "surprised",
    "calm",
    "fluent",
    "whisper",
}


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _norm_name(name: str) -> str:
    return "".join((name or "").strip().lower().split())


_ONLY_PUNCT_OR_SPACE = re.compile(
    r"^[\s\.\,\!\?\-\—\_\~\·\…\，\。\！\？\、\：\；\“\”\(\)\（\）]+$"
)

_LEADING_INLINE_ACTION_RE = re.compile(
    r"^\s*[\(\（\[\【](?P<action>[^)\）\]\】]{1,200})[\)\）\]\】]\s*"
)
_TRAILING_INLINE_ACTION_RE = re.compile(
    r"\s*[\(\（\[\【](?P<action>[^)\）\]\】]{1,200})[\)\）\]\】]\s*$"
)
_SPEECH_ATTR_RE = re.compile(
    r"^\s*(?P<attr>.{1,80}?)(?P<sep>[:：]|\s+|“|\"|‘|'|「|『)(?P<text>.+)$"
)
_TRIVIAL_SPEECH_ATTR_RE = re.compile(
    r"^(?:我|你|他|她|它|我们|你们|他们|她们|大家|众人|所有人)(?:们)?(?:说|说道|问|问道|答|答道)$"
)
_SPEECH_ATTR_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            "低声说",
            "轻声说",
            "小声说",
            "大声说",
            "笑着说",
            "冷冷地说",
            "嘀咕道",
            "呢喃道",
            "咆哮道",
            "吼道",
            "喊道",
            "说道",
            "问道",
            "答道",
            "说",
            "问",
            "答",
        },
        key=len,
        reverse=True,
    )
)


def _looks_like_silence(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if _ONLY_PUNCT_OR_SPACE.match(cleaned):
        return True
    lowered = cleaned.lower()
    if lowered in {"...", "……", "…", "（沉默）", "(silence)", "[silence]"}:
        return True
    return False


def _sanitize_dialogue_content(
    content: str,
    *,
    action: str | None = None,
) -> tuple[str, str | None]:
    """
    Remove inline stage directions from dialogue text.

    Examples:
    - "（叹气）你好" -> text="你好", action+="叹气"
    - "叹了一口气，站起来说：你好" -> text="你好", action+="叹了一口气，站起来说"
    """

    text = str(content or "").strip()
    actions: list[str] = []

    if isinstance(action, str) and action.strip():
        actions.append(action.strip())

    while True:
        m = _LEADING_INLINE_ACTION_RE.match(text)
        if not m:
            break
        inline = m.group("action").strip()
        if inline:
            actions.append(inline)
        text = text[m.end() :].strip()

    while True:
        m = _TRAILING_INLINE_ACTION_RE.search(text)
        if not m:
            break
        inline = m.group("action").strip()
        if inline:
            actions.append(inline)
        text = text[: m.start()].strip()

    m = _SPEECH_ATTR_RE.match(text)
    if m:
        attr = (m.group("attr") or "").strip()
        attr_no_space = "".join(attr.split())
        suffix_ok = any(attr_no_space.endswith(suf) for suf in _SPEECH_ATTR_SUFFIXES)
        if (
            suffix_ok
            and attr_no_space
            and not _TRIVIAL_SPEECH_ATTR_RE.match(attr_no_space)
        ):
            actions.append(attr)
            sep = m.group("sep") or ""
            rest = (m.group("text") or "").strip()
            if sep.strip() and sep in {"“", '"', "‘", "'", "「", "『"}:
                rest = f"{sep}{rest}"
            text = rest.strip()

    text = re.sub(r"\s+", " ", text).strip()
    text = text.lstrip("：:，,。．·-— ").strip()

    seen: set[str] = set()
    merged: list[str] = []
    for item in actions:
        normalized = "".join(item.strip().split())
        if not normalized or normalized in seen:
            continue
        merged.append(item.strip())
        seen.add(normalized)

    merged_action = "；".join(merged) if merged else None
    return text, merged_action


def _extract_scene_number(scene: Scene) -> int:
    try:
        return int(str(scene.scene_number).strip())
    except Exception:
        return int(scene.id)


def _extract_dialogues_for_scene(
    script: Script, scene_number: int
) -> list[dict[str, Any]]:
    items = script.dialogues or []
    results: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sn = item.get("scene_number")
        try:
            sn_int = int(sn)
        except Exception:
            continue
        if sn_int != scene_number:
            continue
        content = item.get("content") or item.get("text") or item.get("line") or ""
        character = item.get("character") or item.get("speaker") or "旁白"
        emotion_raw = item.get("emotion")
        emotion = str(emotion_raw).strip() if isinstance(emotion_raw, str) else None
        emotion = emotion or None
        action_raw = item.get("action")
        action = str(action_raw).strip() if isinstance(action_raw, str) else None
        action = action or None
        spoken, merged_action = _sanitize_dialogue_content(str(content), action=action)
        results.append(
            {
                "character": str(character),
                "content": spoken,
                "emotion": emotion,
                "action": merged_action,
            }
        )
    return results


def _extract_stage_for_scene(script: Script, scene_number: int) -> list[dict[str, Any]]:
    items = script.stage_directions or []
    results: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sn = item.get("scene_number")
        try:
            sn_int = int(sn)
        except Exception:
            continue
        if sn_int != scene_number:
            continue
        content = (
            item.get("content")
            or item.get("direction")
            or item.get("description")
            or ""
        )
        timing = item.get("timing") or "mid"
        results.append({"content": str(content), "timing": str(timing)})
    return results


@dataclass(frozen=True)
class PlannedSegment:
    kind: str  # dialogue | action | pause
    text: str
    speaker_name: str | None = None
    emotion: str | None = None
    action: str | None = None
    timing: str | None = None  # start/mid/end (for action)
    planned_duration_ms: int | None = None


def plan_scene_segments(
    *,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
    pause_after_dialogue_ms: int = 300,
    action_base_ms: int = 800,
    action_per_char_ms: int = 20,
    action_max_ms: int = 3000,
) -> list[PlannedSegment]:
    """
    Build an ordered segment plan for a scene.

    - Dialogue: TTS
    - Action: silence placeholder (MVP)
    - Pause: silence
    """
    stages_start: list[str] = []
    stages_mid: list[str] = []
    stages_end: list[str] = []
    for sd in stage_directions:
        if not isinstance(sd, dict):
            continue
        content = str(sd.get("content") or "").strip()
        if not content:
            continue
        timing = str(sd.get("timing") or "mid").strip().lower()
        if timing in {"start", "begin", "opening"}:
            stages_start.append(content)
        elif timing in {"end", "closing"}:
            stages_end.append(content)
        else:
            stages_mid.append(content)

    planned: list[PlannedSegment] = []

    def _action_duration_ms(content: str) -> int:
        length = len(content)
        return min(
            action_max_ms,
            max(action_base_ms, action_base_ms + length * action_per_char_ms),
        )

    for content in stages_start:
        planned.append(
            PlannedSegment(
                kind="action",
                text=content,
                timing="start",
                planned_duration_ms=_action_duration_ms(content),
            )
        )

    # Insert mid-stage directions roughly after the first dialogue, otherwise at end.
    mid_inserted = False

    for idx, dlg in enumerate(dialogues):
        speaker = str(dlg.get("character") or "旁白")
        content = str(dlg.get("content") or "").strip()
        emotion = (
            str(dlg.get("emotion") or "").strip()
            if isinstance(dlg.get("emotion"), str)
            else None
        )
        emotion = emotion or None
        action = (
            str(dlg.get("action") or "").strip()
            if isinstance(dlg.get("action"), str)
            else None
        )
        action = action or None
        if _looks_like_silence(content):
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text=content or "…",
                    speaker_name=speaker,
                    emotion=emotion,
                    action=action,
                    planned_duration_ms=800,
                )
            )
        else:
            planned.append(
                PlannedSegment(
                    kind="dialogue",
                    text=content,
                    speaker_name=speaker,
                    emotion=emotion,
                    action=action,
                )
            )
        planned.append(
            PlannedSegment(
                kind="pause", text="", planned_duration_ms=pause_after_dialogue_ms
            )
        )

        if not mid_inserted and stages_mid:
            # place mid-stage after first dialogue beat
            for content_mid in stages_mid:
                planned.append(
                    PlannedSegment(
                        kind="action",
                        text=content_mid,
                        timing="mid",
                        planned_duration_ms=_action_duration_ms(content_mid),
                    )
                )
                planned.append(
                    PlannedSegment(
                        kind="pause",
                        text="",
                        planned_duration_ms=pause_after_dialogue_ms,
                    )
                )
            mid_inserted = True

    if stages_mid and not mid_inserted:
        for content_mid in stages_mid:
            planned.append(
                PlannedSegment(
                    kind="action",
                    text=content_mid,
                    timing="mid",
                    planned_duration_ms=_action_duration_ms(content_mid),
                )
            )
            planned.append(
                PlannedSegment(
                    kind="pause", text="", planned_duration_ms=pause_after_dialogue_ms
                )
            )

    for content in stages_end:
        planned.append(
            PlannedSegment(
                kind="action",
                text=content,
                timing="end",
                planned_duration_ms=_action_duration_ms(content),
            )
        )
        planned.append(
            PlannedSegment(
                kind="pause", text="", planned_duration_ms=pause_after_dialogue_ms
            )
        )

    # Scene with no dialogue and no stage directions: add a minimum placeholder.
    has_meaningful = any(
        (
            (seg.kind in {"dialogue", "action"} and seg.text.strip())
            or (seg.kind == "pause" and seg.text.strip())
        )
        for seg in planned
    )
    if not has_meaningful:
        planned = [
            PlannedSegment(
                kind="action",
                text="(no_dialogue)",
                timing="mid",
                planned_duration_ms=2000,
            )
        ]

    return planned


def _ensure_oss_configured() -> None:
    if not oss_service:
        raise RuntimeError("OSS 服务未配置，无法生成并持久化音频")


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        if not rate:
            return 0
        return int(round(frames * 1000 / rate))


def _run_ffmpeg(args: list[str]) -> None:
    completed = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg_failed: {completed.stderr[-2000:]}")


def _generate_silence_wav(
    path: Path, duration_ms: int, sample_rate: int = 24000
) -> None:
    duration_s = max(0.0, float(duration_ms) / 1000.0)
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=channel_layout=mono:sample_rate={sample_rate}",
            "-t",
            f"{duration_s:.3f}",
            "-acodec",
            "pcm_s16le",
            str(path),
        ]
    )


def _normalize_wav(
    in_path: Path,
    out_path: Path,
    *,
    sample_rate: int = 24000,
) -> None:
    """Normalize WAVs to a consistent format for ffmpeg concat."""

    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(in_path),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            str(out_path),
        ]
    )


async def _download_to_file(url: str, path: Path) -> None:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        path.write_bytes(resp.content)


async def _tts_to_wav_file(
    *,
    text: str,
    voice_config: dict[str, Any],
    out_path: Path,
    emotion: str | None = None,
    tts_speed: float = 1.0,
    tts_format: str = "wav",
) -> None:
    if not ai_service.ai_manager:
        raise RuntimeError("AI 管理器未初始化，无法进行 TTS")

    provider = (voice_config.get("provider") or "minimax").strip()
    model = (voice_config.get("tts_model") or "speech-2.6-hd").strip()
    voice_id = (voice_config.get("voice_id") or "").strip() or None
    voice_type = (voice_config.get("voice_type") or "").strip() or None

    kwargs: dict[str, Any] = {"format": tts_format}
    if voice_id:
        kwargs["voice_id"] = voice_id
    if voice_type:
        kwargs["voice_type"] = voice_type
    if emotion:
        kwargs["emotion"] = emotion

    resp = await ai_service.ai_manager.text_to_speech(
        text=text,
        model=model,
        prefer_provider=provider,
        speed=tts_speed,
        **kwargs,
    )
    if not resp.success:
        raise RuntimeError(resp.error or "TTS failed")
    audio_url = None
    if isinstance(resp.data, dict):
        audio_url = resp.data.get("audio_url")
    if not audio_url:
        raise RuntimeError("TTS did not return audio_url")

    await _download_to_file(str(audio_url), out_path)


def _normalize_tts_emotion(
    emotion: str | None,
    *,
    action: str | None = None,
) -> str | None:
    if not emotion and not action:
        return None

    raw = " ".join(
        v.strip()
        for v in [emotion or "", action or ""]
        if isinstance(v, str) and v.strip()
    )
    if not raw:
        return None

    raw_lower = raw.lower()
    if isinstance(emotion, str) and emotion.strip().lower() in _ALLOWED_TTS_EMOTIONS:
        return emotion.strip().lower()

    def _has_any(tokens: Sequence[str]) -> bool:
        return any(tok in raw_lower for tok in tokens)

    if _has_any(
        ["whisper", "低语", "耳语", "压低", "小声", "悄声", "轻声", "低声", "自语"]
    ):
        return "whisper"
    if _has_any(["angry", "愤怒", "生气", "恼火", "怒", "火大", "暴躁"]):
        return "angry"
    if _has_any(
        [
            "sad",
            "悲伤",
            "难过",
            "沮丧",
            "哽咽",
            "哭",
            "伤心",
            "叹气",
            "叹了口气",
            "叹了一口气",
            "叹息",
            "长叹",
        ]
    ):
        return "sad"
    if _has_any(["happy", "高兴", "开心", "喜悦", "兴奋", "激动", "欢快", "愉快"]):
        return "happy"
    if _has_any(["surprised", "惊讶", "吃惊", "震惊", "惊"]):
        return "surprised"
    if _has_any(["fearful", "害怕", "恐惧", "紧张", "慌", "担心", "焦虑", "畏惧"]):
        return "fearful"
    if _has_any(["disgusted", "厌恶", "恶心", "反感"]):
        return "disgusted"
    if _has_any(
        [
            "calm",
            "neutral",
            "thoughtful",
            "平静",
            "冷静",
            "中性",
            "沉稳",
            "严肃",
            "思考",
            "克制",
        ]
    ):
        return "calm"
    if _has_any(
        [
            "fluent",
            "confident",
            "assertive",
            "自信",
            "坚定",
            "果断",
            "专业",
            "流利",
            "从容",
        ]
    ):
        return "fluent"

    # Safety fallback: do not send an unknown label to provider.
    return None


def _concat_wavs(paths: Sequence[Path], out_wav: Path) -> None:
    concat_file = out_wav.parent / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in paths), encoding="utf-8"
    )
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "24000",
            str(out_wav),
        ]
    )


def _encode_mp3(in_wav: Path, out_mp3: Path) -> None:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(in_wav),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(out_mp3),
        ]
    )


def _concat_mp3s(paths: Sequence[Path], out_mp3: Path) -> None:
    """Concatenate MP3s into 1 MP3.

    Workaround: Some ffmpeg builds may fail when re-encoding directly from the
    concat demuxer (`inadequate AVFrame plane padding`). Decode to normalized
    WAV first, concat WAV, then encode once.
    """
    if not paths:
        raise RuntimeError("no_mp3s_to_concat")

    tmp_dir = out_mp3.parent
    wav_paths: list[Path] = []
    for idx, mp3 in enumerate(paths, start=1):
        wav = tmp_dir / f"concat-src-{idx}.wav"
        _normalize_wav(mp3, wav)
        wav_paths.append(wav)

    merged_wav = tmp_dir / "concat-merged.wav"
    _concat_wavs(wav_paths, merged_wav)
    _encode_mp3(merged_wav, out_mp3)


async def generate_scene_dialogue_audio(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scene: Scene,
    tts_model: str = "speech-2.6-hd",
    overwrite_beats: bool = True,
    use_intelligent_timing: bool = True,
    timing_model: str | None = None,
    target_duration_seconds: int | None = None,
) -> dict[str, Any]:
    """
    Generate 1 dialogue audio track per scene and persist beats into scene_beats.

    Two-phase flow for accurate duration control:
    1. Generate TTS for all dialogues first → get actual durations
    2. Call Timeline Agent with actual durations → compute GAPs dynamically
    3. Assemble audio with computed GAPs

    Args:
        use_intelligent_timing: If True, uses AI agent to compute context-aware
            pause durations. Falls back to fixed 300ms pauses on failure.
        timing_model: LLM model to use for timeline calculation. Uses system
            default if not specified.
        target_duration_seconds: Optional target scene duration. When provided,
            gaps will be calculated to help reach the target duration.

    Returns the persisted scene.metadata.dialogue_audio payload.
    """
    _ensure_oss_configured()

    scene_number = _extract_scene_number(scene)
    dialogues = _extract_dialogues_for_scene(script, scene_number)
    stage = _extract_stage_for_scene(script, scene_number)

    # Build scene context for intelligent timing
    scene_context = {
        "scene_id": scene.id,
        "scene_number": scene_number,
        "slug_line": getattr(scene, "slug_line", None),
        "location": getattr(scene, "location", None),
        "time_of_day": getattr(scene, "time_of_day", None),
        "summary": getattr(scene, "summary", None),
        "primary_characters": getattr(scene, "primary_characters", None),
        "conflict_notes": getattr(scene, "conflict_notes", None),
        "dramatic_question": None,
    }
    # Try to get dramatic_question from step_outline if available
    if hasattr(scene, "step_outline") and scene.step_outline:
        scene_context["dramatic_question"] = getattr(
            scene.step_outline, "dramatic_question", None
        )

    story_char_map = get_story_character_map(db, story.id)
    alias_to_canonical = build_story_alias_map(story)
    dialogues = repair_scene_dialogues_for_audio(
        dialogues, alias_to_canonical=alias_to_canonical
    )
    stage = sanitize_stage_directions_for_audio(
        stage, alias_to_canonical=alias_to_canonical
    )
    scene_character_names: list[str] = []
    for dlg in dialogues or []:
        if not isinstance(dlg, dict):
            continue
        name = (dlg.get("character") or "").strip()
        if not name or name == "旁白":
            continue
        if name in scene_character_names:
            continue
        scene_character_names.append(name)

    # Use single temp directory for all phases (TTS generation + assembly)
    with tempfile.TemporaryDirectory(prefix="scene-audio-") as tmp_root:
        tmp_root_path = Path(tmp_root)

        # ========== PHASE 1: Generate TTS for all dialogues first ==========
        # This gives us actual durations before computing GAPs
        dialogue_tts_results: list[dict[str, Any]] = []
        total_dialogue_duration_ms = 0

        for idx, dlg in enumerate(dialogues):
            speaker = dlg.get("character") or "旁白"
            content = dlg.get("content") or ""
            emotion = dlg.get("emotion")
            action = dlg.get("action")

            if not content.strip():
                continue

            speaker_key = _norm_name(speaker)
            ip = story_char_map.get(speaker_key)

            if ip:
                voice_config = await ensure_virtual_ip_voice_config(
                    db, ip, tts_provider="minimax", tts_model=tts_model
                )
                speaker_kind = "virtual_ip"
            else:
                _, voice_config = await ensure_derived_character_voice_binding(
                    db,
                    story=story,
                    episode=episode,
                    scene=scene,
                    script_dialogues=script.dialogues or [],
                    character_name=speaker,
                    tts_provider="minimax",
                    tts_model=tts_model,
                )
                speaker_kind = "derived"

            tts_wav_raw_path = tmp_root_path / f"phase1-dlg-{idx}-raw.wav"
            tts_wav_path = tmp_root_path / f"phase1-dlg-{idx}.wav"
            tts_emotion = _normalize_tts_emotion(emotion, action=action)
            await _tts_to_wav_file(
                text=content,
                voice_config=voice_config,
                out_path=tts_wav_raw_path,
                emotion=tts_emotion,
            )
            _normalize_wav(tts_wav_raw_path, tts_wav_path)
            actual_duration_ms = _wav_duration_ms(tts_wav_path)
            total_dialogue_duration_ms += actual_duration_ms

            dialogue_tts_results.append(
                {
                    "index": idx,
                    "speaker": speaker,
                    "speaker_kind": speaker_kind,
                    "content": content,
                    "emotion": emotion,
                    "action": action,
                    "tts_emotion": tts_emotion,
                    "voice_config": voice_config,
                    "wav_path": tts_wav_path,  # Keep as Path, not string
                    "actual_duration_ms": actual_duration_ms,
                }
            )

        # If dialogues alone already exceed the scene target, compress dialogues
        # so the full scene can still fit the planned duration budget.
        if target_duration_seconds and dialogue_tts_results:
            target_ms = int(target_duration_seconds * 1000)
            # Keep a small reserved window for non-dialogue beats (actions/pause)
            # so storyboard generation still has room to breathe.
            reserved_non_dialogue_ms = 1000
            allowed_dialogue_ms = max(1000, target_ms - reserved_non_dialogue_ms)
            if total_dialogue_duration_ms > allowed_dialogue_ms:
                speed = total_dialogue_duration_ms / allowed_dialogue_ms
                logger.warning(
                    "Dialogues exceed scene target; time-stretching dialogues",
                    extra={
                        "scene_id": scene.id,
                        "scene_number": scene_number,
                        "target_duration_seconds": target_duration_seconds,
                        "target_ms": target_ms,
                        "dialogue_ms_before": total_dialogue_duration_ms,
                        "dialogue_ms_allowed": allowed_dialogue_ms,
                        "speed_factor": round(speed, 3),
                    },
                )
                new_total_dialogue_ms = 0
                for res in dialogue_tts_results:
                    stretched_path = (
                        tmp_root_path / f"phase1-dlg-{res['index']}-stretched.wav"
                    )
                    _run_ffmpeg(
                        time_stretch_wav_ffmpeg_args(
                            in_path=res["wav_path"],
                            out_path=stretched_path,
                            speed=speed,
                        )
                    )
                    new_ms = _wav_duration_ms(stretched_path)
                    res["wav_path"] = stretched_path
                    res["actual_duration_ms"] = new_ms
                    res["audio_speed"] = round(speed, 6)
                    new_total_dialogue_ms += new_ms

                total_dialogue_duration_ms = new_total_dialogue_ms

        # ========== PHASE 2: Compute GAPs with actual durations ==========
        # Update dialogues with actual durations for Timeline Agent
        dialogues_with_actual_duration = []
        for dlg in dialogues:
            dlg_copy = dict(dlg)
            # Find matching TTS result by content
            for tts_res in dialogue_tts_results:
                if tts_res["content"] == dlg.get("content"):
                    dlg_copy["actual_duration_ms"] = tts_res["actual_duration_ms"]
                    break
            dialogues_with_actual_duration.append(dlg_copy)

        # Log actual vs target duration
        if target_duration_seconds:
            target_ms = target_duration_seconds * 1000
            available_gap_ms = target_ms - total_dialogue_duration_ms
            logger.info(
                "Phase 2: Computing GAPs with actual dialogue durations",
                extra={
                    "scene_id": scene.id,
                    "scene_number": scene_number,
                    "target_duration_seconds": target_duration_seconds,
                    "total_dialogue_duration_ms": total_dialogue_duration_ms,
                    "available_gap_ms": available_gap_ms,
                    "dialogue_count": len(dialogue_tts_results),
                },
            )

        # If the scene is already "tight" (dialogues occupy most of the budget),
        # constrain non-dialogue beats to avoid overshooting the target duration.
        action_base_ms = 800
        action_per_char_ms = 20
        action_max_ms = 3000
        pause_after_dialogue_ms = 300
        effective_stage = stage
        effective_use_intelligent_timing = use_intelligent_timing

        if target_duration_seconds:
            target_ms = int(target_duration_seconds * 1000)
            if total_dialogue_duration_ms >= target_ms:
                pause_after_dialogue_ms = 0
                effective_use_intelligent_timing = False
                # Keep at most 1 compact action beat so downstream storyboard has context.
                if stage:
                    combined = "；".join(
                        str(s.get("content") or "").strip()
                        for s in stage
                        if isinstance(s, dict) and str(s.get("content") or "").strip()
                    )
                    combined = combined.strip()
                    if combined:
                        effective_stage = [{"content": combined[:300], "timing": "mid"}]
                        action_base_ms = 1000
                        action_per_char_ms = 0
                        action_max_ms = 1000
                    else:
                        effective_stage = []
                        action_base_ms = 0
                        action_per_char_ms = 0
                        action_max_ms = 0
                else:
                    effective_stage = []
                    action_base_ms = 0
                    action_per_char_ms = 0
                    action_max_ms = 0

        # Call Timeline Agent with actual durations
        segments = await plan_scene_segments_intelligent(
            dialogues=dialogues_with_actual_duration,
            stage_directions=effective_stage,
            scene_context=scene_context,
            ai_service=ai_service,
            use_intelligent_timing=effective_use_intelligent_timing,
            pause_after_dialogue_ms=pause_after_dialogue_ms,
            action_base_ms=action_base_ms,
            action_per_char_ms=action_per_char_ms,
            action_max_ms=action_max_ms,
            timing_model=timing_model,
            target_duration_seconds=target_duration_seconds,
        )

        # ========== PHASE 3: Assemble audio with computed GAPs ==========
        # Reuse pre-generated TTS files from Phase 1
        wav_paths: list[Path] = []
        beats: list[dict[str, Any]] = []

        # Build a lookup map for pre-generated TTS by content
        tts_lookup: dict[str, dict[str, Any]] = {
            res["content"]: res for res in dialogue_tts_results
        }

        for seg in segments:
            if seg.kind == "pause":
                silence_wav = tmp_root_path / f"pause-{len(wav_paths)+1}.wav"
                planned_ms = (
                    int(seg.planned_duration_ms)
                    if seg.planned_duration_ms is not None
                    else 300
                )
                _generate_silence_wav(silence_wav, planned_ms)
                dur_ms = _wav_duration_ms(silence_wav)
                wav_paths.append(silence_wav)
                beats.append(
                    {
                        "beat_type": "pause",
                        "dialogue_excerpt": None,
                        "beat_summary": None,
                        "speaker_name": None,
                        "speaker_kind": None,
                        "voice_config": None,
                        "duration_ms": dur_ms,
                    }
                )
                continue

            if seg.kind == "action":
                action_wav = tmp_root_path / f"action-{len(wav_paths)+1}.wav"
                planned_ms = (
                    int(seg.planned_duration_ms)
                    if seg.planned_duration_ms is not None
                    else 800
                )
                _generate_silence_wav(action_wav, planned_ms)
                dur_ms = _wav_duration_ms(action_wav)
                wav_paths.append(action_wav)
                beats.append(
                    {
                        "beat_type": "action",
                        "dialogue_excerpt": None,
                        "beat_summary": seg.text,
                        "speaker_name": None,
                        "speaker_kind": None,
                        "voice_config": None,
                        "duration_ms": dur_ms,
                    }
                )
                continue

            # dialogue segment - reuse pre-generated TTS from Phase 1
            tts_result = tts_lookup.get(seg.text)

            if tts_result:
                # Reuse the pre-generated TTS file
                wav_paths.append(tts_result["wav_path"])
                beats.append(
                    {
                        "beat_type": "dialogue",
                        "dialogue_excerpt": seg.text,
                        "beat_summary": None,
                        "speaker_name": tts_result["speaker"],
                        "speaker_kind": tts_result["speaker_kind"],
                        "voice_config": tts_result["voice_config"],
                        "emotion": tts_result["emotion"],
                        "tts_emotion": tts_result["tts_emotion"],
                        "action": tts_result["action"],
                        "duration_ms": tts_result["actual_duration_ms"],
                    }
                )
            else:
                # Fallback: TTS not found in Phase 1 (shouldn't happen normally)
                # Generate TTS on-the-fly as fallback
                logger.warning(
                    "Dialogue not found in Phase 1 TTS cache, generating on-the-fly",
                    extra={
                        "scene_id": scene.id,
                        "scene_number": scene_number,
                        "text_preview": seg.text[:50] if seg.text else None,
                    },
                )
                speaker = seg.speaker_name or "旁白"
                speaker_key = _norm_name(speaker)
                ip = story_char_map.get(speaker_key)

                if ip:
                    voice_config = await ensure_virtual_ip_voice_config(
                        db, ip, tts_provider="minimax", tts_model=tts_model
                    )
                    speaker_kind = "virtual_ip"
                else:
                    _, voice_config = await ensure_derived_character_voice_binding(
                        db,
                        story=story,
                        episode=episode,
                        scene=scene,
                        script_dialogues=script.dialogues or [],
                        character_name=speaker,
                        tts_provider="minimax",
                        tts_model=tts_model,
                    )
                    speaker_kind = "derived"

                local_tts_raw = (
                    tmp_root_path / f"fallback-dlg-{len(wav_paths)+1}-raw.wav"
                )
                local_tts = tmp_root_path / f"fallback-dlg-{len(wav_paths)+1}.wav"
                tts_emotion = _normalize_tts_emotion(seg.emotion, action=seg.action)
                await _tts_to_wav_file(
                    text=seg.text,
                    voice_config=voice_config,
                    out_path=local_tts_raw,
                    emotion=tts_emotion,
                )
                _normalize_wav(local_tts_raw, local_tts)
                dur_ms = _wav_duration_ms(local_tts)
                wav_paths.append(local_tts)
                beats.append(
                    {
                        "beat_type": "dialogue",
                        "dialogue_excerpt": seg.text,
                        "beat_summary": None,
                        "speaker_name": speaker,
                        "speaker_kind": speaker_kind,
                        "voice_config": voice_config,
                        "emotion": seg.emotion,
                        "tts_emotion": tts_emotion,
                        "action": seg.action,
                        "duration_ms": dur_ms,
                    }
                )

        scene_wav = tmp_root_path / "scene.wav"
        _concat_wavs(wav_paths, scene_wav)
        scene_mp3 = tmp_root_path / "scene.mp3"
        _encode_mp3(scene_wav, scene_mp3)

        duration_ms_total = _wav_duration_ms(scene_wav)
        duration_seconds_total = round(duration_ms_total / 1000.0, 3)

        validate_duration(
            scene,
            scene_number,
            duration_ms_total,
            duration_seconds_total,
            target_duration_seconds,
        )

        oss_result = await oss_service.upload_file_content(
            file_content=scene_mp3.read_bytes(),
            filename=f"episode{episode.id}-scene{scene_number}.mp3",
            file_type="audio",
            prefix="episode-dialogue/scenes",
            metadata={
                "episode_id": episode.id,
                "scene_id": scene.id,
                "scene_number": scene_number,
                "duration_seconds": duration_seconds_total,
                "generated_at": _utc_now_iso(),
            },
        )
        if not oss_result.get("success") or not oss_result.get("file_url"):
            raise RuntimeError(f"OSS 上传失败: {oss_result}")

        persist_beats(db, beats, scene, scene_character_names, overwrite_beats)
        return update_scene_metadata(
            db, scene, script, oss_result, duration_seconds_total
        )
