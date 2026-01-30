from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

SHOT_CYCLE = ["远景", "中景", "近景", "特写"]
MOVEMENT_CYCLE = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
COMPOSITION_CYCLE = ["三分法", "对称", "前后景", "对角线", "中心对称"]


def cycle_value(cycle: List[str], position: int) -> str:
    if not cycle:
        return ""
    return cycle[position % len(cycle)]


def sanitize_outline(
    scene_number: int | None, index: int, outline: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    changed = False
    shot = outline.get("shot_type")
    movement = outline.get("camera_movement")
    composition = outline.get("composition")
    if not shot:
        shot = cycle_value(SHOT_CYCLE, index + (scene_number or 0))
        outline["shot_type"] = shot
        changed = True
    if not movement:
        movement = cycle_value(MOVEMENT_CYCLE, index)
        outline["camera_movement"] = movement
        changed = True
    if not composition:
        composition = cycle_value(COMPOSITION_CYCLE, index)
        outline["composition"] = composition
        changed = True
    if not outline.get("intent"):
        outline["intent"] = f"强调{movement}镜头表现" if movement else "突出叙事节奏"
        changed = True
    return outline, changed


def normalize_plan_outlines(plan: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    fixes: List[str] = []
    for scene in plan.get("scenes", []):
        outlines = scene.get("frames") or []
        combos = set()
        scene_no = scene.get("scene_number")
        for idx, frame in enumerate(outlines):
            frame, changed = sanitize_outline(scene_no, idx, frame)
            key = (
                frame.get("shot_type"),
                frame.get("camera_movement"),
                frame.get("intent"),
            )
            if key in combos:
                shot = cycle_value(SHOT_CYCLE, idx + 1)
                move = cycle_value(MOVEMENT_CYCLE, idx + 2)
                comp = cycle_value(COMPOSITION_CYCLE, idx + 3)
                frame["shot_type"] = shot
                frame["camera_movement"] = move
                frame["composition"] = comp
                frame["intent"] = frame.get("intent") or f"镜头强调{move}"
                combos.add((shot, move, frame["intent"]))
                fixes.append(f"scene {scene_no} frame {idx} varied")
                continue
            combos.add(key)
            if changed:
                fixes.append(f"scene {scene_no} frame {idx} normalized")
    return plan, fixes


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def count_frames_by_scene(frames: Iterable[Dict[str, Any]]) -> Dict[int, int]:
    counts: Dict[int, int] = {}
    for frame in frames:
        scene_no = _maybe_int(frame.get("scene_number"))
        if scene_no is None:
            continue
        counts[scene_no] = counts.get(scene_no, 0) + 1
    return counts


def find_scene_deficits(
    plan: Dict[str, Any],
    frames: Iterable[Dict[str, Any]],
    default_target: int,
) -> Dict[int, int]:
    counts = count_frames_by_scene(frames)
    deficits: Dict[int, int] = {}
    for scene in plan.get("scenes", []):
        scene_no = _maybe_int(scene.get("scene_number"))
        if scene_no is None:
            continue
        target = scene.get("target_frames") or default_target
        try:
            target_int = int(target)
        except (TypeError, ValueError):
            target_int = default_target
        existing = counts.get(scene_no, 0)
        if existing < target_int:
            deficits[scene_no] = target_int - existing
    return deficits
