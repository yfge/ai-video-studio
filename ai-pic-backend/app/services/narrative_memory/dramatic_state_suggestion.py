"""Explicit provider task for scene-level dramatic-state suggestions."""

import json

import anyio
from app.core.database import get_task_db
from app.models.task import TaskStatus
from app.repositories.script_repository import ScriptRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.dramatic_state import DramaticStatePayload
from app.services.ai.structured_output import generate_with_repair
from app.services.ai_service import ai_service
from app.services.narrative_memory.dramatic_state_service import DramaticStateService


def process_dramatic_state_suggestion(
    task_id: int,
    script_business_id: str,
    scene_business_id: str,
    payload: dict,
    user_id: int,
) -> None:
    with get_task_db() as db:
        tasks = TaskRepository(db)
        task = tasks.get_by_id(task_id)
        if not task:
            return
        try:
            task.status = TaskStatus.PROCESSING
            db.commit()
            user = UserRepository(db).get_by_id(user_id)
            service = DramaticStateService(ScriptRepository(db))
            script, scene, current = service.suggestion_context(
                script_business_id, scene_business_id, user
            )
            manager = ai_service.ai_manager
            if not manager:
                raise RuntimeError("当前没有可用的文本模型提供商")

            async def _run():
                return await generate_with_repair(
                    ai_manager=manager,
                    base_prompt=_prompt(script, scene, current),
                    model=payload.get("model"),
                    prefer_provider=None,
                    temperature=0.3,
                    schema_name="dramatic_state",
                    schema=DramaticStatePayload.model_json_schema(by_alias=True),
                    system_prompt="你是剧本潜台词编辑，只返回严格 JSON。",
                    pydantic_model=DramaticStatePayload,
                    max_repairs=1,
                )

            result = anyio.run(_run)
            normalized = result.get("normalized")
            if not normalized:
                raise RuntimeError("潜台词建议返回格式无效")
            service.save_suggestion(
                script_business_id,
                scene_business_id,
                based_on_version=int(payload["expected_version"]),
                state=DramaticStatePayload.model_validate(normalized),
                user=user,
            )
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"dramatic-state:{script_business_id}:{scene_business_id}"
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            task = tasks.get_by_id(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc) or repr(exc)
                db.commit()


def _prompt(script, scene: dict, current: dict) -> str:
    context = {
        "scene": scene,
        "current_dramatic_state": current.get("dramatic_state"),
        "episode_narrative_memory": (script.extra_metadata or {}).get(
            "narrative_memory"
        ),
        "audience_disclosure": (script.extra_metadata or {}).get("audience_disclosure"),
    }
    return f"""为当前场景建议 DramaticState 草稿。区分表层行动、隐藏目标和真实情绪；
subtext_only 不可直说，must_not_reveal 不可提前泄露。只使用给定 Story 的上下文。
上下文：{json.dumps(context, ensure_ascii=False, default=str)}"""
