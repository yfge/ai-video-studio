"""
Seed normalized `scenes` rows from existing `Script.scenes` JSON for a given script.

Usage examples:
  python ai-pic-backend/scripts/seed_normalized_scenes.py --script-id 123
  python ai-pic-backend/scripts/seed_normalized_scenes.py --script-id 123 --dry-run

Notes:
- Requires Alembic migration `a1b2c3d4e5f6_add_story_structure_tables.py` applied.
- Non-destructive: only inserts missing scene rows for the target script_id.
"""
from __future__ import annotations

import argparse
import logging
from typing import Any, List

from app.core.database import SessionLocal
from app.models.script import Script
from app.models.story_structure import Scene


logger = logging.getLogger("seed_normalized_scenes")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def to_slug_line(item: dict[str, Any]) -> str:
    time = (item.get("time") or "").upper()
    location = item.get("location") or "UNKNOWN"
    segs = [s for s in [time, location] if s]
    return " ".join(segs) or "SCENE"


def to_scene_number_str(idx: int, item: dict[str, Any]) -> str:
    num = item.get("scene_number")
    if isinstance(num, int) and num > 0:
        return str(num)
    try:
        # tolerate numeric strings
        if isinstance(num, str) and num.strip():
            n = int(num)
            if n > 0:
                return str(n)
    except Exception:
        pass
    return str(idx + 1)


def seed_for_script(script_id: int, *, dry_run: bool = False) -> int:
    db = SessionLocal()
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            logger.error("Script %s not found", script_id)
            return 0
        source_scenes: List[dict[str, Any]] = list(script.scenes or [])  # type: ignore
        if not source_scenes:
            logger.info("Script %s has no JSON scenes; nothing to seed.", script_id)
            return 0

        existing = (
            db.query(Scene).filter(Scene.script_id == script_id).all()
        )
        existing_keys = {(s.scene_number) for s in existing}

        to_insert: List[Scene] = []
        for idx, item in enumerate(source_scenes):
            scene_number_str = to_scene_number_str(idx, item)
            if scene_number_str in existing_keys:
                continue
            sc = Scene(
                script_id=script_id,
                scene_number=scene_number_str,
                slug_line=to_slug_line(item),
                environment_type=None,
                location=item.get("location"),
                time_of_day=item.get("time"),
                summary=item.get("description"),
                page_length_eighths=None,
                primary_characters=None,
                conflict_notes=None,
                ai_prompt_snapshot=None,
                status="draft",
                extra_metadata=None,
            )
            to_insert.append(sc)

        if not to_insert:
            logger.info("All scenes already present for script %s; nothing new to insert.", script_id)
            return 0

        logger.info("Prepared %d new scenes for script %s", len(to_insert), script_id)
        if dry_run:
            logger.info("Dry-run enabled; not inserting.")
            return len(to_insert)

        db.add_all(to_insert)
        db.commit()
        logger.info("Inserted %d scenes.", len(to_insert))
        return len(to_insert)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed normalized scenes from Script.scenes JSON")
    parser.add_argument("--script-id", type=int, required=True, help="Target script id")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    args = parser.parse_args()

    count = seed_for_script(args.script_id, dry_run=args.dry_run)
    logger.info("Done. Prepared/Inserted %d scenes.", count)


if __name__ == "__main__":
    main()

