"""Versioned scene intent/subtext metadata and deterministic quality checks."""

import hashlib
import json
from typing import Any

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.script_repository import ScriptRepository
from app.schemas.dramatic_state import DramaticStatePayload


class DramaticStateService:
    def __init__(self, repo: ScriptRepository):
        self.repo = repo

    def get(self, script_business_id: str, scene_business_id: str, user: User) -> dict:
        script, scene = self._scene(script_business_id, scene_business_id, user)
        state = scene.get("dramatic_state") or self._empty_state()
        version = int(scene.get("dramatic_state_version") or 0)
        return self._response(scene_business_id, state, version, script, scene)

    def update(
        self,
        script_business_id: str,
        scene_business_id: str,
        *,
        expected_version: int,
        state: DramaticStatePayload,
        user: User,
    ) -> dict:
        script, scene = self._scene(script_business_id, scene_business_id, user)
        actual = int(scene.get("dramatic_state_version") or 0)
        if actual != expected_version:
            raise ConflictError(
                "场景潜台词已被其他窗口更新",
                context={
                    "expected_version": expected_version,
                    "actual_version": actual,
                },
            )
        data = state.model_dump(by_alias=True)
        scene["dramatic_state"] = data
        scene["dramatic_state_version"] = actual + 1
        scene["dramatic_state_hash"] = self._hash(data)
        script.scenes = [
            dict(item) if isinstance(item, dict) else item
            for item in script.scenes or []
        ]
        self.repo.session.commit()
        self.repo.session.refresh(script)
        return self._response(scene_business_id, data, actual + 1, script, scene)

    def _scene(self, script_business_id: str, scene_business_id: str, user: User):
        owner_id = None if user.is_admin or user.is_superuser else user.id
        script = self.repo.get_with_relations(
            business_id=script_business_id, user_id=owner_id
        )
        if not script:
            raise NotFoundError.script(script_business_id)
        for index, item in enumerate(script.scenes or [], start=1):
            if not isinstance(item, dict):
                continue
            identifiers = {
                str(item.get("scene_business_id") or ""),
                str(item.get("scene_id") or ""),
                str(item.get("scene_number") or index),
            }
            if scene_business_id in identifiers:
                item.setdefault("scene_business_id", scene_business_id)
                return script, item
        raise NotFoundError.scene(scene_business_id)

    def _response(self, scene_id, state, version, script, scene) -> dict:
        return {
            "scene_business_id": scene_id,
            "version": version,
            "state_hash": scene.get("dramatic_state_hash") or self._hash(state),
            "dramatic_state": state,
            "quality_gate": self._quality_gate(state, script, scene),
            "suggestion": scene.get("dramatic_state_suggestion"),
            "suggestion_based_on_version": scene.get(
                "dramatic_state_suggestion_based_on_version"
            ),
            "available_memory_preview": self._memory_preview(script),
        }

    def suggestion_context(
        self, script_business_id: str, scene_business_id: str, user: User
    ) -> tuple[Any, dict, dict]:
        script, scene = self._scene(script_business_id, scene_business_id, user)
        return script, scene, self.get(script_business_id, scene_business_id, user)

    def save_suggestion(
        self,
        script_business_id: str,
        scene_business_id: str,
        *,
        based_on_version: int,
        state: DramaticStatePayload,
        user: User,
    ) -> dict:
        script, scene = self._scene(script_business_id, scene_business_id, user)
        scene["dramatic_state_suggestion"] = state.model_dump(by_alias=True)
        scene["dramatic_state_suggestion_based_on_version"] = based_on_version
        script.scenes = [
            dict(item) if isinstance(item, dict) else item
            for item in script.scenes or []
        ]
        self.repo.session.commit()
        return self._response(
            scene_business_id,
            scene.get("dramatic_state") or self._empty_state(),
            int(scene.get("dramatic_state_version") or 0),
            script,
            scene,
        )

    @staticmethod
    def _quality_gate(state: dict, script, scene: dict) -> dict:
        text = DramaticStateService._dialogue_text(script, scene)
        issues = []
        for secret in state.get("must_not_reveal") or []:
            if secret and secret in text:
                issues.append({"id": "must_not_reveal", "detail": secret})
        for intent in state.get("character_intents") or []:
            hidden = intent.get("hidden_goal") or ""
            if (
                intent.get("expression_policy") == "subtext_only"
                and hidden
                and hidden in text
            ):
                issues.append(
                    {
                        "id": "subtext_spoken_directly",
                        "detail": hidden,
                        "character_business_id": intent.get("character_business_id"),
                    }
                )
        return {"passed": not issues, "blocking_issues": issues}

    @staticmethod
    def _dialogue_text(script, scene: dict) -> str:
        values: list[str] = []
        values.extend(DramaticStateService._strings(scene.get("dialogues")))
        scene_number = scene.get("scene_number")
        for item in script.dialogues or []:
            if isinstance(item, dict) and (
                scene_number is None or item.get("scene_number") == scene_number
            ):
                values.extend(DramaticStateService._strings(item))
        return " ".join(values)

    @staticmethod
    def _memory_preview(script) -> list[dict]:
        context = (script.extra_metadata or {}).get("narrative_memory") or {}
        return [
            {
                "character_business_id": item.get("character_business_id"),
                "snapshot_hash": item.get("snapshot_hash"),
                "memories": item.get("memories") or [],
                "growth_state": item.get("growth_state") or {},
            }
            for item in context.get("character_snapshots") or []
        ]

    @staticmethod
    def _strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            return [
                part
                for item in value.values()
                for part in DramaticStateService._strings(item)
            ]
        if isinstance(value, list):
            return [
                part for item in value for part in DramaticStateService._strings(item)
            ]
        return []

    @staticmethod
    def _empty_state() -> dict:
        return DramaticStatePayload().model_dump(by_alias=True)

    @staticmethod
    def _hash(data: dict) -> str:
        raw = json.dumps(
            data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(raw.encode()).hexdigest()
