#!/usr/bin/env python3
"""Scenario registry for browser and golden-path harness flows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrowserScenario:
    name: str
    path: str
    requires_auth: bool
    required_text: str
    notes: str


BROWSER_SCENARIOS: dict[str, BrowserScenario] = {
    "login_smoke": BrowserScenario(
        name="login_smoke",
        path="/login",
        requires_auth=False,
        required_text="登录",
        notes="Validate the login form renders without blocking console or network errors.",
    ),
    "virtual_ip_image_generation_smoke": BrowserScenario(
        name="virtual_ip_image_generation_smoke",
        path="/virtual-ip/{virtual_ip_id}/images",
        requires_auth=True,
        required_text="虚拟",
        notes="Open the Virtual IP image workspace and capture the request path evidence.",
    ),
    "episode_timeline_smoke": BrowserScenario(
        name="episode_timeline_smoke",
        path="/episodes/{episode_id}/storyboard",
        requires_auth=True,
        required_text="分镜",
        notes="Open the episode storyboard/timeline-adjacent workspace and capture readiness.",
    ),
    "task_details_trace_smoke": BrowserScenario(
        name="task_details_trace_smoke",
        path="/tasks",
        requires_auth=True,
        required_text="任务",
        notes="Open the task list so run_id/request_id/task_id evidence can be correlated.",
    ),
}


GOLDEN_PATH_SCENARIOS = {
    "mock_smoke": {
        "description": "Health-check the lite stack and artifact pipeline in mock mode.",
        "requires_auth": False,
    },
    "operator_smoke": {
        "description": "Login and verify the operator-facing web entrypoints are reachable.",
        "requires_auth": True,
    },
    "timeline_export_regression": {
        "description": (
            "Queue the timeline pipeline and trace the resulting task until completion "
            "or a well-structured failure."
        ),
        "requires_auth": True,
    },
}
