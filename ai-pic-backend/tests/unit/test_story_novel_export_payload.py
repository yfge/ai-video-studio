from app.models.script import Story, StoryCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.services.story.story_novel_export_payload import build_story_novel_payload


def test_story_novel_payload_includes_virtual_ip_biography(db_session):
    user = User(
        username="payload_admin",
        email="payload_admin@example.com",
        hashed_password="not-used",
        full_name="Payload Admin",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    vip = VirtualIP(
        user_id=user.id,
        name="Test VIP",
        biography="人物小传内容",
        background_story="背景故事内容",
        description="角色描述",
        tags=["tag1"],
    )
    story = Story(title="Test Story", genre="Romance", user_id=user.id)
    db_session.add_all([vip, story])
    db_session.commit()
    db_session.refresh(vip)
    db_session.refresh(story)

    story_character = StoryCharacter(
        story_id=story.id,
        virtual_ip_id=vip.id,
        virtual_ip_business_id=vip.business_id,
        character_name="主角",
        role_type="protagonist",
    )
    db_session.add(story_character)
    db_session.commit()

    payload = build_story_novel_payload(db_session, story=story)
    characters = payload.get("characters")
    assert isinstance(characters, list)
    assert any(
        (item.get("virtual_ip") or {}).get("biography") == "人物小传内容"
        for item in characters
    )
