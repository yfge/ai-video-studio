"""
Prototype extractor for normalising Story → Episode → Script payloads into the
planned relational schema (`story_treatments`, `story_step_outlines`, `scenes`,
`scene_beats`, `shots`).

Two operation modes are supported:
1. Sample mode (default): uses in-memory fixtures that reflect current JSON structure.
2. Live mode (`--mode live --script-id <id>`): pulls an actual script + related story
   hierarchy from the configured database, performs extraction, and (optionally)
   exercises insert statements inside a rollback-only transaction to validate the
   upcoming tables.

Usage examples:
  # Existing behaviour – emit JSON for sample payloads
  python ai-pic-backend/scripts/prototype_story_structure_migration.py --dump-json

  # Inspect real script 42 and run insert probe (rolled back automatically)
  python ai-pic-backend/scripts/prototype_story_structure_migration.py \
      --mode live --script-id 42 --insert-probe
"""

from __future__ import annotations

import argparse
import json
import logging
from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.script import Episode, Script, Story

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Data classes representing normalized rows
# ---------------------------------------------------------------------------
@dataclass
class StoryTreatmentRow:
    story_id: int
    revision_number: int
    status: str
    title: str
    logline: Optional[str]
    theme_summary: Optional[str]
    act_structure: Optional[Dict[str, Any]]
    target_audience_notes: Optional[str]
    tone_reference: Optional[Dict[str, Any]]
    created_by: Optional[int]
    approved_by: Optional[int]
    ai_prompt_snapshot: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class StepOutlineRow:
    story_id: int
    episode_id: Optional[int]
    story_treatment_id: int  # placeholder, replaced during insert
    sequence_number: int
    act_label: Optional[str]
    beat_title: str
    beat_summary: Optional[str]
    dramatic_question: Optional[str]
    characters_involved: Optional[List[Any]]
    location_hint: Optional[str]
    duration_estimate_minutes: Optional[float]
    status: str
    metadata: Dict[str, Any]


@dataclass
class SceneRow:
    script_id: int
    story_step_outline_id: Optional[int]  # placeholder prototype id
    scene_number: str
    slug_line: str
    environment_type: Optional[str]
    location: Optional[str]
    time_of_day: Optional[str]
    summary: Optional[str]
    page_length_eighths: Optional[int]
    primary_characters: Optional[List[Any]]
    conflict_notes: Optional[str]
    ai_prompt_snapshot: Optional[Dict[str, Any]]
    status: str
    metadata: Dict[str, Any]


@dataclass
class SceneBeatRow:
    scene_id: int  # placeholder prototype id
    order_index: int
    beat_type: Optional[str]
    beat_summary: Optional[str]
    characters_involved: Optional[List[Any]]
    dialogue_excerpt: Optional[str]
    camera_notes: Optional[str]
    duration_seconds: Optional[float]
    metadata: Dict[str, Any]


@dataclass
class ShotRow:
    scene_id: int  # placeholder prototype id
    scene_beat_id: Optional[int]  # placeholder prototype id
    shot_number: str
    shot_type: Optional[str]
    camera_setup: Optional[str]
    camera_movement: Optional[str]
    framing: Optional[str]
    focus_subject: Optional[str]
    duration_seconds: Optional[float]
    storyboard_frame_asset_id: Optional[int]
    lighting_notes: Optional[str]
    audio_notes: Optional[str]
    status: str
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Sample payload representative of current JSON structure
# ---------------------------------------------------------------------------
SAMPLE_STORY: Dict[str, Any] = {
    "id": 101,
    "title": "城市奇遇记",
    "genre": "都市",
    "theme": "人与人的信任",
    "target_audience": "都市白领",
    "world_building": "现代城市，夜幕霓虹",
    "premise": "小李偶遇神秘女子，卷入连续误会。",
    "synopsis": "误会引发冒险，最终互相信任。",
}

