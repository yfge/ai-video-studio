from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from app.core.logging import get_logger
from app.models.episode_character import EpisodeCharacter
from app.models.script import Episode, Story, StoryCharacter
from app.models.story_structure import Scene
from app.models.virtual_ip import VirtualIP
from app.services.ai_service import ai_service
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG
from app.utils.json_utils import extract_json_block
from sqlalchemy.orm import Session

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _norm_name(name: str) -> str:
    return "".join((name or "").strip().lower().split())


def _voice_candidates(limit: int = 40) -> list[dict[str, str]]:
    """Return a compact candidate list for agent selection."""
    zh = [v for v in SYSTEM_VOICE_CATALOG if (v.get("language") or "").startswith("zh")]
    # Heuristic buckets from voice_id naming conventions.
    buckets: list[list[dict[str, str]]] = [
        [v for v in zh if "female" in (v.get("voice_id") or "")],
        [v for v in zh if "male" in (v.get("voice_id") or "")],
        [
            v
            for v in zh
            if any(tok in (v.get("voice_id") or "") for tok in ["girl", "boy", "child"])
        ],
        zh,
    ]
    picked: list[dict[str, str]] = []
    seen: set[str] = set()
    for group in buckets:
        for item in group:
            voice_id = (item.get("voice_id") or "").strip()
            if not voice_id or voice_id in seen:
                continue
            seen.add(voice_id)
            picked.append(
                {
                    "voice_id": voice_id,
                    "voice_name": (item.get("voice_name") or "").strip(),
                    "language": (item.get("language") or "").strip(),
                }
            )
            if len(picked) >= limit:
                return picked
    return picked


def get_story_character_map(db: Session, story_id: int) -> dict[str, VirtualIP]:
    """Map normalized character_name -> VirtualIP for a story."""
    rows = db.query(StoryCharacter).filter(StoryCharacter.story_id == story_id).all()
    if not rows:
        return {}
    virtual_ip_ids = {row.virtual_ip_id for row in rows if row.virtual_ip_id}
    if not virtual_ip_ids:
        return {}
    ips = db.query(VirtualIP).filter(VirtualIP.id.in_(sorted(virtual_ip_ids))).all()
    ip_by_id = {ip.id: ip for ip in ips}
    mapping: dict[str, VirtualIP] = {}
    for row in rows:
        ip = ip_by_id.get(row.virtual_ip_id)
        if not ip:
            continue
        name = row.character_name or ip.name
        if not name:
            continue
        mapping[_norm_name(str(name))] = ip
    return mapping


def get_episode_character_map(db: Session, episode_id: int) -> dict[str, VirtualIP]:
    """
    Map normalized character_name -> VirtualIP for episode-level temporary characters.

    Returns: dict mapping normalized character names to VirtualIP objects
    """
    rows = (
        db.query(EpisodeCharacter)
        .filter(
            EpisodeCharacter.episode_id == episode_id,
            EpisodeCharacter.is_deleted == False,
        )
        .all()
    )
    if not rows:
        return {}

    virtual_ip_ids = {row.virtual_ip_id for row in rows if row.virtual_ip_id}
    if not virtual_ip_ids:
        return {}

    ips = db.query(VirtualIP).filter(VirtualIP.id.in_(sorted(virtual_ip_ids))).all()
    ip_by_id = {ip.id: ip for ip in ips}

    mapping: dict[str, VirtualIP] = {}
    for row in rows:
        ip = ip_by_id.get(row.virtual_ip_id)
        if not ip:
            continue

        # Priority: character_name > VirtualIP.name
        name = row.character_name or ip.name
        if not name:
            continue

        # Clone VirtualIP and apply overrides
        # Note: We need to handle voice_config_override
        effective_ip = ip
        if row.voice_config_override:
            # Create a shallow copy with overridden voice_config
            # This is a lightweight approach; for full isolation, consider a wrapper class
            effective_ip = type(ip)()
            for attr in dir(ip):
                if not attr.startswith("_") and not callable(getattr(ip, attr)):
                    setattr(effective_ip, attr, getattr(ip, attr))
            effective_ip.voice_config = row.voice_config_override

        mapping[_norm_name(str(name))] = effective_ip

    return mapping


def get_combined_character_map(
    db: Session, story_id: int, episode_id: int | None = None
) -> dict[str, VirtualIP]:
    """
    Merge Story and Episode character mappings with Episode priority.

    If a character name exists in both Story and Episode, Episode wins.

    Returns: dict mapping normalized character names to VirtualIP objects
    """
    # Start with Story characters
    mapping = get_story_character_map(db, story_id)

    # Overlay Episode characters (overwrite conflicts)
    if episode_id:
        episode_mapping = get_episode_character_map(db, episode_id)
        mapping.update(episode_mapping)

    return mapping


