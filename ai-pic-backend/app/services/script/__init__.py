"""
Script services package.

Provides business logic for script management including CRUD operations
and AI-powered generation.
"""

from app.services.script.production_pipeline import (
    annotate_storyboard_frames_with_hooks,
    build_hook_schedule,
    run_auto_timeline_placeholders,
    run_production_script_generation,
)
from app.services.script.script_generator import ScriptGenerator, get_script_generator
from app.services.script.script_service import ScriptService, get_script_service

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
