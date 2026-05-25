"""Timeline render task dispatch boundary."""

from app.models.timeline import RenderJob
from app.models.user import User


def dispatch_timeline_render_job(job: RenderJob, current_user: User) -> None:
    dispatch_timeline_render_job_for_user_id(job, current_user.id)


def dispatch_timeline_render_job_for_user_id(
    job: RenderJob,
    user_id: int | None,
) -> None:
    from app.services.task_worker_timeline_render import timeline_render_task

    timeline_render_task.delay(job.id, user_id)
