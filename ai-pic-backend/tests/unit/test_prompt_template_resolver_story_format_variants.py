from app.prompts.manager import PromptManager
from app.prompts.template_resolver import resolve_template_name


def test_resolve_template_name_picks_short_drama_variant_when_available():
    prompts_dir = PromptManager().prompts_dir

    assert (
        resolve_template_name(
            "script_dialogues",
            {"story": {"story_format": "short_drama"}},
            prompts_dir,
        )
        == "script_dialogues_short_drama"
    )
    assert (
        resolve_template_name(
            "script_scenes",
            {"story": {"story_format": "short_drama"}},
            prompts_dir,
        )
        == "script_scenes_short_drama"
    )
    assert (
        resolve_template_name(
            "script_beats",
            {"story": {"story_format": "short_drama"}},
            prompts_dir,
        )
        == "script_beats_short_drama"
    )
    assert (
        resolve_template_name(
            "system_prompt_story",
            {"story_format": "short_drama"},
            prompts_dir,
        )
        == "system_prompt_story_short_drama"
    )
    assert (
        resolve_template_name(
            "system_prompt_script",
            {"story_format": "short_drama"},
            prompts_dir,
        )
        == "system_prompt_script_short_drama"
    )


def test_resolve_template_name_falls_back_when_variant_missing():
    prompts_dir = PromptManager().prompts_dir

    assert (
        resolve_template_name(
            "script_dialogues",
            {"story": {"story_format": "tv_series"}},
            prompts_dir,
        )
        == "script_dialogues"
    )
