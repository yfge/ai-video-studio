import json
from pathlib import Path
from typing import Any, Iterable, List
from uuid import uuid4

import pytest
from app.core.config import settings


@pytest.fixture
def mock_ai_service(monkeypatch):
    """Mock AIService to avoid real external dependencies."""

    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    created_files: List[Path] = []

    class _Logger:
        def warning(self, *_: object, **__: object) -> None:
            return None

        def info(self, *_: object, **__: object) -> None:
            return None

    class _MockAIService:
        def __init__(self) -> None:
            class _MockAIManager:
                async def image_to_image(
                    self,
                    image_url: str,
                    prompt: str,
                    model: str | None = None,
                    prefer_provider: str | None = None,
                    count: int = 1,
                    size: str | None = None,
                    **_: str,
                ):
                    from types import SimpleNamespace

                    return SimpleNamespace(
                        success=True,
                        data={
                            "images": [
                                f"https://example.com/mock-img2img/{uuid4().hex}.png"
                            ]
                        },
                        provider=prefer_provider or "mock-provider",
                        model=model or "mock-model",
                        usage={},
                    )

                async def generate_text(self, prompt: str, **_: str):
                    from app.services.providers.base import (
                        AIModelType,
                        AIResponse,
                        AITaskType,
                    )

                    if "投流表" in prompt or "Traffic Sheet" in prompt:
                        payload = {
                            "episode_id": 1,
                            "script_id": 1,
                            "market_region": "NA",
                            "micro_genre": "test",
                            "assets": [
                                {
                                    "asset_id": "ep1_asset01_15s",
                                    "duration_seconds": 15,
                                    "market_region": "NA",
                                    "micro_genre": "test",
                                    "hook_type": "reveal",
                                    "source_episode": 1,
                                    "source_timecode_start": "00:00:00",
                                    "source_timecode_end": "00:00:15",
                                    "key_line": "mock line",
                                    "visual_hook": "mock visual",
                                    "shot_list": ["shot 1"],
                                    "cliff_or_cta": "mock cta",
                                    "music_reference": None,
                                    "compliance_flags": [],
                                }
                            ],
                        }
                    else:
                        payload = {
                            "overall_score": 4.2,
                            "dimension_scores": {
                                "conflict_intensity": 4.5,
                                "character_recognizability": 4.0,
                                "cultural_fit": 4.5,
                                "clip_ability": 4.0,
                                "logic_coherence": 4.0,
                            },
                            "verdict": "pass",
                            "strengths": ["mock strength"],
                            "risks": [],
                            "rewrite_guidance": [],
                            "suggested_ad_hooks": ["mock hook"],
                        }

                    return AIResponse(
                        success=True,
                        data=json.dumps(payload, ensure_ascii=False),
                        provider="mock-provider",
                        model="mock-model",
                        task_type=AITaskType.STORY_GENERATION,
                        model_type=AIModelType.TEXT_GENERATION,
                        usage={},
                    )

            self.ai_manager = _MockAIManager()
            self.logger = _Logger()

        async def generate_virtual_ip_image(
            self,
            ip_name: str,
            description: str,
            style: str,
            category: str,
            model: str,
            additional_prompts: Iterable[str] | None = None,
            **_: str,
        ) -> dict:
            filename = f"mock-ai-{uuid4().hex}.png"
            file_path = uploads_dir / filename
            file_path.write_bytes(b"0" * 2048)
            created_files.append(file_path)
            return {
                "prompt": f"mock prompt for {ip_name}",
                "style": style,
                "model_used": model or "mock-model",
                "generation_method": "mock-provider",
                "local_file_path": str(file_path),
                "oss_upload": None,
                "usage": {"provider": "mock-provider", "model": model or "mock-model"},
                "additional_prompts": list(additional_prompts or []),
            }

        async def _persist_generated_image(
            self,
            image_data: str,
            *,
            ip_name: str,
            category: str,
            prefix: str,
            metadata: dict | None = None,
            require_upload: bool = False,
        ) -> dict:
            filename = f"mock-variant-{uuid4().hex}.png"
            file_path = uploads_dir / filename
            file_path.write_bytes(b"0" * 2048)
            created_files.append(file_path)

            oss_url = None
            oss_upload = None
            if require_upload:
                oss_url = f"https://oss.example.com/{prefix}/{filename}"
                oss_upload = {"success": True, "file_url": oss_url}

            return {
                "local_file_path": str(file_path),
                "relative_path": f"/uploads/{filename}",
                "file_size": file_path.stat().st_size,
                "filename": filename,
                "oss_url": oss_url,
                "oss_upload": oss_upload,
                "metadata": metadata or {},
                "ip_name": ip_name,
                "category": category,
                "prefix": prefix,
                "source_image": image_data,
            }

        async def generate_story_outline(self, **_: str) -> dict:
            normalized = {
                "premise": "Mock premise",
                "synopsis": "Mock synopsis",
                "main_conflict": "Mock conflict",
                "resolution": "Mock resolution",
                "main_characters": [
                    {"name": "Hero", "role": "protagonist"},
                    {"name": "Guide", "role": "mentor"},
                ],
                "character_relationships": {"Hero": {"Guide": "mentor"}},
            }
            return {
                "normalized": normalized,
                "prompt": "mock-story-prompt",
                "generation_method": "mock-provider:story",
            }

        async def generate_episodes(self, episode_count: int = 1, **_: str) -> dict:
            episodes_payload = {
                "episodes": [
                    {
                        "episode_number": idx + 1,
                        "title": f"Mock Episode {idx + 1}",
                        "summary": "Mock summary",
                        "plot_points": [{"order": 1, "description": "Mock plot"}],
                        "character_arcs": {"Hero": "Learns trust"},
                        "conflicts": [
                            {
                                "type": "mock",
                                "description": "Mock conflict",
                                "intensity": "medium",
                            }
                        ],
                        "scene_count": 3,
                    }
                    for idx in range(episode_count or 1)
                ]
            }
            return {
                "content": json.dumps(episodes_payload, ensure_ascii=False),
                "prompt": "mock-episode-prompt",
                "generation_method": "mock-provider:episodes",
            }

        async def generate_script(self, **_: Any) -> dict:
            character_name = "旁白"

            script_payload = {
                "content": (
                    "【音效】砰！画面直接切入冲突现场。\n"
                    "# screenplay (zh-CN)\n"
                    "## 场景\n"
                    f"- [场景 1] Scene 1: {character_name} finds the hidden key.\n"
                    f"【快】【情绪目的：推进冲突】{character_name} grabs the key before the door opens.\n"
                    "\n## 对白\n"
                    f"[场景 1] {character_name}: Stop now?\n"
                    "\n## 舞台指示\n"
                    f"[场景 1][mid] {character_name} hides the key under the lamp.\n"
                    "【慢】【情绪目的：留下悬念】Which door does the key open?"
                ),
                "scenes": [
                    {
                        "scene_number": 1,
                        "location": "Room",
                        "time": "Day",
                        "description": "Mock scene description",
                    }
                ],
                "dialogues": [
                    {
                        "scene_number": 1,
                        "character": character_name,
                        "content": "Stop now?",
                    }
                ],
                "stage_directions": [
                    {"scene_number": 1, "direction": "Camera pans across the room."}
                ],
            }
            return {
                "content": script_payload,
                "prompt": "mock-script-prompt",
                "generation_method": "mock-provider:scripts",
            }

    mock_service = _MockAIService()

    from app.services import ai_service as ai_module

    monkeypatch.setattr(ai_module, "ai_service", mock_service)

    # Patch cached imports for modules that bind `ai_service` at import-time.
    import app.api.v1.endpoints.episodes.async_tasks as episodes_async
    import app.api.v1.endpoints.episodes.regenerate as episodes_regenerate
    import app.api.v1.endpoints.scripts_legacy as scripts_legacy_ep
    import app.api.v1.endpoints.virtual_ip_images.async_tasks as vip_async
    import app.api.v1.endpoints.virtual_ip_images.generation as vip_generation
    import app.api.v1.endpoints.virtual_ip_images.generation_helpers as vip_gen_helpers
    import app.services.episode.episode_generation_persistence as episode_generation_persistence
    import app.services.episode.episode_generation_service as episode_generation_service
    import app.services.script.script_generator as script_generator_service
    import app.services.story.story_generation_service as story_generation_service
    import app.services.story.story_novel_export_ai as story_novel_export_ai

    monkeypatch.setattr(scripts_legacy_ep, "ai_service", mock_service)
    monkeypatch.setattr(vip_gen_helpers, "ai_service", mock_service)
    monkeypatch.setattr(vip_generation, "ai_service", mock_service)
    monkeypatch.setattr(vip_async, "ai_service", mock_service)
    monkeypatch.setattr(episodes_async, "ai_service", mock_service)
    monkeypatch.setattr(episodes_regenerate, "ai_service", mock_service)
    monkeypatch.setattr(story_generation_service, "ai_service", mock_service)
    monkeypatch.setattr(episode_generation_service, "ai_service", mock_service)
    monkeypatch.setattr(episode_generation_persistence, "ai_service", mock_service)
    monkeypatch.setattr(script_generator_service, "ai_service", mock_service)
    monkeypatch.setattr(story_novel_export_ai, "ai_service", mock_service)

    try:
        yield mock_service
    finally:
        for file_path in created_files:
            if file_path.exists():
                file_path.unlink()