SAMPLE_EPISODE: Dict[str, Any] = {
    "id": 501,
    "story_id": 101,
    "episode_number": 1,
    "title": "初遇",
    "summary": "主角在夜市偶遇神秘女子，卷入误会",
    "duration_minutes": 15,
    "scene_count": 3,
    "plot_points": [
        {
            "order": 1,
            "title": "夜市偶遇",
            "summary": "小李在夜市邂逅神秘女子。",
            "act": "ACT I",
            "characters": ["小李", "神秘女子"],
            "location": "夜市主街",
            "duration_minutes": 3.5,
        },
        {
            "order": 2,
            "title": "跟踪误会",
            "summary": "小李跟随女子导致误会升级。",
            "act": "ACT II",
            "characters": ["小李", "神秘女子"],
            "location": "夜市后巷",
            "duration_minutes": 4.0,
        },
        {
            "order": 3,
            "title": "雨夜对峙",
            "summary": "雨夜对峙揭示误会缘由。",
            "act": "ACT II",
            "characters": ["小李", "神秘女子", "巡警"],
            "location": "城市天台",
            "duration_minutes": 7.5,
        },
    ],
}

SAMPLE_SCRIPT: Dict[str, Any] = {
    "id": 3001,
    "episode_id": 501,
    "title": "初遇 - 剧本草稿",
    "content": "小李穿梭在夜市的人群中，四处张望……",
    "scenes": [
        {
            "scene_number": "1",
            "environment": "EXT",
            "location": "夜市主街",
            "time": "夜",
            "description": "小李在夜市摊位挑选饰品，灯光昏黄。",
            "characters": ["小李", "摊主阿姨"],
            "summary": "小李寻找礼物。",
            "beats": [
                {
                    "type": "action",
                    "summary": "小李给女友挑选项链。",
                    "characters": ["小李"],
                    "duration_seconds": 20,
                },
                {
                    "type": "dialogue",
                    "summary": "摊主推销饰品。",
                    "characters": ["小李", "摊主阿姨"],
                    "dialogue_excerpt": "摊主：这款最适合送女朋友。",
                },
            ],
        },
        {
            "scene_number": "2",
            "environment": "EXT",
            "location": "夜市后巷",
            "time": "雨后夜晚",
            "description": "神秘女子在小巷回头，雨后的路面倒映霓虹。",
            "characters": ["神秘女子"],
            "summary": "神秘女子察觉被跟踪。",
            "beats": [
                {
                    "type": "action",
                    "summary": "女子加快脚步。",
                    "duration_seconds": 12,
                },
                {
                    "type": "dialogue",
                    "summary": "女子警告小李不要跟踪。",
                    "dialogue_excerpt": "神秘女子：别跟着我。",
                },
            ],
        },
        {
            "scene_number": "3",
            "environment": "INT",
            "location": "城市天台",
            "time": "深夜",
            "description": "雨继续落下，警灯闪烁。",
            "characters": ["小李", "神秘女子", "巡警"],
            "summary": "巡警介入化解误会。",
            "beats": [
                {
                    "type": "action",
                    "summary": "巡警质问小李。",
                    "characters": ["巡警", "小李"],
                },
                {
                    "type": "dialogue",
                    "summary": "误会化解。",
                    "characters": ["小李", "神秘女子"],
                    "dialogue_excerpt": "小李：我只是想还你东西。",
                },
            ],
        },
    ],
    "storyboard_plan": [
        {
            "scene_number": 1,
            "shot_number": "1A",
            "shot_type": "WS",
            "camera_movement": "pan",
            "framing": "小李与摊位全景",
            "focus_subject": "小李",
            "duration_seconds": 4.8,
            "lighting_notes": "暖色灯串",
        },
        {
            "scene_number": 2,
            "shot_number": "2A",
            "shot_type": "CU",
            "camera_movement": "handheld",
            "framing": "女子回头特写",
            "focus_subject": "神秘女子",
            "duration_seconds": 3.2,
        },
        {
            "scene_number": 3,
            "shot_number": "3B",
            "shot_type": "MS",
            "camera_movement": "static",
            "framing": "巡警与小李中景",
            "focus_subject": "巡警",
            "duration_seconds": 5.0,
            "audio_notes": "雨声 + 远处警笛",
        },
    ],
}


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------
def build_slug_line(payload: Dict[str, Any]) -> str:
    env = payload.get("environment") or payload.get("env") or "INT"
    location = payload.get("location") or payload.get("place") or "UNKNOWN LOCATION"
    time_of_day = payload.get("time") or payload.get("time_of_day") or "UNKNOWN TIME"
    return f"{env}. {location} - {time_of_day}"


