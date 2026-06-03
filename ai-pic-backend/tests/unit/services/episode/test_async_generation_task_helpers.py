import json

from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.episode.async_generation_task_helpers import build_marketing_overrides


def test_build_marketing_overrides_returns_json_serializable_payloads():
    request = EpisodeGenerationRequest.model_validate(
        {
            "story_id": 48,
            "episode_count": 10,
            "episode_duration": 3,
            "market_region": "US",
            "micro_genre": "revenge romance",
            "hook_plan": {
                "opening_hook": "A public betrayal opens the first episode.",
                "key_reversals": [
                    {
                        "beat_type": "reversal",
                        "description": "The enemy is secretly an ally.",
                        "timing": "midpoint",
                        "intensity": "high",
                    }
                ],
            },
            "twist_density": "high",
            "cliffhanger_plan": ["Episode 1 ends on a reveal."],
            "ad_snippets": [
                {
                    "duration_seconds": 15,
                    "hook": "She returns with proof.",
                    "visual_summary": "A contract lands on the banquet table.",
                    "call_to_action": "Watch her revenge begin.",
                }
            ],
        }
    )

    overrides = build_marketing_overrides(request)

    assert isinstance(overrides["hook_plan"], dict)
    assert isinstance(overrides["ad_snippets"][0], dict)
    json.dumps(overrides, ensure_ascii=False)
