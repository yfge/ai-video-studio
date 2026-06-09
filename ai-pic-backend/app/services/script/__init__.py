"""
Script services package.

The package exposes common script services without importing the production
pipeline during package initialization. Several audio modules import script
submodules directly; eager production imports create a circular dependency with
scene audio generation.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ScriptService",
    "get_script_service",
    "ScriptGenerator",
    "get_script_generator",
    "annotate_storyboard_frames_with_hooks",
    "build_hook_schedule",
    "run_auto_timeline_placeholders",
    "run_production_script_generation",
]


def __getattr__(name: str) -> Any:
    if name in {"ScriptService", "get_script_service"}:
        from app.services.script.script_service import (
            ScriptService,
            get_script_service,
        )

        return {
            "ScriptService": ScriptService,
            "get_script_service": get_script_service,
        }[name]

    if name in {"ScriptGenerator", "get_script_generator"}:
        from app.services.script.script_generator import (
            ScriptGenerator,
            get_script_generator,
        )

        return {
            "ScriptGenerator": ScriptGenerator,
            "get_script_generator": get_script_generator,
        }[name]

    if name in {
        "annotate_storyboard_frames_with_hooks",
        "build_hook_schedule",
        "run_auto_timeline_placeholders",
        "run_production_script_generation",
    }:
        from app.services.script.production_pipeline import (
            annotate_storyboard_frames_with_hooks,
            build_hook_schedule,
            run_auto_timeline_placeholders,
            run_production_script_generation,
        )

        return {
            "annotate_storyboard_frames_with_hooks": annotate_storyboard_frames_with_hooks,
            "build_hook_schedule": build_hook_schedule,
            "run_auto_timeline_placeholders": run_auto_timeline_placeholders,
            "run_production_script_generation": run_production_script_generation,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
