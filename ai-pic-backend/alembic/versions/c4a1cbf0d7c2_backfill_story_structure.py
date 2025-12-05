"""Backfill story structure tables from script JSON."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.script import Script, Episode, Story

ROOT = Path(__file__).resolve().parents[2]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prototype_story_structure_migration import assemble_payload, load_live_payloads  # noqa: E402

# revision identifiers, used by Alembic.
revision = "c4a1cbf0d7c2"
down_revision = "7f3d2a1b9c00"
branch_labels = None
depends_on = None


REQUIRED_TABLES = [
    "story_treatments",
    "story_step_outlines",
    "scenes",
    "scene_beats",
    "shots",
    "scripts",
]


def _tables_available(connection) -> bool:
    inspector = sa.inspect(connection)
    return all(inspector.has_table(name) for name in REQUIRED_TABLES)


def _has_normalized_rows(connection, script_id: int) -> bool:
    scenes = sa.table("scenes", sa.column("script_id"))
    count = connection.execute(
        sa.select(sa.func.count()).select_from(scenes).where(scenes.c.script_id == script_id)
    ).scalar()
    return bool(count and count > 0)


def _materialize_payload(connection, payload: Dict[str, List[Dict[str, object]]]) -> None:
    metadata = sa.MetaData()
    tables = {name: sa.Table(name, metadata, autoload_with=connection) for name in REQUIRED_TABLES if name != "scripts"}

    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
    migration_marker = {"migration_revision": revision, "migration_source": "alembic_backfill"}

    treatment_id_map: Dict[Tuple[int, int], int] = {}
    for row in payload.get("story_treatments", []):
        insert_data = dict(row)
        meta_blob = insert_data.get("metadata") or {}
        meta_blob.update(migration_marker)
        insert_data["metadata"] = meta_blob
        insert_data.setdefault("is_deleted", False)
        insert_data.setdefault("created_at", timestamp)
        insert_data.setdefault("updated_at", timestamp)
        result = connection.execute(tables["story_treatments"].insert().values(**insert_data))
        inserted_id = result.inserted_primary_key[0]
        treatment_id_map[(insert_data["story_id"], insert_data["revision_number"])] = inserted_id

    outline_id_map: Dict[int, int] = {}
    for row in payload.get("story_step_outlines", []):
        insert_data = dict(row)
        meta_blob = insert_data.get("metadata") or {}
        meta_blob.update(migration_marker)
        insert_data["metadata"] = meta_blob
        treatment_key_raw = meta_blob.get("treatment_key")
        if isinstance(treatment_key_raw, list) and len(treatment_key_raw) == 2:
            treatment_key = (int(treatment_key_raw[0]), int(treatment_key_raw[1]))
        else:
            treatment_key = (insert_data["story_id"], 1)
        insert_data["story_treatment_id"] = treatment_id_map.get(treatment_key)
        insert_data.setdefault("created_at", timestamp)
        insert_data.setdefault("updated_at", timestamp)
        result = connection.execute(tables["story_step_outlines"].insert().values(**insert_data))
        inserted_id = result.inserted_primary_key[0]
        proto_id = meta_blob.get("prototype_outline_id")
        if proto_id is not None:
            outline_id_map[int(proto_id)] = inserted_id

    scene_id_map: Dict[int, int] = {}
    for row in payload.get("scenes", []):
        insert_data = dict(row)
        meta_blob = insert_data.get("metadata") or {}
        meta_blob.update(migration_marker)
        insert_data["metadata"] = meta_blob
        outline_proto = meta_blob.get("outline_proto_id")
        if outline_proto:
            insert_data["story_step_outline_id"] = outline_id_map.get(int(outline_proto))
        insert_data.setdefault("created_at", timestamp)
        insert_data.setdefault("updated_at", timestamp)
        result = connection.execute(tables["scenes"].insert().values(**insert_data))
        inserted_id = result.inserted_primary_key[0]
        proto_scene_id = meta_blob.get("prototype_scene_id")
        if proto_scene_id is not None:
            scene_id_map[int(proto_scene_id)] = inserted_id

    beat_id_map: Dict[int, int] = {}
    for row in payload.get("scene_beats", []):
        insert_data = dict(row)
        meta_blob = insert_data.get("metadata") or {}
        meta_blob.update(migration_marker)
        insert_data["metadata"] = meta_blob
        proto_scene_id = meta_blob.get("prototype_scene_id")
        if proto_scene_id is None:
            continue
        scene_fk = scene_id_map.get(int(proto_scene_id))
        if scene_fk is None:
            continue
        insert_data["scene_id"] = scene_fk
        insert_data.setdefault("created_at", timestamp)
        insert_data.setdefault("updated_at", timestamp)
        result = connection.execute(tables["scene_beats"].insert().values(**insert_data))
        inserted_id = result.inserted_primary_key[0]
        proto_beat_id = meta_blob.get("prototype_beat_id")
        if proto_beat_id is not None:
            beat_id_map[int(proto_beat_id)] = inserted_id

    for row in payload.get("shots", []):
        insert_data = dict(row)
        meta_blob = insert_data.get("metadata") or {}
        meta_blob.update(migration_marker)
        insert_data["metadata"] = meta_blob
        proto_scene_id = meta_blob.get("prototype_scene_id")
        scene_fk = scene_id_map.get(int(proto_scene_id)) if proto_scene_id is not None else None
        if scene_fk is None:
            continue
        insert_data["scene_id"] = scene_fk
        proto_beat_id = meta_blob.get("prototype_beat_id")
        insert_data["scene_beat_id"] = beat_id_map.get(int(proto_beat_id)) if proto_beat_id else None
        insert_data.setdefault("created_at", timestamp)
        insert_data.setdefault("updated_at", timestamp)
        connection.execute(tables["shots"].insert().values(**insert_data))


def upgrade() -> None:
    bind = op.get_bind()
    if not _tables_available(bind):
        return

    session = Session(bind=bind)
    try:
        scripts: List[Script] = session.query(Script).all()
        for script in scripts:
            if _has_normalized_rows(bind, script.id):
                continue
            story_payload, episode_payload, script_payload = load_live_payloads(session, script.id)
            payload, _warnings = assemble_payload(story_payload, episode_payload, script_payload)
            _materialize_payload(bind, payload)
    finally:
        session.close()


def downgrade() -> None:
    bind = op.get_bind()
    if not _tables_available(bind):
        return

    metadata = sa.MetaData()
    tables = {name: sa.Table(name, metadata, autoload_with=bind) for name in REQUIRED_TABLES if name != "scripts"}

    def _delete(name: str, where_clause):
        bind.execute(tables[name].delete().where(where_clause))

    marker_expr = lambda table: table.c.metadata["migration_revision"].as_string() == revision  # type: ignore

    _delete("shots", marker_expr(tables["shots"]))
    _delete("scene_beats", marker_expr(tables["scene_beats"]))
    _delete("scenes", marker_expr(tables["scenes"]))
    _delete("story_step_outlines", marker_expr(tables["story_step_outlines"]))
    _delete("story_treatments", marker_expr(tables["story_treatments"]))
