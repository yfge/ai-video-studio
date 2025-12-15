from __future__ import annotations

import re
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

import httpx
from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene, SceneBeat
from app.services.ai_service import ai_service
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
    concat_file = out_mp3.parent / "concat.txt"
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
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(out_mp3),
        ]
    )


def build_episode_timeline_beats(
    *,
    scenes: Sequence[Scene],
    beats_by_scene_id: dict[int, Sequence[SceneBeat]],
) -> tuple[list[dict[str, Any]], int]:
    offset_ms = 0
    merged: list[dict[str, Any]] = []

    for scene in scenes:
        scene_id = int(scene.id)
        try:
            scene_number = int(str(scene.scene_number).strip())
        except Exception:
            scene_number = None

        cursor_ms = 0
        for beat in beats_by_scene_id.get(scene_id, []):
            meta = beat.extra_metadata if isinstance(beat.extra_metadata, dict) else {}

            start_ms = meta.get("start_ms")
            end_ms = meta.get("end_ms")

            start_ms_int = (
                int(start_ms)
                if isinstance(start_ms, (int, float, str)) and str(start_ms).strip()
                else None
            )
            end_ms_int = (
                int(end_ms)
                if isinstance(end_ms, (int, float, str)) and str(end_ms).strip()
                else None
            )

            if start_ms_int is None:
                start_ms_int = cursor_ms
            if end_ms_int is None:
                dur_s = float(beat.duration_seconds or 0)
                end_ms_int = start_ms_int + max(0, int(round(dur_s * 1000)))
            if end_ms_int < start_ms_int:
                end_ms_int = start_ms_int

            cursor_ms = end_ms_int

            text = (
                beat.dialogue_excerpt
                if beat.beat_type == "dialogue"
                else beat.beat_summary
            )
            merged.append(
                {
                    "scene_id": scene_id,
                    "scene_number": scene_number,
                    "beat_id": int(beat.id),
                    "beat_type": beat.beat_type,
                    "speaker_name": meta.get("speaker_name"),
                    "text": text,
                    "start_ms": offset_ms + start_ms_int,
                    "end_ms": offset_ms + end_ms_int,
                }
            )

        offset_ms += cursor_ms

    return merged, offset_ms


