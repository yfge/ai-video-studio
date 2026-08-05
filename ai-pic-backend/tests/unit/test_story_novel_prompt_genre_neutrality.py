from inspect import getsource
from pathlib import Path

from app.prompts.manager import prompt_manager
from app.services.narrative_memory import evidence_repair, extraction_prompt
from app.services.story import (
    story_novel_adaptation_prompt,
    story_novel_ai_prompts,
    story_novel_canon_repair,
    story_novel_knowledge_prompt,
    story_novel_plan_repair,
    story_novel_plan_semantic_prompt,
    story_novel_planning_prompt,
    story_novel_state_evidence_repair,
    story_novel_state_extraction_prompt,
    story_novel_state_prompt,
    story_novel_thread_schedule,
    story_novel_thread_schedule_repair,
    story_novel_v3_prompts,
    story_seed_thread_contract,
    story_seed_thread_repair,
)
from app.services.story.story_novel_prompt_renderer import V3_PROMPT_TEMPLATES_V3

_TOPIC_SPECIFIC_TERMS = (
    "农业",
    "农业观察",
    "种田",
    "务农",
    "农活",
    "农事",
    "开荒",
    "田地",
    "耕地",
    "庄稼",
    "作物",
    "种植",
    "播种",
    "收割",
    "施肥",
    "灌溉",
    "粮食",
    "粮仓",
    "谷种",
    "农具",
    "穿越",
    "轻穿越",
    "现代经验",
    "现代知识",
    "外挂",
    "金手指",
    "男女主",
    "男主",
    "女主",
    "感情线",
    "恋情",
    "暧昧",
    "告白",
    "最终证据确认",
    "跨桥",
    "工程量",
    "工牌",
    "手机备注",
    "回到公司",
    "化验",
    "施工报告",
    "实验报告",
    "严肃文学",
)


def test_story_novel_prompt_sources_are_genre_neutral():
    template_dir = Path(prompt_manager.prompts_dir)
    violations = {}

    current_names = set(V3_PROMPT_TEMPLATES_V3)
    template_paths = [
        *sorted(template_dir.glob("story_novel_*.txt")),
        template_dir / "story_seed.txt",
    ]
    assert current_names <= {path.stem for path in template_paths}
    for template_path in template_paths:
        source = template_path.read_text(encoding="utf-8")
        matches = [term for term in _TOPIC_SPECIFIC_TERMS if term in source]
        if matches:
            violations[template_path.stem] = matches

    service_root = Path(__file__).parents[2] / "app" / "services"
    dynamic_paths = [
        *sorted((service_root / "story").glob("story_novel*.py")),
        *sorted((service_root / "story").glob("story_seed*.py")),
        *sorted((service_root / "narrative_memory").glob("*.py")),
    ]
    for source_path in dynamic_paths:
        source = source_path.read_text(encoding="utf-8")
        if "prompt" not in source.lower() and "提示词" not in source:
            continue
        matches = [term for term in _TOPIC_SPECIFIC_TERMS if term in source]
        if matches:
            violations[str(source_path.relative_to(service_root))] = matches

    for module in (
        story_novel_adaptation_prompt,
        story_novel_ai_prompts,
        story_novel_canon_repair,
        story_novel_knowledge_prompt,
        story_novel_plan_repair,
        story_novel_plan_semantic_prompt,
        story_novel_planning_prompt,
        story_novel_state_evidence_repair,
        story_novel_state_extraction_prompt,
        story_novel_state_prompt,
        story_novel_thread_schedule,
        story_novel_thread_schedule_repair,
        story_novel_v3_prompts,
        story_seed_thread_contract,
        story_seed_thread_repair,
        extraction_prompt,
        evidence_repair,
    ):
        source = getsource(module)
        matches = [term for term in _TOPIC_SPECIFIC_TERMS if term in source]
        if matches:
            violations[module.__name__] = matches

    assert violations == {}


def test_v3_writing_prompts_do_not_force_a_domain_process():
    prompts = {
        "story_novel_chapter_brief_v3": prompt_manager.render_prompt(
            "story_novel_chapter_brief_v3", {"brief_input_json": "{}"}
        ),
        "story_novel_chapter_package_v3": prompt_manager.render_prompt(
            "story_novel_chapter_package_v3", {"package_input_json": "{}"}
        ),
        "story_novel_prose_blocks_v3": prompt_manager.render_prompt(
            "story_novel_prose_blocks_v3", {"prose_input_json": "{}"}
        ),
    }

    for prompt in prompts.values():
        assert "农业" not in prompt
        assert "发现—判断—行动—可见结果/代价" not in prompt
    assert "只有当前合同确实涉及" in prompts["story_novel_chapter_brief_v3"]
    assert "不得套用某一领域的固定流程" in prompts["story_novel_prose_blocks_v3"]
