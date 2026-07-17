from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasPlanNode,
    ProductionCanvasSkillResult,
)

from .planner_ports import canvas_skill_node_id, canvas_skill_ports

NODE_LAYOUT = {
    "brief.compose": (80, 360, 210, None, None),
    "content.plan": (340, 360, 240, None, None),
    "asset.select": (620, 360, 240, "/virtual-ip", "检查资产选择"),
    "virtual_ip.image": (900, 360, 240, "/tasks", "查看 IP 图任务"),
    "environment.image": (1180, 360, 240, "/tasks", "查看环境图任务"),
    "script.generate": (1460, 360, 240, "/stories", "进入故事生产"),
    "timeline.assemble": (1740, 360, 250, "/tasks", "查看时间线任务"),
    "storyboard.plan": (2030, 360, 240, "/tasks", "查看分镜任务"),
    "image.candidates": (2310, 360, 250, "/tasks", "查看图片任务"),
    "video.candidates": (2600, 360, 250, "/tasks", "查看视频任务"),
    "timeline.render": (2890, 360, 240, "/stories", "查看渲染状态"),
    "timeline.export": (3170, 360, 240, "/stories", "查看成片资产"),
    "report.summarize": (3450, 360, 240, "/tasks", "查看报告证据"),
}


def build_plan_nodes(
    skill_results: list[ProductionCanvasSkillResult],
) -> list[ProductionCanvasPlanNode]:
    nodes: list[ProductionCanvasPlanNode] = []
    compact = len(skill_results) < len(NODE_LAYOUT)
    for index, result in enumerate(skill_results):
        default_x = 80 + index * 280
        x, y, width, action_href, action_label = NODE_LAYOUT.get(
            result.skill,
            (default_x, 360, 240, None, None),
        )
        input_ports, output_ports = canvas_skill_ports(result.skill)
        nodes.append(
            ProductionCanvasPlanNode(
                id=canvas_skill_node_id(result.skill),
                label=result.label,
                title=result.title,
                status=result.status,
                x=default_x if compact else x,
                y=y,
                width=width,
                skill=result.skill,
                detail=result.detail,
                outputs=result.outputs,
                reuse_targets=result.reuse_targets,
                action_href=action_href,
                action_label=action_label,
                input_ports=input_ports,
                output_ports=output_ports,
            )
        )
    return nodes
