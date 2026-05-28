"""Scene conflict checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_VAGUE_CONFLICT_PHRASES = (
    "推进剧情",
    "推动剧情",
    "剧情继续",
    "故事继续",
    "制造悬念",
    "留下悬念",
    "制造冲突",
    "推动冲突",
    "升级冲突",
    "出现转折",
    "发生反转",
    "完成转折",
    "关系变化",
    "情绪变化",
)

_STAKES_MARKERS = (
    "秒",
    "分钟",
    "小时",
    "倒计时",
    "清零",
    "归零",
    "丢失",
    "删除",
    "永久",
    "奖金",
    "合同",
    "客户",
    "验收",
    "发布",
    "上线",
    "证据",
    "文件",
    "日志",
    "权限",
    "资产",
    "视频",
    "音频",
    "订单",
    "账单",
    "扣款",
    "赔偿",
    "余额",
    "报警",
    "警报",
    "停机",
    "封禁",
    "锁定",
)

_OPPOSITION_MARKERS = (
    "系统",
    "权限",
    "黑影",
    "客户",
    "队友",
    "供应商",
    "后台",
    "审核",
    "日志",
    "控制台",
    "倒计时",
    "警报",
    "锁",
    "拒绝",
    "删除",
    "篡改",
    "封禁",
    "屏幕",
    "文件",
    "接口",
    "回调",
    "账单",
    "模型",
    "资产",
    "老板",
    "审片员",
    "内鬼",
)


def conflict_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        if not _is_specific_text(_scene_field(scene, "question")):
            failed.append("scene_conflict_question")
        if not _has_marker(_scene_field(scene, "stakes"), _STAKES_MARKERS):
            failed.append("scene_conflict_stakes")
        if not _has_marker(_scene_field(scene, "opposition"), _OPPOSITION_MARKERS):
            failed.append("scene_conflict_opposition")
        if not _is_specific_text(_scene_field(scene, "turn")):
            failed.append("scene_conflict_turn")
    return failed


def _scene_field(scene: dict[str, Any], field: str) -> str:
    value = scene.get(field)
    if value:
        return str(value)
    conflict = scene.get("conflict")
    if isinstance(conflict, dict):
        return str(conflict.get(field) or "")
    return ""


def _is_specific_text(value: str) -> bool:
    text = _compact_text(value)
    if len(text) < 4:
        return False
    return not any(phrase in text for phrase in _VAGUE_CONFLICT_PHRASES)


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def _has_marker(text: str, markers: tuple[str, ...]) -> bool:
    compacted = _compact_text(text)
    return any(marker in compacted for marker in markers)
