"""Provider stages for v4 intent and prose, both bound to frozen inputs."""

from . import story_novel_block_contract as block_contract
from .story_novel_chapter_intent import parse_chapter_intent
from .story_novel_export_ai import TruncatedNovelOutput
from .story_novel_finish_reason import is_recoverable_length_finish_reason
from .story_novel_prompt_renderer import render_novel_prompt
from .story_novel_v3_generation import _generate_with_format_repair
from .story_novel_v3_truncation import recover_truncated_prose


async def generate_chapter_intent(
    revision, position, snapshot, generate_text, *, before_call=None
):
    prompt = render_novel_prompt(
        "story_novel_chapter_intent_v4",
        planner_input_json=_json(snapshot["model_input"]),
    )
    return await _generate_with_format_repair(
        revision,
        prompt,
        lambda text: parse_chapter_intent(text, snapshot),
        generate_text,
        stage=f"chapter_planning.{position}",
        max_tokens=12_000,
        format_repair_max_tokens=8_000,
        before_call=before_call,
    )


async def generate_prose_blocks_v4(
    revision, position, prose_input, expected_count, generate_text, *, before_call=None
):
    prompt = prose_blocks_v4_prompt(prose_input)

    def parse(text):
        blocks = block_contract.parse_prose_block_response(text, expected_count)
        return {
            "block_contents": blocks,
            **block_contract.assemble_prose_blocks(blocks),
        }

    try:
        return await _generate_with_format_repair(
            revision,
            prompt,
            parse,
            generate_text,
            stage=f"prose.{position}",
            max_tokens=block_contract.prose_token_budget(prose_input),
            before_call=before_call,
        )
    except TruncatedNovelOutput as exc:
        if not is_recoverable_length_finish_reason(exc.finish_reason):
            raise
        return await recover_truncated_prose(
            revision,
            position,
            prose_input,
            expected_count,
            prompt,
            exc,
            generate_text,
            block_contract.prose_token_budget(prose_input),
            before_call=before_call,
        )


def _json(value: dict) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def prose_blocks_v4_prompt(prose_input: dict):
    return render_novel_prompt(
        "story_novel_prose_blocks_v4", prose_input_json=_json(prose_input)
    )