def extract_story_treatment(story: Dict[str, Any]) -> StoryTreatmentRow:
    prototype_id = 1  # single treatment per story for prototype
    metadata = {
        "source": "story",
        "prototype_treatment_id": prototype_id,
        "extracted_fields": ["premise", "synopsis", "theme"],
    }
    return StoryTreatmentRow(
        story_id=story["id"],
        revision_number=1,
        status="draft",
        title=f"{story.get('title', 'Story')} Treatment v1",
        logline=story.get("premise"),
        theme_summary=story.get("theme"),
        act_structure={
            "premise": story.get("premise"),
            "synopsis": story.get("synopsis"),
        },
        target_audience_notes=story.get("target_audience"),
        tone_reference=None,
        created_by=None,
        approved_by=None,
        ai_prompt_snapshot=None,
        metadata=metadata,
    )


def extract_step_outlines(
    treatment_key: Tuple[int, int], story: Dict[str, Any], episode: Dict[str, Any]
) -> Tuple[List[StepOutlineRow], Dict[str, int]]:
    outlines: List[StepOutlineRow] = []
    outline_lookup: Dict[str, int] = {}
    beats = episode.get("plot_points") or []
    for idx, beat in enumerate(beats, start=1):
        proto_outline_id = idx
        scene_ref = beat.get("scene_number") or beat.get("scene") or beat.get("order") or proto_outline_id
        outline_lookup[str(scene_ref)] = proto_outline_id
        metadata = {
            "source": "episode.plot_points",
            "prototype_outline_id": proto_outline_id,
            "treatment_key": list(treatment_key),
            "original_scene_reference": scene_ref,
        }
        outlines.append(
            StepOutlineRow(
                story_id=story["id"],
                episode_id=episode.get("id"),
                story_treatment_id=proto_outline_id,  # placeholder, swapped during insert
                sequence_number=beat.get("order") or idx,
                act_label=beat.get("act"),
                beat_title=beat.get("title") or f"Beat {idx}",
                beat_summary=beat.get("summary"),
                dramatic_question=beat.get("dramatic_question"),
                characters_involved=beat.get("characters"),
                location_hint=beat.get("location"),
                duration_estimate_minutes=beat.get("duration_minutes"),
                status="draft",
                metadata=metadata,
            )
        )
    return outlines, outline_lookup


def extract_scenes(
    script: Dict[str, Any],
    outline_lookup: Dict[str, int],
) -> Tuple[List[SceneRow], Dict[str, int]]:
    scene_rows: List[SceneRow] = []
    scene_id_lookup: Dict[str, int] = {}
    for idx, raw_scene in enumerate(script.get("scenes") or [], start=1):
        scene_number = str(raw_scene.get("scene_number") or idx)
        outline_proto = outline_lookup.get(scene_number)
        proto_scene_id = idx
        scene_id_lookup[scene_number] = proto_scene_id
        metadata = {
            "source": "script.scenes",
            "prototype_scene_id": proto_scene_id,
            "outline_proto_id": outline_proto,
            "raw": deepcopy(raw_scene),
        }
        scene_rows.append(
            SceneRow(
                script_id=script["id"],
                story_step_outline_id=outline_proto,
                scene_number=scene_number,
                slug_line=build_slug_line(raw_scene),
                environment_type=raw_scene.get("environment"),
                location=raw_scene.get("location"),
                time_of_day=raw_scene.get("time"),
                summary=raw_scene.get("summary") or raw_scene.get("description"),
                page_length_eighths=None,
                primary_characters=raw_scene.get("characters"),
                conflict_notes=raw_scene.get("conflict"),
                ai_prompt_snapshot=None,
                status="draft",
                metadata=metadata,
            )
        )
    return scene_rows, scene_id_lookup