async def generate_scene_dialogue_audio(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scene: Scene,
    tts_model: str = "speech-2.6-hd",
    overwrite_beats: bool = True,
) -> dict[str, Any]:
    """
    Generate 1 dialogue audio track per scene and persist beats into scene_beats.

    Returns the persisted scene.metadata.dialogue_audio payload.
    """
    _ensure_oss_configured()

    scene_number = _extract_scene_number(scene)
    dialogues = _extract_dialogues_for_scene(script, scene_number)
    stage = _extract_stage_for_scene(script, scene_number)
    segments = plan_scene_segments(dialogues=dialogues, stage_directions=stage)

    story_char_map = get_story_character_map(db, story.id)

    # Build wav segments
    with tempfile.TemporaryDirectory(prefix="scene-audio-") as tmp_root:
        tmp_root_path = Path(tmp_root)
        wav_paths: list[Path] = []
        beats: list[dict[str, Any]] = []

        for seg in segments:
            if seg.kind == "pause":
                silence_wav = tmp_root_path / f"pause-{len(wav_paths)+1}.wav"
                _generate_silence_wav(silence_wav, int(seg.planned_duration_ms or 300))
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
                _generate_silence_wav(action_wav, int(seg.planned_duration_ms or 800))
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

            # dialogue segment
            speaker = seg.speaker_name or "旁白"
            speaker_key = _norm_name(speaker)
            voice_config: dict[str, Any]
            speaker_kind: str

            ip = story_char_map.get(speaker_key)
            if ip:
                voice_config = await ensure_virtual_ip_voice_config(
                    db,
                    ip,
                    tts_provider="minimax",
                    tts_model=tts_model,
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

            local_tts = tmp_root_path / f"dlg-{len(wav_paths)+1}.wav"
            tts_emotion = _normalize_tts_emotion(seg.emotion, action=seg.action)
            await _tts_to_wav_file(
                text=seg.text,
                voice_config=voice_config,
                out_path=local_tts,
                emotion=tts_emotion,
            )
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

        # Persist beats into scene_beats
        if overwrite_beats:
            db.query(SceneBeat).filter(SceneBeat.scene_id == scene.id).delete(
                synchronize_session=False
            )

        start_ms = 0
        for idx, beat in enumerate(beats, start=1):
            dur_ms = int(beat.get("duration_ms") or 0)
            end_ms = start_ms + dur_ms
            meta = {
                "start_ms": start_ms,
                "end_ms": end_ms,
                "speaker_name": beat.get("speaker_name"),
                "speaker_kind": beat.get("speaker_kind"),
                "voice_config": beat.get("voice_config"),
                "emotion": beat.get("emotion"),
                "tts_emotion": beat.get("tts_emotion"),
                "action": beat.get("action"),
                "source": "dialogue_audio_pipeline",
            }
            row = SceneBeat(
                scene_id=scene.id,
                order_index=idx,
                beat_type=beat.get("beat_type"),
                beat_summary=beat.get("beat_summary"),
                dialogue_excerpt=beat.get("dialogue_excerpt"),
                duration_seconds=round(dur_ms / 1000.0, 3),
                extra_metadata=meta,
            )
            db.add(row)
            start_ms = end_ms

        # Update scene metadata with audio info
        extra = dict(scene.extra_metadata or {})
        prev = extra.get("dialogue_audio")
        prev_version = 0
        if isinstance(prev, dict):
            try:
                prev_version = int(prev.get("version") or 0)
            except Exception:
                prev_version = 0
        payload = {
            "oss_url": oss_result["file_url"],
            "duration_seconds": duration_seconds_total,
            "generated_at": _utc_now_iso(),
            "version": prev_version + 1,
            "script_id": script.id,
        }
        extra["dialogue_audio"] = payload
        scene.extra_metadata = extra
        db.add(scene)
        db.commit()
        db.refresh(scene)

        return payload


async def generate_episode_audio_timeline(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
) -> dict[str, Any]:
    """
    Concatenate scene dialogue tracks into 1 episode track and merge beats into an episode timeline.

    Writes `episodes.extra_metadata.audio_timeline` and uploads the episode audio to OSS.
    """
    _ensure_oss_configured()

    scenes = db.query(Scene).filter(Scene.script_id == script.id).all()
    scenes_sorted = sorted(
        scenes,
        key=lambda s: (
            1 if str(getattr(s, "scene_number", "")).strip().isdigit() is False else 0,
            (
                int(str(getattr(s, "scene_number", 0)).strip())
                if str(getattr(s, "scene_number", "")).strip().isdigit()
                else 0
            ),
            str(getattr(s, "scene_number", "")),
        ),
    )
    if not scenes_sorted:
        raise RuntimeError("no_scenes_found")

    missing_audio: list[str] = []
    scene_audio_urls: list[str] = []
    scene_ids: list[int] = []
    for scene in scenes_sorted:
        meta = scene.extra_metadata if isinstance(scene.extra_metadata, dict) else {}
        payload = meta.get("dialogue_audio") if isinstance(meta, dict) else None
        if not isinstance(payload, dict) or not payload.get("oss_url"):
            missing_audio.append(str(scene.scene_number))
            continue
        scene_audio_urls.append(str(payload["oss_url"]))
        scene_ids.append(int(scene.id))

    if missing_audio:
        raise RuntimeError(f"missing_scene_dialogue_audio: {', '.join(missing_audio)}")

    beats = (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id.in_(scene_ids))
        .order_by(SceneBeat.scene_id.asc(), SceneBeat.order_index.asc())
        .all()
    )
    beats_by_scene: dict[int, list[SceneBeat]] = {sid: [] for sid in scene_ids}
    for beat in beats:
        beats_by_scene.setdefault(int(beat.scene_id), []).append(beat)

    missing_beats = [
        str(scene.scene_number)
        for scene in scenes_sorted
        if not beats_by_scene.get(int(scene.id))
    ]
    if missing_beats:
        raise RuntimeError(f"missing_scene_beats: {', '.join(missing_beats)}")

    timeline_beats, duration_ms_total = build_episode_timeline_beats(
        scenes=scenes_sorted,
        beats_by_scene_id=beats_by_scene,
    )
    duration_seconds_total = round(duration_ms_total / 1000.0, 3)

    with tempfile.TemporaryDirectory(prefix="episode-audio-") as tmp_root:
        tmp_root_path = Path(tmp_root)
        mp3_paths: list[Path] = []
        for idx, url in enumerate(scene_audio_urls, start=1):
            p = tmp_root_path / f"scene-{idx}.mp3"
            await _download_to_file(str(url), p)
            mp3_paths.append(p)

        episode_mp3 = tmp_root_path / "episode.mp3"
        _concat_mp3s(mp3_paths, episode_mp3)

        oss_result = await oss_service.upload_file_content(
            file_content=episode_mp3.read_bytes(),
            filename=f"episode{episode.id}-script{script.id}.mp3",
            file_type="audio",
            prefix="episode-dialogue/episodes",
            metadata={
                "episode_id": episode.id,
                "script_id": script.id,
                "duration_seconds": duration_seconds_total,
                "generated_at": _utc_now_iso(),
            },
        )
        if not oss_result.get("success") or not oss_result.get("file_url"):
            raise RuntimeError(f"OSS 上传失败: {oss_result}")

    extra = dict(episode.extra_metadata or {})
    prev = extra.get("audio_timeline")
    prev_version = 0
    if isinstance(prev, dict):
        ep_audio = prev.get("episode_audio")
        if isinstance(ep_audio, dict):
            try:
                prev_version = int(ep_audio.get("version") or 0)
            except Exception:
                prev_version = 0

    payload = {
        "script_id": script.id,
        "episode_audio": {
            "oss_url": oss_result["file_url"],
            "duration_seconds": duration_seconds_total,
            "generated_at": _utc_now_iso(),
            "version": prev_version + 1,
        },
        "beats": timeline_beats,
    }
    extra["audio_timeline"] = payload
    episode.extra_metadata = extra
    db.add(episode)
    db.commit()
    db.refresh(episode)

    return payload