@dataclass(frozen=True)
class DerivedCharacterScopeDecision:
    scope: str  # "scene" | "episode" | "story"
    reason: str | None = None


async def _agent_choose_voice_id(
    *,
    character_name: str,
    character_description: str | None,
    candidates: list[dict[str, str]],
    model: str | None = None,
    prefer_provider: str | None = None,
) -> tuple[str | None, str | None, dict[str, Any]]:
    """
    Ask a text model to choose a minimax voice_id from candidates.

    Returns: (voice_id, reason, debug_meta)
    """
    if not ai_service.ai_manager or not hasattr(ai_service.ai_manager, "generate_text"):
        return None, None, {"error": "ai_manager_not_initialized"}

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "voice_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["voice_id"],
    }

    prompt = (
        "你是一个配音导演助手。请为给定角色从候选系统音色中选择最合适的 voice_id。\n"
        "要求：\n"
        "1) 只能从候选列表中选择 voice_id；\n"
        "2) 优先匹配角色气质/年龄/性别（若信息不足则选择更通用的成人音色）；\n"
        "3) 只返回严格 JSON。\n\n"
        f"角色名：{character_name}\n"
        f"角色描述：{character_description or ''}\n"
        f"候选音色（voice_id / voice_name）：\n"
        + "\n".join(f"- {c['voice_id']} / {c.get('voice_name','')}" for c in candidates)
    )
    resp = await ai_service.ai_manager.generate_text(
        prompt=prompt,
        model=model,
        prefer_provider=prefer_provider,
        temperature=0.0,
        stream=False,
        json_schema={"name": "voice_choice", "schema": schema},
        system_prompt="只返回严格 JSON，且 voice_id 必须来自候选列表。",
    )
    meta = {
        "provider": resp.provider,
        "model": resp.model,
        "usage": resp.usage,
        "raw": resp.data,
    }
    if not resp.success:
        return None, None, {**meta, "error": resp.error}

    parsed = extract_json_block(resp.data) if isinstance(resp.data, str) else None
    if not isinstance(parsed, dict):
        return None, None, {**meta, "error": "invalid_json"}

    voice_id = str(parsed.get("voice_id") or "").strip()
    reason = str(parsed.get("reason") or "").strip() or None
    allowed = {c["voice_id"] for c in candidates}
    if voice_id not in allowed:
        logger.info(
            "Agent chose voice_id not in candidates",
            extra={"character": character_name, "chosen": voice_id},
        )
        return (
            None,
            reason,
            {**meta, "error": "voice_id_not_in_candidates", "chosen": voice_id},
        )
    return voice_id, reason, meta


def _fallback_voice_id(candidates: Iterable[dict[str, str]]) -> str:
    # Prefer a stable, widely-available fallback.
    for item in candidates:
        vid = (item.get("voice_id") or "").strip()
        if vid:
            return vid
    return "Chinese (Mandarin)_Lyrical_Voice"


async def ensure_virtual_ip_voice_config(
    db: Session,
    virtual_ip: VirtualIP,
    *,
    selection_model: str | None = None,
    selection_prefer_provider: str | None = None,
    tts_provider: str = "minimax",
    tts_model: str = "speech-2.6-hd",
) -> dict[str, Any]:
    """
    Ensure VirtualIP.voice_config exists. If missing, run an agent to pick a system voice_id and persist it.

    Returns the (possibly newly-created) voice_config dict.
    """
    existing = (
        virtual_ip.voice_config if isinstance(virtual_ip.voice_config, dict) else None
    )
    if existing and (existing.get("voice_id") or existing.get("voice_type")):
        return existing

    candidates = _voice_candidates()
    voice_id, reason, agent_meta = await _agent_choose_voice_id(
        character_name=virtual_ip.name,
        character_description=(virtual_ip.description or "").strip() or None,
        candidates=candidates,
        model=selection_model,
        prefer_provider=selection_prefer_provider,
    )
    chosen = voice_id or _fallback_voice_id(candidates)
    if not voice_id:
        logger.info(
            "Voice binding fallback used for VirtualIP",
            extra={"virtual_ip_id": virtual_ip.id, "chosen": chosen},
        )

    voice_config: dict[str, Any] = {
        "provider": tts_provider,
        "tts_model": tts_model,
        "voice_id": chosen,
        "selected_at": _utc_now_iso(),
        "selected_by": "agent" if voice_id else "fallback",
        "selection_reason": reason,
        "selection_meta": agent_meta,
    }

    virtual_ip.voice_config = voice_config
    db.add(virtual_ip)
    db.commit()
    db.refresh(virtual_ip)
    return voice_config


