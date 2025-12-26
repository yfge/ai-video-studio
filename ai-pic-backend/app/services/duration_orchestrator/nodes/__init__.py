"""
Duration Orchestrator LangGraph 节点

每个节点负责 StateGraph 中的一个处理步骤。
"""

from app.services.duration_orchestrator.nodes.allocate_budget import (
    allocate_budget_node,
    should_proceed_to_generation,
)
from app.services.duration_orchestrator.nodes.assemble_episode import (
    assemble_episode_node,
)
from app.services.duration_orchestrator.nodes.commit_scene import (
    commit_scene_node,
    should_continue_or_assemble,
)
from app.services.duration_orchestrator.nodes.final_validation import (
    final_validation_node,
    should_pass_or_fail,
)
from app.services.duration_orchestrator.nodes.generate_dialogue import (
    generate_dialogue_node,
    should_proceed_to_tts,
)
from app.services.duration_orchestrator.nodes.prepare_retry import (
    prepare_retry_node,
    should_retry_or_fail,
)
from app.services.duration_orchestrator.nodes.tts_trial import (
    estimate_duration_from_dialogues,
    tts_trial_node,
)
from app.services.duration_orchestrator.nodes.validate_duration import (
    check_all_scenes_done,
    should_commit_or_retry,
    validate_duration_node,
)

__all__ = [
    # Budget allocation
    "allocate_budget_node",
    "should_proceed_to_generation",
    # Dialogue generation
    "generate_dialogue_node",
    "should_proceed_to_tts",
    # TTS trial
    "tts_trial_node",
    "estimate_duration_from_dialogues",
    # Duration validation
    "validate_duration_node",
    "should_commit_or_retry",
    "check_all_scenes_done",
    # Scene commit
    "commit_scene_node",
    "should_continue_or_assemble",
    # Retry preparation
    "prepare_retry_node",
    "should_retry_or_fail",
    # Episode assembly
    "assemble_episode_node",
    # Final validation
    "final_validation_node",
    "should_pass_or_fail",
]