def extract_scene_beats(
    script: Dict[str, Any],
    scene_id_lookup: Dict[str, int],
) -> Tuple[List[SceneBeatRow], Dict[Tuple[str, int], int]]:
    beats: List[SceneBeatRow] = []
    beat_lookup: Dict[Tuple[str, int], int] = {}
    for scene_payload in script.get("scenes") or []:
        scene_number = str(scene_payload.get("scene_number") or "")
        scene_proto_id = scene_id_lookup.get(scene_number)
        if not scene_proto_id:
            continue
        for order_index, beat in enumerate(scene_payload.get("beats") or [], start=1):
            proto_beat_id = len(beats) + 1
            beat_lookup[(scene_number, order_index)] = proto_beat_id
            metadata = {
                "source": "scene.beats",
                "scene_number": scene_number,
                "prototype_scene_id": scene_proto_id,
                "prototype_beat_id": proto_beat_id,
            }
            beats.append(
                SceneBeatRow(
                    scene_id=scene_proto_id,
                    order_index=order_index,
                    beat_type=beat.get("type"),
                    beat_summary=beat.get("summary"),
                    characters_involved=beat.get("characters"),
                    dialogue_excerpt=beat.get("dialogue_excerpt"),
                    camera_notes=beat.get("camera_notes"),
                    duration_seconds=beat.get("duration_seconds"),
                    metadata=metadata,
                )
            )
    return beats, beat_lookup


def extract_shots(
    script: Dict[str, Any],
    scene_id_lookup: Dict[str, int],
    beat_lookup: Dict[Tuple[str, int], int],
) -> List[ShotRow]:
    shots: List[ShotRow] = []
    for entry in script.get("storyboard_plan") or []:
        scene_number = str(entry.get("scene_number"))
        scene_proto_id = scene_id_lookup.get(scene_number)
        if not scene_proto_id:
            continue
        beat_order = (
            entry.get("beat_index")
            or entry.get("beat_order")
            or entry.get("beat_number")
            or entry.get("scene_beat_order")
            or 1
        )
        proto_beat_id = beat_lookup.get((scene_number, int(beat_order)))
        metadata = {
            "source": "script.storyboard_plan",
            "prototype_scene_id": scene_proto_id,
            "prototype_beat_id": proto_beat_id,
            "raw": deepcopy(entry),
        }
        shots.append(
            ShotRow(
                scene_id=scene_proto_id,
                scene_beat_id=proto_beat_id,
                shot_number=str(entry.get("shot_number") or f"{scene_number}X"),
                shot_type=entry.get("shot_type"),
                camera_setup=entry.get("camera_setup"),
                camera_movement=entry.get("camera_movement"),
                framing=entry.get("framing"),
                focus_subject=entry.get("focus_subject"),
                duration_seconds=entry.get("duration_seconds"),
                storyboard_frame_asset_id=None,
                lighting_notes=entry.get("lighting_notes"),
                audio_notes=entry.get("audio_notes"),
                status="planned",
                metadata=metadata,
            )
        )
    return shots


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def _engine_config_for_url(url: str) -> Dict[str, Any]:
    url_lower = url.lower()
    if "sqlite" in url_lower:
        return {"connect_args": {"check_same_thread": False}}
    if "mysql" in url_lower:
        return {
            "pool_size": 20,
            "max_overflow": 0,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "connect_args": {"charset": "utf8mb4", "autocommit": False},
        }
    return {}


def build_engine(dsn: Optional[str] = None) -> Engine:
    url = dsn or settings.DATABASE_URL
    config = _engine_config_for_url(url)
    engine = create_engine(url, **config)
    return engine


