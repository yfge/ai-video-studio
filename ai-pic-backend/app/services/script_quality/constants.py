from __future__ import annotations

import re
from dataclasses import dataclass

DIALOGUE_RE = re.compile(
    r"^([\u4e00-\u9fa5A-Z][\u4e00-\u9fa5A-Z\s]{0,20})[：:]\s*(.+)$"
)
SCENE_HEADER_RE = re.compile(
    r"(^\\[第?\\d+场\\])|(^场景\\s*\\d+)|(^Scene\\s*\\d+)|(^INT\\.|^EXT\\.)",
    re.I,
)
TAG_RE = re.compile(r"【([^】]+)】")


@dataclass(frozen=True)
class PhraseRule:
    phrase: str
    severity: str
    suggestion: str


# “不可拍”/“不可直接拍摄”的常见表述（仅对非对白行做提示）
UNFILMABLE_PHRASES: list[PhraseRule] = [
    PhraseRule(
        "他感到", "error", "改为可拍动作：低头、手抠衣角、呼吸急促、眼眶发红等。"
    ),
    PhraseRule("她感到", "error", "改为可拍动作：后退半步、手指发抖、强撑微笑等。"),
    PhraseRule("感到", "warn", "避免心理描写，改为镜头可见的动作/表情/环境变化。"),
    PhraseRule("觉得", "warn", "避免主观判断，改为镜头可见的动作/物理反馈。"),
    PhraseRule("气氛", "error", "改为可拍信号：灯光忽灭、风吹倒物体、远处警笛等。"),
    PhraseRule("氛围", "warn", "改为可拍信号：光影、环境音、道具变化。"),
    PhraseRule("关系破裂", "error", "改为可拍构图：两人左右两端、背对背、拒绝对视等。"),
    PhraseRule("两人关系", "warn", "改为具体动作与空间关系，不要抽象描述关系。"),
    PhraseRule("悲伤", "warn", "改为可拍动作：眼眶发红、吞咽、手指抠紧等。"),
    PhraseRule("愤怒", "warn", "改为可拍动作：咬牙、拳头攥紧、杯子震动等。"),
    PhraseRule("压抑", "warn", "改为可拍信号：沉闷低频声、灯光闪烁、空间逼仄构图。"),
]


TEMPO_TAGS = ("快", "慢", "加速区", "减速区")
EMOTION_TAG_KEYWORDS = ("情绪目的", "情绪目标")
SFX_TAG_KEYWORDS = ("音效", "氛围音", "环境音")

HOOK_MARKERS = ("【音效】", "（音效", "(音效", "啪", "砰", "咚", "！", "?", "？")

UNIMPLEMENTED_CHECKS = [
    "动作四段式（起势→过程→落点/物理反馈→反应）",
    "平行任务（对话时手上必须有事做）",
    "场景极性反转（The Turn）与三重障碍递增",
    "第三演员道具（通过物体传递关系）",
    "同框过渡与转场逻辑标签（声音/动作/匹配）",
]
