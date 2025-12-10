from app.utils import story_parser
from app.utils.json_utils import extract_json_block


def test_extract_json_block_handles_code_fence_and_noise():
    payload = """
Here is your outline:
```json
{
    "premise": "A hero learns to rest.",
    "synopsis": "Full outline."
}
```
Extra text that should be ignored.
"""
    parsed = extract_json_block(payload)
    assert parsed == {
        "premise": "A hero learns to rest.",
        "synopsis": "Full outline.",
    }


def test_extract_json_block_trims_non_json_wrappers():
    payload = 'Result => {"premise": "P", "synopsis": "S"} Thanks!'
    parsed = extract_json_block(payload)
    assert parsed == {"premise": "P", "synopsis": "S"}


def test_extract_json_block_reexported_from_story_parser():
    assert story_parser.extract_json_block is extract_json_block
