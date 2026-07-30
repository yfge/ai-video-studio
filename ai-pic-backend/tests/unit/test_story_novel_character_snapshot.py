from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.services.story.story_novel_domain import build_story_snapshot
from app.services.story.story_novel_planning_service import planning_contract


def test_revision_snapshot_freezes_relational_character_profile():
    story = Story(title="青禾记", genre="种田", story_characters=[])
    profile = VirtualIP(
        name="沈禾",
        description="二十四岁的农学试验员，她擅长盐碱地改良。",
        biography="她离开实验站后回乡承包荒田。",
    )
    character = StoryCharacter(
        business_id="character-1",
        virtual_ip_business_id="vip-1",
        character_name="沈禾",
        role_type="protagonist",
        importance=5,
        personality="克制而坚韧",
    )
    character.virtual_ip = profile
    story.story_characters = [character]

    snapshot = build_story_snapshot(story)
    frozen = planning_contract(snapshot)["characters"][0]

    assert frozen["name"] == "沈禾"
    assert frozen["virtual_ip"]["description"].startswith("二十四岁")
    assert "她离开实验站" in frozen["virtual_ip"]["biography"]
    profile.biography = "后来被修改的档案"
    assert "她离开实验站" in frozen["virtual_ip"]["biography"]
