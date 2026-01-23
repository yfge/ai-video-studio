"""
剧本评分与投流素材服务模块

提供 HookScore/ScriptScore 评分功能，用于评估短剧剧本的投流效果与制作可行性。
提供 TrafficSheet 生成功能，从剧本中提炼 15/30/60 秒投流素材。
"""

from .script_score_service import ScriptScoreService, score_script_from_db
from .traffic_sheet_service import TrafficSheetService, generate_traffic_sheet_from_db

__all__ = [
    "ScriptScoreService",
    "score_script_from_db",
    "TrafficSheetService",
    "generate_traffic_sheet_from_db",
]
