from __future__ import annotations

import re
from dataclasses import dataclass

NAME = r"[“\"']?(?P<name>[^，,。；;“”\"']{1,64}?)[”\"']?"
IP_PATTERNS = [
    re.compile(
        rf"(?:创建|新建|新增)\s*(?:一个|一名)?\s*(?:名为|叫)?\s*{NAME}"
        r"\s*的\s*(?:虚拟\s*IP|IP|角色|人物|主角)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:创建|新建|新增)\s*(?:一个|一名)?\s*"
        rf"(?:虚拟\s*IP|IP|角色|人物|主角)\s*(?:叫|名为|是)?\s*{NAME}",
        re.IGNORECASE,
    ),
    re.compile(rf"(?:角色|人物|主角|IP)\s*(?:叫|名为|是)\s*{NAME}", re.IGNORECASE),
    re.compile(
        rf"(?:以|基于)\s*{NAME}\s*(?:为主角|做主角|做第\s*\d+\s*集|制作第|生成第)",
        re.IGNORECASE,
    ),
]
ENVIRONMENT_PATTERNS = [
    re.compile(
        rf"(?:创建|新建|新增)\s*(?:一个)?\s*(?:名为|叫)?\s*{NAME}"
        r"\s*的\s*(?:环境|场景)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:创建|新建|新增)\s*(?:一个)?\s*(?:环境|场景)"
        rf"\s*(?:叫|名为|是)?\s*{NAME}",
        re.IGNORECASE,
    ),
    re.compile(rf"(?:环境|场景)\s*(?:叫|名为|是|为)\s*{NAME}", re.IGNORECASE),
    re.compile(rf"(?:以|在)\s*{NAME}\s*(?:为)?(?:环境|场景)", re.IGNORECASE),
]
LOCATION_NAMES = (
    "共享办公区",
    "办公室",
    "会议室",
    "工作室",
    "直播间",
    "咖啡馆",
    "餐厅",
    "酒吧",
    "商场",
    "校园",
    "学校",
    "医院",
    "车站",
    "机场",
    "码头",
    "天台",
    "客厅",
    "卧室",
    "公寓",
    "街道",
    "巷道",
    "海边",
    "森林",
    "城堡",
    "村庄",
    "工厂",
    "仓库",
)


@dataclass(frozen=True)
class CanvasAssetPromptIntent:
    virtual_ip_name: str | None = None
    environment_name: str | None = None


def _clean_name(value: str | None) -> str | None:
    cleaned = (value or "").strip().strip("“”\"' ")
    cleaned = re.sub(r"^(?:一个|一名|名为|叫)", "", cleaned).strip()
    cleaned = re.sub(r"的$", "", cleaned).strip()
    return cleaned[:64] or None


def _match_name(prompt: str, patterns: list[re.Pattern[str]]) -> str | None:
    for pattern in patterns:
        if match := pattern.search(prompt):
            return _clean_name(match.group("name"))
    return None


def parse_canvas_asset_prompt(prompt: str) -> CanvasAssetPromptIntent:
    environment_name = _match_name(prompt, ENVIRONMENT_PATTERNS)
    if environment_name is None:
        environment_name = next(
            (name for name in LOCATION_NAMES if name in prompt), None
        )
    return CanvasAssetPromptIntent(
        virtual_ip_name=_match_name(prompt, IP_PATTERNS),
        environment_name=environment_name,
    )
