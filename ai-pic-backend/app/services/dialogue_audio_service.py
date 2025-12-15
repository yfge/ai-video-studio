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


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _norm_name(name: str) -> str:
    return "".join((name or "").strip().lower().split())


_ONLY_PUNCT_OR_SPACE = re.compile(
    r"^[\s\.\,\!\?\-\—\_\~\·\…\，\。\！\？\、\：\；\“\”\(\)\（\）]+$"
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
        results.append({"character": str(character), "content": str(content)})
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
        if _looks_like_silence(content):
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text=content or "…",
                    speaker_name=speaker,
                    planned_duration_ms=800,
                )
            )
        else:
            planned.append(
                PlannedSegment(kind="dialogue", text=content, speaker_name=speaker)
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
            await _tts_to_wav_file(
                text=seg.text, voice_config=voice_config, out_path=local_tts
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
