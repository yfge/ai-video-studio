import re
from typing import Any, Dict, List


def extract_script_structure(content: str) -> Dict[str, Any]:
    """
    从纯文本剧本中尽力抽取结构化信息（场景、对话、舞台指示）。
    这是启发式提取，不依赖AI，适合作为JSON失败时的兜底。
    """
    scenes: List[Dict[str, Any]] = []
    dialogues: List[Dict[str, Any]] = []
    stage_directions: List[Dict[str, Any]] = []

    lines = [ln.strip() for ln in content.splitlines()]

    # 场景识别规则
    scene_patterns = [
        re.compile(r"^(场景|Scene)\s*([0-9０-９一二三四五六七八九十]+)[：:、. ]?(.*)$", re.I),
        re.compile(r"^(INT\.|EXT\.|INT/EXT\.)\s*(.+)$", re.I),
        re.compile(r"^(内景|外景)[：: .、，]?\s*(.+)$"),
    ]

    # 对话识别：例如 “小雅：……”，或 “LI MING: …”
    dialogue_pattern = re.compile(r"^([\u4e00-\u9fa5A-Z][\u4e00-\u9fa5A-Z\s]{0,20})[：:]\s*(.+)$")

    # 舞台指示：括号/方括号/以“动作：/旁白：/音效：/音乐：”开头
    stage_patterns = [
        re.compile(r"^[（(\[](.+)[)）\]]$"),
        re.compile(r"^(动作|旁白|音效|音乐|环境|镜头|效果)[：:]\s*(.+)$"),
    ]

    current_scene_idx = 0

    for ln in lines:
        if not ln:
            continue

        # 1) 场景
        matched_scene = None
        for pat in scene_patterns:
            m = pat.match(ln)
            if m:
                matched_scene = m
                break
        if matched_scene:
            current_scene_idx += 1
            # 提取location/time尽力而为
            location = ""
            time_hint = ""
            if len(matched_scene.groups()) >= 1:
                tail = matched_scene.group(len(matched_scene.groups())) or ""
                # 提取常见时间标记
                if any(t in tail for t in ["日", "白天", "早上", "上午", "中午", "下午", "夜", "晚上", "傍晚", "黄昏"]):
                    time_hint = "夜" if ("夜" in tail or "晚上" in tail) else "日"
                location = tail.strip()

            scenes.append({
                "scene_number": current_scene_idx,
                "location": location,
                "time": time_hint or None,
                "description": ln,
                "characters": [],
                "props": [],
                "notes": ""
            })
            continue

        # 2) 对话
        dm = dialogue_pattern.match(ln)
        if dm:
            character = dm.group(1).strip()
            text = dm.group(2).strip()
            dialogues.append({
                "scene_number": current_scene_idx or None,
                "character": character,
                "content": text,
                "emotion": None,
                "action": None,
                "notes": None,
            })
            continue

        # 3) 舞台指示
        matched_stage = None
        stage_text = None
        for sp in stage_patterns:
            sm = sp.match(ln)
            if sm:
                matched_stage = sm
                stage_text = sm.group(len(sm.groups())) if sm.groups() else ln
                break
        if matched_stage:
            stage_directions.append({
                "scene_number": current_scene_idx or None,
                "timing": None,
                "content": stage_text.strip() if stage_text else ln,
                "type": None,
            })
            continue

    metadata = {
        "total_scenes": len(scenes),
        "total_dialogues": len(dialogues),
    }

    return {
        "content": content,
        "scenes": scenes,
        "dialogues": dialogues,
        "stage_directions": stage_directions,
        "metadata": metadata,
    }