def _get_bindings(container: dict[str, Any]) -> dict[str, Any]:
    raw = container.get("derived_character_voice_bindings")
    if isinstance(raw, dict):
        return raw
    return {}


def _set_bindings(container: dict[str, Any], bindings: dict[str, Any]) -> None:
    container["derived_character_voice_bindings"] = bindings


def find_existing_derived_voice_binding(
    *,
    story: Story,
    episode: Episode,
    scene: Scene | None,
    character_name: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """
    Find an existing derived-character voice binding, preferring narrower scope:
    scene -> episode -> story.

    Returns: (scope, record)
    """
    key = _norm_name(character_name)

    if scene and isinstance(scene.extra_metadata, dict):
        bindings = _get_bindings(scene.extra_metadata)
        record = bindings.get(key)
        if isinstance(record, dict) and record.get("voice_config"):
            return "scene", record

    if isinstance(episode.extra_metadata, dict):
        bindings = _get_bindings(episode.extra_metadata)
        record = bindings.get(key)
        if isinstance(record, dict) and record.get("voice_config"):
            return "episode", record

    if isinstance(story.extra_metadata, dict):
        bindings = _get_bindings(story.extra_metadata)
        record = bindings.get(key)
        if isinstance(record, dict) and record.get("voice_config"):
            return "story", record

    return None, None


async def _agent_decide_derived_scope(
    *,
    character_name: str,
    occurrences_in_episode: int,
    episodes_in_story: int,
    model: str | None = None,
    prefer_provider: str | None = None,
) -> tuple[DerivedCharacterScopeDecision | None, dict[str, Any]]:
    if not ai_service.ai_manager or not hasattr(ai_service.ai_manager, "generate_text"):
        return None, {"error": "ai_manager_not_initialized"}

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "scope": {"type": "string", "enum": ["scene", "episode", "story"]},
            "reason": {"type": "string"},
        },
        "required": ["scope"],
    }

    prompt = (
        "你是剧本制作系统的角色资产助手。给定一个“衍生角色”（IP库中不存在），请判断其音色绑定作用域：\n"
        "- scene：仅当前场景有效（一次性路人/店员）\n"
        "- episode：当前集内多次出现\n"
        "- story：跨多集反复出现（长期角色）\n\n"
        "只返回严格 JSON。\n\n"
        f"角色名：{character_name}\n"
        f"该角色在本集出现次数：{occurrences_in_episode}\n"
        f"该角色在全故事中出现的集数：{episodes_in_story}\n"
    )

    resp = await ai_service.ai_manager.generate_text(
        prompt=prompt,
        model=model,
        prefer_provider=prefer_provider,
        temperature=0.0,
        stream=False,
        json_schema={"name": "derived_scope", "schema": schema},
        system_prompt="只返回严格 JSON，scope 必须为 scene/episode/story 之一。",
    )
    meta = {
        "provider": resp.provider,
        "model": resp.model,
        "usage": resp.usage,
        "raw": resp.data,
    }
    if not resp.success:
        return None, {**meta, "error": resp.error}
    parsed = extract_json_block(resp.data) if isinstance(resp.data, str) else None
    if not isinstance(parsed, dict):
        return None, {**meta, "error": "invalid_json"}

    scope = str(parsed.get("scope") or "").strip()
    reason = str(parsed.get("reason") or "").strip() or None
    if scope not in {"scene", "episode", "story"}:
        return None, {**meta, "error": "invalid_scope", "chosen": scope}
    return DerivedCharacterScopeDecision(scope=scope, reason=reason), meta


def _fallback_scope(
    occurrences_in_episode: int, episodes_in_story: int
) -> DerivedCharacterScopeDecision:
    if episodes_in_story >= 2:
        return DerivedCharacterScopeDecision(
            scope="story", reason="heuristic: appears in multiple episodes"
        )
    if occurrences_in_episode >= 2:
        return DerivedCharacterScopeDecision(
            scope="episode", reason="heuristic: appears multiple times in episode"
        )
    return DerivedCharacterScopeDecision(
        scope="scene", reason="heuristic: one-off in scene"
    )


def _count_derived_character_occurrences(
    *,
    script_dialogues: list[dict[str, Any]] | None,
    character_name: str,
) -> int:
    if not script_dialogues:
        return 0
    key = _norm_name(character_name)
    n = 0
    for item in script_dialogues:
        if not isinstance(item, dict):
            continue
        who = item.get("character") or item.get("speaker") or item.get("name")
        if not who:
            continue
        if _norm_name(str(who)) == key:
            n += 1
    return n


