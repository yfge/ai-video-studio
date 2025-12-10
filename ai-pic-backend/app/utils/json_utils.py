import json
import re
from typing import Any, Dict


def extract_json_block(payload: str | None) -> Dict[str, Any] | None:
    """
    尝试从包含 Markdown 代码块或额外文字的字符串中提取 JSON 对象。
    优先处理 ```json ... ``` 包裹的内容，再回退到首尾花括号截取。
    """
    if not payload:
        return None

    text = payload.strip()

    # 去掉 ```json ... ``` 或 ``` ... ``` 包裹
    fence_match = re.search(r"```[a-zA-Z]*\s*(.*?)\s*```", text, flags=re.S)
    if fence_match:
        text = fence_match.group(1).strip()

    # 如果不以 { 开头，尝试截取第一个 JSON 对象
    if not text.lstrip().startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    try:
        return json.loads(text)
    except Exception:
        return None
