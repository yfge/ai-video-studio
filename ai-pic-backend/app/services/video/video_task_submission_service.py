from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import anyio

from app.core.logging import get_logger
from app.models.script import Script
from app.models.task import Task, TaskStatus
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.repositories.video_generation_task_repository import (
    VideoGenerationTaskRepository,
)
from app.services.video.video_task_dispatcher import VideoTaskDispatcher
from app.services.video.video_task_utils import (
    build_parameters_payload,
    build_selection_map,
    coerce_duration,
    normalize_submission_options,
    resolve_frame_urls,
    resolve_prompt,
)


VIDEO_TASK_TIMEOUT = timedelta(hours=1)


class VideoTaskSubmissionService:
    def __init__(self, db, ai_manager):
        self.db = db
        self.repo = VideoGenerationTaskRepository(db)
        self.dispatcher = VideoTaskDispatcher(ai_manager)
        self.logger = get_logger("video_task_submission")

    def submit_storyboard_video_tasks(
        self,
        *,
        task_id: int,
        script_id: int,
        frame_indexes: Optional[List[int]],
        selections: Optional[List[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
    ) -> None:
        task = self._load_task(task_id)
        frames = self._load_storyboard_frames(script_id)
        target_indexes = self._resolve_target_indexes(frame_indexes, frames)
        selection_by_index = build_selection_map(selections)
        opts = normalize_submission_options(options)

        submitted = 0
        failures: list[str] = []
        for idx in target_indexes:
            submitted_one, error = self._submit_frame(
                task,
                script_id,
                idx,
                frames,
                selection_by_index,
                opts,
            )
            if submitted_one:
                submitted += 1
            if error:
                failures.append(error)

        self.db.commit()
        self._finalize_submission(task, submitted, failures)

    def _load_task(self, task_id: int) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise RuntimeError("任务不存在")
        task.status = TaskStatus.PROCESSING
        self.db.commit()
        return task

    def _load_storyboard_frames(self, script_id: int) -> List[Dict[str, Any]]:
        script = self.db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise RuntimeError("剧本不存在")
        storyboard = (script.extra_metadata or {}).get("storyboard") or {}
        frames_src = list(storyboard.get("frames") or [])
        if not frames_src:
            raise RuntimeError("未找到分镜数据")
        return [dict(fr) if isinstance(fr, dict) else {} for fr in frames_src]

    def _resolve_target_indexes(
        self, frame_indexes: Optional[List[int]], frames: List[Dict[str, Any]]
    ) -> List[int]:
        return frame_indexes or list(range(len(frames)))

    def _submit_frame(
        self,
        task: Task,
        script_id: int,
        frame_index: int,
        frames: List[Dict[str, Any]],
        selection_by_index: Dict[int, Dict[str, Any]],
        opts: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        if frame_index < 0 or frame_index >= len(frames):
            return False, None
        frame = frames[frame_index]
        selection = selection_by_index.get(frame_index) or {}
        start_url, end_url, error = resolve_frame_urls(
            frame, selection, opts["use_end_frame"]
        )
        if error:
            self._record_failure(task, script_id, frame_index, error)
            return False, f"frame {frame_index}: {error}"

        prompt_value = resolve_prompt(frame, opts.get("prompt"))
        duration_int = coerce_duration(
            opts["duration"] if opts.get("duration") is not None else frame.get("duration_seconds")
        )

        response = self._submit_provider_task(
            prompt_value, start_url, end_url, duration_int, opts
        )
        if not response.success:
            self._record_failure(task, script_id, frame_index, response.error)
            return False, f"frame {frame_index}: {response.error}"

        provider_task_id = (response.data or {}).get("task_id")
        if not provider_task_id:
            self._record_failure(task, script_id, frame_index, "未返回任务ID")
            return False, f"frame {frame_index}: 未返回任务ID"

        self._create_task_record(
            task=task,
            script_id=script_id,
            frame_index=frame_index,
            response=response,
            prompt=prompt_value,
            start_url=start_url,
            end_url=end_url,
            duration=duration_int,
            opts=opts,
        )
        return True, None

    def _submit_provider_task(
        self,
        prompt: Optional[str],
        start_url: Optional[str],
        end_url: Optional[str],
        duration: int,
        opts: Dict[str, Any],
    ):
        payload = {
            "prompt": prompt,
            "image_url": start_url,
            "end_image_url": end_url,
            "model": opts.get("model"),
            "prefer_provider": None,
            "duration": duration,
            "fps": opts["fps"],
            "resolution": opts["resolution"],
            "ratio": opts.get("ratio"),
            "watermark": opts.get("watermark"),
            "seed": opts.get("seed"),
            "camera_fixed": opts.get("camera_fixed"),
            "camera_control": opts.get("camera_control"),
            "service_tier": opts.get("service_tier"),
            "execution_expires_after": opts.get("execution_expires_after"),
            "return_last_frame": opts.get("return_last_frame"),
        }
        return anyio.run(self._submit_provider_task_async, payload)

    async def _submit_provider_task_async(
        self, payload: Dict[str, Any]
    ) -> Any:
        return await self.dispatcher.submit_video_task(**payload)

    def _create_task_record(
        self,
        *,
        task: Task,
        script_id: int,
        frame_index: int,
        response,
        prompt: Optional[str],
        start_url: Optional[str],
        end_url: Optional[str],
        duration: int,
        opts: Dict[str, Any],
    ) -> None:
        self.repo.create(
            task_id=task.id,
            script_id=script_id,
            frame_index=frame_index,
            user_id=task.user_id,
            provider=response.provider,
            provider_task_id=str((response.data or {}).get("task_id")),
            model=response.model,
            model_type="image_to_video",
            prompt=prompt,
            parameters=json.dumps(
                build_parameters_payload(prompt, start_url, end_url, duration, opts),
                ensure_ascii=False,
            ),
            status=VideoGenerationTaskStatus.SUBMITTED,
            submitted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + VIDEO_TASK_TIMEOUT,
        )

    def _finalize_submission(
        self, task: Task, submitted: int, failures: List[str]
    ) -> None:
        if submitted == 0:
            error_msg = "未生成任何视频" + (
                f"：{failures[0]}" if failures else ""
            )
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            self.db.commit()
            raise RuntimeError(error_msg)
        if failures:
            task.error_message = "; ".join(failures[:5])
            self.db.commit()

    def _record_failure(
        self,
        task: Task,
        script_id: int,
        frame_index: int,
        error_message: str,
    ) -> None:
        self.repo.create(
            task_id=task.id,
            script_id=script_id,
            frame_index=frame_index,
            user_id=task.user_id,
            provider="unknown",
            provider_task_id="",
            model=None,
            model_type="image_to_video",
            prompt=None,
            parameters=json.dumps({}, ensure_ascii=False),
            status=VideoGenerationTaskStatus.FAILED,
            error_message=error_message,
        )
