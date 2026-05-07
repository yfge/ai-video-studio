#!/usr/bin/env python3
"""Scenario registry for browser and golden-path harness flows."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrowserScenario:
    name: str
    path: str
    requires_auth: bool
    required_text: str
    notes: str


@dataclass(frozen=True)
class GoldenPathScenario:
    name: str
    description: str
    requires_auth: bool
    notes: str
    requires_script_id: bool = False
    requires_virtual_ip_id: bool = False
    legacy_aliases: tuple[str, ...] = field(default_factory=tuple)


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
    "virtual_ip_list_smoke": BrowserScenario(
        name="virtual_ip_list_smoke",
        path="/virtual-ip",
        requires_auth=True,
        required_text="IP 项目",
        notes="Open the IP-centered asset entrypoint and capture migration-state evidence.",
    ),
    "virtual_ip_detail_smoke": BrowserScenario(
        name="virtual_ip_detail_smoke",
        path="/virtual-ip/{virtual_ip_id}",
        requires_auth=True,
        required_text="IP 详情",
        notes="Open the IP detail operator workspace and capture readiness evidence.",
    ),
    "environment_migration_smoke": BrowserScenario(
        name="environment_migration_smoke",
        path="/environments",
        requires_auth=True,
        required_text="环境迁移",
        notes="Open the environment migration entrypoint and capture migration-state evidence.",
    ),
    "environment_detail_smoke": BrowserScenario(
        name="environment_detail_smoke",
        path="/environments/{environment_id}",
        requires_auth=True,
        required_text="环境详情",
        notes="Open the environment detail generation workspace and capture migration-state evidence.",
    ),
    "workbench_smoke": BrowserScenario(
        name="workbench_smoke",
        path="/",
        requires_auth=True,
        required_text="生产工作台",
        notes="Open the authenticated operator workbench and capture dashboard readiness.",
    ),
    "story_master_detail_smoke": BrowserScenario(
        name="story_master_detail_smoke",
        path="/stories",
        requires_auth=True,
        required_text="故事列表",
        notes="Open the story master-detail production view and capture list/detail readiness.",
    ),
    "episode_timeline_smoke": BrowserScenario(
        name="episode_timeline_smoke",
        path="/episodes/{episode_id}/workspace?tab=timeline",
        requires_auth=True,
        required_text="时间轴",
        notes="Open the canonical episode workspace timeline tab and capture readiness.",
    ),
    "episode_script_generation_form_smoke": BrowserScenario(
        name="episode_script_generation_form_smoke",
        path="/episodes/{episode_id}/workspace?tab=script",
        requires_auth=True,
        required_text="生产级异步链路",
        notes="Open the episode script tab and confirm the production async generation controls render.",
    ),
    "episode_workspace_storyboard_smoke": BrowserScenario(
        name="episode_workspace_storyboard_smoke",
        path="/episodes/{episode_id}/workspace?tab=storyboard",
        requires_auth=True,
        required_text="分镜",
        notes="Open the workspace storyboard support view; the legacy direct storyboard route is intentionally not used.",
    ),
    "task_details_trace_smoke": BrowserScenario(
        name="task_details_trace_smoke",
        path="/tasks",
        requires_auth=True,
        required_text="任务",
        notes="Open the task list so run_id/request_id/task_id evidence can be correlated.",
    ),
}


GOLDEN_PATH_SCENARIOS: dict[str, GoldenPathScenario] = {
    "mock_smoke": GoldenPathScenario(
        name="mock_smoke",
        description="Health-check the lite stack and artifact pipeline in mock mode.",
        requires_auth=False,
        notes="Verifies the backend health endpoint and artifact plumbing.",
    ),
    "auth_login_and_me": GoldenPathScenario(
        name="auth_login_and_me",
        description="Authenticate through the API and validate the current operator identity.",
        requires_auth=True,
        notes="Captures request-id and run-id headers across login and /auth/me.",
        legacy_aliases=("operator_smoke",),
    ),
    "task_traceability": GoldenPathScenario(
        name="task_traceability",
        description="List tasks after login and capture headers and task list reachability.",
        requires_auth=True,
        notes="Confirms authenticated task access and request trace headers.",
    ),
    "virtual_ip_image_generation_real_or_mock": GoldenPathScenario(
        name="virtual_ip_image_generation_real_or_mock",
        description="Generate a virtual IP image through the sync API path in real or mock mode.",
        requires_auth=True,
        notes="Uses the configured Virtual IP id and asserts the returned image metadata.",
        requires_virtual_ip_id=True,
    ),
    "episode_timeline_generation": GoldenPathScenario(
        name="episode_timeline_generation",
        description="Queue the timeline pipeline and track the resulting task until completion.",
        requires_auth=True,
        notes="Asserts task creation and completion for the timeline pipeline.",
        requires_script_id=True,
    ),
    "timeline_export_end_to_end": GoldenPathScenario(
        name="timeline_export_end_to_end",
        description="Queue the timeline pipeline and require a persisted result reference at completion.",
        requires_auth=True,
        notes="Treats missing result references as a contract failure, even if the task completed.",
        requires_script_id=True,
        legacy_aliases=("timeline_export_regression",),
    ),
}


for scenario in list(GOLDEN_PATH_SCENARIOS.values()):
    for alias in scenario.legacy_aliases:
        GOLDEN_PATH_SCENARIOS[alias] = scenario