def _count_story_episodes_with_character(
    db: Session,
    *,
    story_id: int,
    character_name: str,
) -> int:
    """
    Count how many episodes in a story contain the character name in their latest script dialogues.
    Best-effort heuristic (JSON is not queryable efficiently).
    """
    from app.models.script import Script

    key = _norm_name(character_name)
    episodes = db.query(Episode).filter(Episode.story_id == story_id).all()
    if not episodes:
        return 0
    ep_ids = [e.id for e in episodes]
    from sqlalchemy import func

    latest_subq = (
        db.query(
            Script.episode_id.label("episode_id"),
            func.max(Script.id).label("latest_id"),
        )
        .filter(Script.episode_id.in_(ep_ids))
        .group_by(Script.episode_id)
        .subquery()
    )
    scripts = (
        db.query(Script).join(latest_subq, Script.id == latest_subq.c.latest_id).all()
    )
    latest_by_episode = {sc.episode_id: sc for sc in scripts}

    count = 0
    for sc in latest_by_episode.values():
        dialogues = sc.dialogues or []
        found = False
        for item in dialogues:
            if not isinstance(item, dict):
                continue
            who = item.get("character") or item.get("speaker") or item.get("name")
            if who and _norm_name(str(who)) == key:
                found = True
                break
        if found:
            count += 1
    return count


async def ensure_derived_character_voice_binding(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    scene: Scene | None,
    script_dialogues: list[dict[str, Any]] | None,
    character_name: str,
    selection_model: str | None = None,
    selection_prefer_provider: str | None = None,
    tts_provider: str = "minimax",
    tts_model: str = "speech-2.6-hd",
) -> tuple[str, dict[str, Any]]:
    """
    Ensure a derived character voice binding exists at the agent-selected scope.

    Returns: (scope, voice_config)
    """
    existing_scope, existing_record = find_existing_derived_voice_binding(
        story=story, episode=episode, scene=scene, character_name=character_name
    )
    if existing_scope and isinstance(existing_record, dict):
        voice_cfg = existing_record.get("voice_config")
        if isinstance(voice_cfg, dict) and (
            voice_cfg.get("voice_id") or voice_cfg.get("voice_type")
        ):
            return existing_scope, voice_cfg

    occurrences = _count_derived_character_occurrences(
        script_dialogues=script_dialogues, character_name=character_name
    )
    episodes_in_story = _count_story_episodes_with_character(
        db, story_id=story.id, character_name=character_name
    )

    decision, scope_meta = await _agent_decide_derived_scope(
        character_name=character_name,
        occurrences_in_episode=occurrences,
        episodes_in_story=episodes_in_story,
        model=selection_model,
        prefer_provider=selection_prefer_provider,
    )
    if not decision:
        decision = _fallback_scope(occurrences, episodes_in_story)

    candidates = _voice_candidates()
    voice_id, reason, agent_meta = await _agent_choose_voice_id(
        character_name=character_name,
        character_description=None,
        candidates=candidates,
        model=selection_model,
        prefer_provider=selection_prefer_provider,
    )
    chosen = voice_id or _fallback_voice_id(candidates)

    voice_config: dict[str, Any] = {
        "provider": tts_provider,
        "tts_model": tts_model,
        "voice_id": chosen,
        "selected_at": _utc_now_iso(),
        "selected_by": "agent" if voice_id else "fallback",
        "selection_reason": reason,
        "selection_meta": agent_meta,
    }

    record = {
        "character_name": character_name,
        "scope": decision.scope,
        "scope_reason": decision.reason,
        "scope_meta": scope_meta,
        "voice_config": voice_config,
        "updated_at": _utc_now_iso(),
        "source": "dialogue_audio_pipeline",
    }

    key = _norm_name(character_name)

    if decision.scope == "scene":
        if not scene:
            # Fallback to episode scope if scene is absent.
            decision = DerivedCharacterScopeDecision(
                scope="episode", reason="scene_missing_fallback"
            )
        else:
            meta = dict(scene.extra_metadata or {})
            bindings = dict(_get_bindings(meta))
            bindings[key] = record
            _set_bindings(meta, bindings)
            scene.extra_metadata = meta
            db.add(scene)
            db.commit()
            db.refresh(scene)
            return "scene", voice_config

    if decision.scope == "story":
        meta = dict(story.extra_metadata or {})
        bindings = dict(_get_bindings(meta))
        bindings[key] = record
        _set_bindings(meta, bindings)
        story.extra_metadata = meta
        db.add(story)
        db.commit()
        db.refresh(story)
        return "story", voice_config

    # episode scope (default)
    meta = dict(episode.extra_metadata or {})
    bindings = dict(_get_bindings(meta))
    bindings[key] = record
    _set_bindings(meta, bindings)
    episode.extra_metadata = meta
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return "episode", voice_config
