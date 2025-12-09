from app.utils.story_parser import extract_json_block


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
