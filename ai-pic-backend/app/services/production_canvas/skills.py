from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasSkillDefinition,
    ProductionCanvasSkillReuseTarget,
)

from .clip_skills import CLIP_SKILL_DEFINITIONS


def _target(
    kind: str,
    label: str,
    target: str,
    description: str | None = None,
) -> ProductionCanvasSkillReuseTarget:
    return ProductionCanvasSkillReuseTarget(
        kind=kind,
        label=label,
        target=target,
        description=description,
    )


SKILL_DEFINITIONS = [
    ProductionCanvasSkillDefinition(
        id="brief.compose",
        label="Brief Skill",
        description="Turn the chat production goal into a structured short-drama brief.",
        reuse_targets=[
            _target("artifact", "Canvas prompt", "production_canvas.prompt"),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="asset.select",
        label="Asset Selection",
        description="Inspect existing IP and environment assets and select matching reuse inputs.",
        reuse_targets=[
            _target(
                "repository",
                "Virtual IP repository",
                "app.repositories.virtual_ip_repository.VirtualIPRepository",
            ),
            _target(
                "repository",
                "Environment repository",
                "app.repositories.environment_repository.EnvironmentRepository",
            ),
            _target(
                "repository",
                "IP environment links",
                "app.repositories.virtual_ip_environment_repository.VirtualIPEnvironmentRepository",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="virtual_ip.image",
        label="Virtual IP Image",
        description="Queue existing Virtual IP image generation for the selected character asset.",
        reuse_targets=[
            _target(
                "worker",
                "Virtual IP image worker",
                "tasks.virtual_ip_image_generate",
            ),
            _target(
                "service",
                "Virtual IP image generation",
                "app.services.ai.images_generation.ImageGenerationService.generate_virtual_ip_image",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="environment.image",
        label="Environment Image",
        description="Queue existing environment text-to-image generation for the selected scene asset.",
        reuse_targets=[
            _target(
                "worker",
                "Environment image worker",
                "tasks.environment_image_generate",
            ),
            _target(
                "service",
                "Environment image generation",
                "app.services.story_structure.environment_image_generation.generate_environment_images",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="script.generate",
        label="Script Skill",
        description="Queue production script generation through the existing script pipeline.",
        reuse_targets=[
            _target(
                "api",
                "Script async endpoint",
                "app.api.v1.endpoints.scripts_generation_queue.generate_script_async",
            ),
            _target(
                "service",
                "Production script pipeline",
                "app.services.script.production_pipeline.run_production_script_generation",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="timeline.assemble",
        label="Timeline Skill",
        description="Reuse the shared audio, Timeline Spec, and shot-plan main chain.",
        reuse_targets=[
            _target(
                "service",
                "Timeline pipeline queue",
                "app.services.script.timeline_pipeline_queue.queue_timeline_pipeline_task",
            ),
            _target(
                "service",
                "Timeline main chain",
                "app.services.timeline_pipeline_runner.run_timeline_main_chain",
            ),
            _target(
                "service",
                "Timeline import",
                "app.services.timeline_import_service.import_audio_timeline_to_timeline_spec",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="storyboard.plan",
        label="Storyboard Skill",
        description="Reuse storyboard generation and production storyboard placeholder logic.",
        reuse_targets=[
            _target(
                "service",
                "Storyboard queue service",
                "app.services.storyboard.generation_queue.queue_storyboard_generation_task",
            ),
            _target(
                "service",
                "Production storyboard placeholders",
                "app.services.script.production_storyboard.run_auto_timeline_placeholders",
            ),
            _target(
                "worker",
                "Storyboard task processor",
                "app.api.v1.endpoints.storyboard.task_processors._process_storyboard_generation_task",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="image.candidates",
        label="Image Candidates",
        description="Create or reuse storyboard/keyframe image candidates through existing image services.",
        reuse_targets=[
            _target(
                "service",
                "Storyboard image generation",
                "app.services.storyboard.storyboard_image_autogen.queue_storyboard_image_generation",
            ),
            _target(
                "service",
                "Timeline keyframe processor",
                "app.services.timeline_clip_keyframe_processor.TimelineClipKeyframeProcessor",
            ),
        ],
    ),
    *CLIP_SKILL_DEFINITIONS[:1],
    ProductionCanvasSkillDefinition(
        id="video.candidates",
        label="Video Candidates",
        description="Queue provider video candidates from storyboard frames or Timeline clips.",
        reuse_targets=[
            _target(
                "service",
                "Storyboard video queue service",
                "app.services.storyboard.video_generation_queue.queue_storyboard_video_generation_task",
            ),
            _target(
                "service",
                "Timeline video rework dispatch",
                "app.services.timeline_clip_video_rework_dispatch.dispatch_timeline_clip_video_rework_task",
            ),
        ],
    ),
    *CLIP_SKILL_DEFINITIONS[1:],
    ProductionCanvasSkillDefinition(
        id="timeline.render",
        label="Render Skill",
        description="Render the current Timeline version after all clip videos are ready.",
        reuse_targets=[
            _target(
                "service",
                "Timeline render",
                "app.services.timeline_service.TimelineService.queue_render_job",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="timeline.export",
        label="Export Skill",
        description="Expose the successful final render as a downloadable production asset.",
        reuse_targets=[
            _target(
                "repository",
                "Render jobs",
                "app.repositories.timeline_repository.RenderJobRepository",
            ),
        ],
    ),
    ProductionCanvasSkillDefinition(
        id="report.summarize",
        label="Report Skill",
        description="Summarize task, quality, cost, provider, and render evidence.",
        reuse_targets=[
            _target("api", "Task audit endpoint", "app.api.v1.endpoints.tasks"),
            _target(
                "service",
                "Timeline render dispatch",
                "app.services.timeline_render_dispatch.dispatch_timeline_render_job",
            ),
        ],
    ),
]


def list_canvas_skill_definitions() -> list[ProductionCanvasSkillDefinition]:
    return list(SKILL_DEFINITIONS)


def get_canvas_skill_definition(skill_id: str) -> ProductionCanvasSkillDefinition:
    return next(skill for skill in SKILL_DEFINITIONS if skill.id == skill_id)