def load_live_payloads(session: Session, script_id: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    script: Script | None = session.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise ValueError(f"Script {script_id} not found")
    episode: Episode | None = script.episode
    if not episode:
        raise ValueError(f"Script {script_id} missing episode reference")
    story: Story | None = episode.story
    if not story:
        raise ValueError(f"Episode {episode.id} missing story reference")

    story_payload = {
        "id": story.id,
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "target_audience": story.target_audience,
        "world_building": story.world_building,
        "premise": story.premise,
        "synopsis": story.synopsis,
    }

    episode_payload = {
        "id": episode.id,
        "story_id": episode.story_id,
        "episode_number": episode.episode_number,
        "title": episode.title,
        "summary": episode.summary,
        "duration_minutes": episode.duration_minutes,
        "scene_count": episode.scene_count,
        "plot_points": episode.plot_points or [],
    }

    script_payload = {
        "id": script.id,
        "episode_id": script.episode_id,
        "title": script.title,
        "content": script.content,
        "scenes": script.scenes or [],
        "dialogues": script.dialogues or [],
        "stage_directions": script.stage_directions or [],
        "storyboard_plan": script.storyboard_plan or [],
    }
    return story_payload, episode_payload, script_payload


def assemble_payload(story: Dict[str, Any], episode: Dict[str, Any], script: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    treatment = extract_story_treatment(story)
    treatment_key = (treatment.story_id, treatment.revision_number)

    step_outlines, outline_lookup = extract_step_outlines(treatment_key, story, episode)
    scenes, scene_lookup = extract_scenes(script, outline_lookup)
    scene_beats, beat_lookup = extract_scene_beats(script, scene_lookup)
    shots = extract_shots(script, scene_lookup, beat_lookup)

    payload = {
        "story_treatments": [asdict(treatment)],
        "story_step_outlines": [asdict(row) for row in step_outlines],
        "scenes": [asdict(row) for row in scenes],
        "scene_beats": [asdict(row) for row in scene_beats],
        "shots": [asdict(row) for row in shots],
    }
    return payload


def probe_insert(engine: Engine, payload: Dict[str, List[Dict[str, Any]]]) -> None:
    inspector = sa.inspect(engine)
    required_tables = [
        "story_treatments",
        "story_step_outlines",
        "scenes",
        "scene_beats",
        "shots",
    ]
    missing = [table for table in required_tables if not inspector.has_table(table)]
    if missing:
        logger.warning("Insert probe skipped: tables missing %s", missing)
        return

    metadata = sa.MetaData()
    tables = {
        name: sa.Table(name, metadata, autoload_with=engine)
        for name in required_tables
    }

    connection = engine.connect()
    transaction = connection.begin()
    try:
        treatment_id_map: Dict[Tuple[int, int], int] = {}
        for row in payload.get("story_treatments", []):
            insert_data = dict(row)
            metadata_blob = insert_data.get("metadata") or {}
            metadata_blob.setdefault("probe", True)
            insert_data["metadata"] = metadata_blob
            result = connection.execute(tables["story_treatments"].insert().values(**insert_data))
            inserted_id = result.inserted_primary_key[0]
            treatment_id_map[(insert_data["story_id"], insert_data["revision_number"])] = inserted_id
        logger.info("Inserted %d story_treatments (rolled back later)", len(treatment_id_map))

        outline_id_map: Dict[int, int] = {}
        for row in payload.get("story_step_outlines", []):
            insert_data = dict(row)
            metadata_blob = insert_data.get("metadata") or {}
            treatment_key_raw = metadata_blob.get("treatment_key")
            treatment_key = None
            if isinstance(treatment_key_raw, list) and len(treatment_key_raw) == 2:
                treatment_key = (int(treatment_key_raw[0]), int(treatment_key_raw[1]))
            else:
                treatment_key = (insert_data["story_id"], 1)
            treatment_fk = treatment_id_map.get(treatment_key)
            if treatment_fk is None:
                logger.warning("Skipping step outline; no treatment found for key %s", treatment_key)
                continue
            insert_data["story_treatment_id"] = treatment_fk
            result = connection.execute(tables["story_step_outlines"].insert().values(**insert_data))
            inserted_id = result.inserted_primary_key[0]
            proto_id = metadata_blob.get("prototype_outline_id")
            if proto_id is not None:
                outline_id_map[int(proto_id)] = inserted_id
        logger.info("Inserted %d story_step_outlines", len(outline_id_map))

        scene_id_map: Dict[int, int] = {}
        for row in payload.get("scenes", []):
            insert_data = dict(row)
            metadata_blob = insert_data.get("metadata") or {}
            outline_proto = metadata_blob.get("outline_proto_id")
            if outline_proto:
                insert_data["story_step_outline_id"] = outline_id_map.get(int(outline_proto))
            else:
                insert_data["story_step_outline_id"] = None
            proto_scene_id = metadata_blob.get("prototype_scene_id")
            if proto_scene_id is None:
                logger.warning("Skipping scene without prototype id metadata")
                continue
            result = connection.execute(tables["scenes"].insert().values(**insert_data))
            inserted_id = result.inserted_primary_key[0]
            scene_id_map[int(proto_scene_id)] = inserted_id
        logger.info("Inserted %d scenes", len(scene_id_map))

        beat_id_map: Dict[int, int] = {}
        for row in payload.get("scene_beats", []):
            insert_data = dict(row)
            metadata_blob = insert_data.get("metadata") or {}
            scene_proto = metadata_blob.get("prototype_scene_id")
            if scene_proto is None:
                logger.warning("Skipping beat without scene prototype id")
                continue
            real_scene_id = scene_id_map.get(int(scene_proto))
            if real_scene_id is None:
                logger.warning("Skipping beat; scene %s not inserted", scene_proto)
                continue
            insert_data["scene_id"] = real_scene_id
            result = connection.execute(tables["scene_beats"].insert().values(**insert_data))
            inserted_id = result.inserted_primary_key[0]
            proto_beat_id = metadata_blob.get("prototype_beat_id")
            if proto_beat_id is not None:
                beat_id_map[int(proto_beat_id)] = inserted_id
        logger.info("Inserted %d scene_beats", len(beat_id_map))

        shot_count = 0
        for row in payload.get("shots", []):
            insert_data = dict(row)
            metadata_blob = insert_data.get("metadata") or {}
            scene_proto = metadata_blob.get("prototype_scene_id")
            if scene_proto is None:
                logger.warning("Skipping shot without scene prototype id")
                continue
            real_scene_id = scene_id_map.get(int(scene_proto))
            if real_scene_id is None:
                logger.warning("Skipping shot; scene %s not inserted", scene_proto)
                continue
            insert_data["scene_id"] = real_scene_id
            beat_proto = metadata_blob.get("prototype_beat_id")
            if beat_proto:
                insert_data["scene_beat_id"] = beat_id_map.get(int(beat_proto))
            else:
                insert_data["scene_beat_id"] = None
            connection.execute(tables["shots"].insert().values(**insert_data))
            shot_count += 1
        logger.info("Inserted %d shots", shot_count)

        transaction.rollback()
        logger.info("Insert probe completed; transaction rolled back successfully.")
    except Exception as exc:  # pragma: no cover - diagnostic path
        transaction.rollback()
        logger.error("Insert probe failed: %s", exc)
        raise
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# CLI orchestration
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prototype story structure extractor")
    parser.add_argument(
        "--mode",
        choices=["sample", "live"],
        default="sample",
        help="Extraction source: sample fixture (default) or live database records.",
    )
    parser.add_argument("--script-id", type=int, help="Script ID to extract when running in live mode.")
    parser.add_argument("--dsn", type=str, help="Override DATABASE_URL for live mode connections.")
    parser.add_argument("--dump-json", action="store_true", help="Emit extracted payload as JSON.")
    parser.add_argument("--insert-probe", action="store_true", help="Attempt insert + rollback against live database.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.mode == "live":
        if not args.script_id:
            raise SystemExit("Live mode requires --script-id")
        engine = build_engine(args.dsn)
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            story, episode, script = load_live_payloads(session, args.script_id)
        payload = assemble_payload(story, episode, script)
        if args.insert_probe:
            probe_insert(engine, payload)
        engine.dispose()
    else:
        payload = assemble_payload(SAMPLE_STORY, SAMPLE_EPISODE, SAMPLE_SCRIPT)

    logger.info(
        "Extraction ready: %d treatments, %d outlines, %d scenes, %d beats, %d shots",
        len(payload["story_treatments"]),
        len(payload["story_step_outlines"]),
        len(payload["scenes"]),
        len(payload["scene_beats"]),
        len(payload["shots"]),
    )

    if args.dump_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
