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


def test_extract_json_block_ignores_trailing_json_examples_inside_code_fence():
    payload = """
```json
{
  "premise": "P",
  "synopsis": "S"
}
只输出严格JSON：{"frames":[...]}
```
"""
    parsed = extract_json_block(payload)
    assert parsed == {"premise": "P", "synopsis": "S"}


def test_extract_json_block_trims_non_json_wrappers():
    payload = 'Result => {"premise": "P", "synopsis": "S"} Thanks!'
    parsed = extract_json_block(payload)
    assert parsed == {"premise": "P", "synopsis": "S"}


def test_extract_json_block_handles_trailing_commas():
    payload = '{"premise": "P", "synopsis": "S",}'
    parsed = extract_json_block(payload)
    assert parsed == {"premise": "P", "synopsis": "S"}


def test_extract_json_block_handles_yaml_payload():
    payload = "premise: P\nsynopsis: S\n"
    parsed = extract_json_block(payload)
    assert parsed == {"premise": "P", "synopsis": "S"}


def test_extract_json_block_reexported_from_story_parser():
    assert story_parser.extract_json_block is extract_json_block