def build_storyboard_frames_from_audio_timeline(
    *,
    audio_timeline: dict[str, Any],
    min_pause_duration_ms: int = 1500,
) -> list[dict[str, Any]]:
    beats = audio_timeline.get("beats") if isinstance(audio_timeline, dict) else None
    if not isinstance(beats, list):
        raise RuntimeError("audio_timeline_missing_beats")

    frames: list[dict[str, Any]] = []
    scene_index_map: dict[int, int] = {}
    next_scene_index = 1

    for beat in beats:
        if not isinstance(beat, dict):
            continue
        beat_type = beat.get("beat_type")
        if beat_type not in {"dialogue", "action", "pause"}:
            continue

        start_ms = beat.get("start_ms")
        end_ms = beat.get("end_ms")
        if start_ms is None or end_ms is None:
            continue
        try:
            start_ms_int = int(start_ms)
            end_ms_int = int(end_ms)
        except Exception:
            continue
        if end_ms_int < start_ms_int:
            continue

        duration_ms = end_ms_int - start_ms_int
        if beat_type == "pause" and duration_ms < min_pause_duration_ms:
            continue

        scene_id = beat.get("scene_id")
        scene_id_int = (
            int(scene_id)
            if isinstance(scene_id, (int, str)) and str(scene_id).strip()
            else None
        )
        scene_number = beat.get("scene_number")
        try:
            scene_number_int = int(scene_number) if scene_number is not None else None
        except Exception:
            scene_number_int = None

        if scene_id_int is not None and scene_id_int not in scene_index_map:
            scene_index_map[scene_id_int] = next_scene_index
            next_scene_index += 1

        speaker = (
            (beat.get("speaker_name") or "旁白") if beat_type == "dialogue" else None
        )
        text = (beat.get("text") or "").strip()
        if beat_type == "dialogue":
            description = f"{speaker}: {text}".strip() if text else str(speaker)
        elif beat_type == "pause":
            description = "（停顿）"
        else:
            description = text or "（动作）"

        frames.append(
            {
                "frame_id": str(uuid4()),
                "frame_number": len(frames) + 1,
                "scene_number": scene_number_int,
                "scene_index": (
                    scene_index_map.get(scene_id_int)
                    if scene_id_int is not None
                    else None
                ),
                "description": description,
                "duration_seconds": round(duration_ms / 1000.0, 3),
                "generation_source": "audio_timeline",
                "generation_method": "audio_timeline",
                "status": "draft",
                "start_ms": start_ms_int,
                "end_ms": end_ms_int,
            }
        )

    return frames


def generate_storyboard_from_episode_audio_timeline(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    overwrite_existing: bool = False,
    min_pause_duration_ms: int = 1500,
) -> dict[str, Any]:
    """Generate storyboard frame placeholders from episode audio timeline and persist into script.extra_metadata."""
    ep_meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    audio_timeline = (
        ep_meta.get("audio_timeline") if isinstance(ep_meta, dict) else None
    )
    if not isinstance(audio_timeline, dict):
        raise RuntimeError("episode_audio_timeline_not_found")
    if audio_timeline.get("script_id") != script.id:
        raise RuntimeError("audio_timeline_script_mismatch")

    frames = build_storyboard_frames_from_audio_timeline(
        audio_timeline=audio_timeline,
        min_pause_duration_ms=min_pause_duration_ms,
    )
    if not frames:
        raise RuntimeError("no_frames_generated_from_audio_timeline")

    extra = dict(script.extra_metadata or {})
    existing = extra.get("storyboard") if isinstance(extra, dict) else None
    if not overwrite_existing and isinstance(existing, dict):
        existing_frames = existing.get("frames")
        if isinstance(existing_frames, list):
            for frame in existing_frames:
                if not isinstance(frame, dict):
                    continue
                if any(
                    frame.get(key)
                    for key in (
                        "image_url",
                        "start_image_url",
                        "start_image_urls",
                        "end_image_url",
                        "end_image_urls",
                        "video_url",
                        "video_urls",
                    )
                ):
                    raise RuntimeError(
                        "storyboard_has_assets_refuse_overwrite: set overwrite_existing=true"
                    )

    sb_meta = {
        "generated_at": _utc_now_iso(),
        "generation_source": "audio_timeline",
        "generation_method": "audio_timeline",
        "script_id": script.id,
        "episode_id": episode.id,
        "audio_timeline_version": (audio_timeline.get("episode_audio") or {}).get(
            "version"
        ),
    }
    extra["storyboard"] = {"frames": frames, "meta": sb_meta}
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.utcnow()
    script.storyboard_version = (script.storyboard_version or 0) + 1
    db.add(script)
    db.commit()
    db.refresh(script)

    return {"frames": frames, "meta": sb_meta}
