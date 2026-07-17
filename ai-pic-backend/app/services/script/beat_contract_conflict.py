from __future__ import annotations

import re
from typing import Any

from app.services.script.beat_contract_specificity import is_specific_text

_DEADLINE_PATTERN = re.compile(
    r"(?:\d+\s*(?:秒|分钟|小时|天|周|月)|今天|明天|后天|本周|下周|本月|下月|月底|年底)"
)

_STAKES_MARKERS = (
    "秒",
    "分钟",
    "小时",
    "倒计时",
    "清零",
    "归零",
    "丢失",
    "失去",
    "删除",
    "永久",
    "生命",
    "死亡",
    "受伤",
    "自由",
    "身份",
    "名誉",
    "关系",
    "机会",
    "目标",
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
    "公开",
    "播放",
    "传播",
    "复制",
    "写入",
    "回传",
    "占用",
    "模板",
    "样本",
    "底稿",
    "署名",
)

_OPPOSITION_MARKERS = (
    "系统",
    "权限",
    "规则",
    "黑影",
    "对手",
    "人物",
    "家人",
    "时间",
    "距离",
    "天气",
    "道路",
    "门",
    "关键物件",
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
    "会议屏",
    "大屏",
    "连屏",
    "工作群",
    "提示窗",
    "侧栏",
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


def conflict_issues(scene: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    conflict = scene.conflict

    if not conflict.question.strip() or not is_specific_text(conflict.question):
        issues.append(
            {
                "check_id": "scene_conflict_question",
                "message": "scene conflict must name a concrete dramatic question",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"question": conflict.question},
            }
        )

    if not conflict.stakes.strip() or not conflict.opposition.strip():
        issues.append(
            {
                "check_id": "scene_conflict",
                "message": "scene conflict must name stakes and opposition",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {
                    "stakes": conflict.stakes,
                    "opposition": conflict.opposition,
                },
            }
        )
    elif not is_specific_text(conflict.stakes) or not is_specific_text(
        conflict.opposition
    ):
        issues.append(
            {
                "check_id": "scene_conflict_specificity",
                "message": "scene conflict must include concrete stakes and opposition",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {
                    "stakes": conflict.stakes,
                    "opposition": conflict.opposition,
                },
            }
        )

    if conflict.stakes.strip() and not has_concrete_stakes(conflict.stakes):
        issues.append(
            {
                "check_id": "scene_conflict_stakes",
                "message": "scene stakes must name a concrete loss or deadline",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"stakes": conflict.stakes},
            }
        )
    if conflict.opposition.strip() and not _has_marker(
        conflict.opposition, _OPPOSITION_MARKERS
    ):
        issues.append(
            {
                "check_id": "scene_conflict_opposition",
                "message": "scene opposition must name a concrete blocking source",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"opposition": conflict.opposition},
            }
        )

    turn = conflict.turn or ""
    if not turn.strip() or not is_specific_text(turn):
        issues.append(
            {
                "check_id": "scene_conflict_turn",
                "message": "scene conflict must name a concrete turn",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"turn": conflict.turn},
            }
        )

    return issues


def _has_marker(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def has_concrete_stakes(text: str) -> bool:
    return bool(_DEADLINE_PATTERN.search(text)) or _has_marker(text, _STAKES_MARKERS)


def has_concrete_opposition(text: str) -> bool:
    return _has_marker(text, _OPPOSITION_MARKERS)
