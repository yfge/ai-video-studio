"""Integration tests for readiness check API endpoints."""

import pytest

from app.models.script import Episode, Story, StoryCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage


def _create_user(db_session, *, username: str = "test_user") -> User:
    """Create a test user."""
    user = db_session.query(User).filter(User.username == username).first()
    if user:
        return user

    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_virtual_ip(db_session, user: User, *, has_image: bool = True) -> VirtualIP:
    """Create a VirtualIP with optional image."""
    vip = VirtualIP(
        name="Test Character",
        description="A test character",
        user_id=user.id,
        is_active=True,
    )
    db_session.add(vip)
    db_session.commit()
    db_session.refresh(vip)

    if has_image:
        image = VirtualIPImage(
            virtual_ip_id=vip.id,
            filename="test.png",
            original_filename="test.png",
            file_path="/images/test.png",
            file_size=1024,
            mime_type="image/png",
            category="avatar",
        )
        db_session.add(image)
        db_session.commit()

    return vip


def _create_story(
    db_session,
    user: User,
    *,
    title: str = "Test Story",
    genre: str = "Drama",
    story_format: str = "tv_series",
    synopsis: str = "A" * 60,
    main_conflict: str = "Main conflict",
    setting_time: str = "Present",
) -> Story:
    """Create a test story."""
    story = Story(
        title=title,
        genre=genre,
        story_format=story_format,
        synopsis=synopsis,
        main_conflict=main_conflict,
        setting_time=setting_time,
        user_id=user.id,
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)
    return story


def _create_story_character(
    db_session, story: Story, vip: VirtualIP
) -> StoryCharacter:
    """Link a VirtualIP to a story as a character."""
    char = StoryCharacter(
        story_id=story.id,
        virtual_ip_id=vip.id,
        character_name="Test Character",
        role_type="protagonist",
    )
    db_session.add(char)
    db_session.commit()
    db_session.refresh(char)
    return char


def _create_episode(
    db_session, story: Story, *, episode_number: int = 1, title: str = "Episode 1"
) -> Episode:
    """Create a test episode."""
    episode = Episode(
        story_id=story.id,
        episode_number=episode_number,
        title=title,
    )
    db_session.add(episode)
    db_session.commit()
    db_session.refresh(episode)
    return episode


class TestStoryReadinessEndpoint:
    """Tests for POST /stories/{story_id}/readiness-check."""

    def test_story_readiness_all_pass(self, client, db_session):
        """Test readiness check passes for a fully configured story."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        story = _create_story(db_session, user)
        _create_story_character(db_session, story, vip)

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["can_proceed"] is True
        assert data["story_id"] == story.id
        assert data["episode_id"] is None

    def test_story_readiness_missing_title(self, client, db_session):
        """Test readiness check fails for missing title."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story = _create_story(db_session, user, title="")

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is False
        assert data["can_proceed"] is False

        title_check = next(c for c in data["checks"] if c["name"] == "title_present")
        assert title_check["passed"] is False
        assert title_check["severity"] == "CRITICAL"

    def test_story_readiness_no_characters(self, client, db_session):
        """Test readiness check fails when no characters linked."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story = _create_story(db_session, user)

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()
        assert data["can_proceed"] is False

        char_check = next(c for c in data["checks"] if c["name"] == "has_characters")
        assert char_check["passed"] is False
        assert char_check["severity"] == "CRITICAL"

    def test_story_readiness_character_without_image(self, client, db_session):
        """Test readiness warns when VirtualIP has no images."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=False)
        story = _create_story(db_session, user)
        _create_story_character(db_session, story, vip)

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()
        # can_proceed but not ready
        assert data["can_proceed"] is True
        assert data["ready"] is False

        portrait_check = next(
            c for c in data["checks"] if c["name"] == "virtual_ip_has_portrait"
        )
        assert portrait_check["passed"] is False
        assert portrait_check["severity"] == "ERROR"

    def test_story_readiness_short_synopsis(self, client, db_session):
        """Test readiness warns on short synopsis."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        story = _create_story(db_session, user, synopsis="Too short")
        _create_story_character(db_session, story, vip)

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()

        synopsis_check = next(
            c for c in data["checks"] if c["name"] == "synopsis_present"
        )
        assert synopsis_check["passed"] is False
        assert synopsis_check["severity"] == "ERROR"

    def test_story_not_found(self, client, db_session):
        """Test 404 for non-existent story."""
        response = client.post("/api/v1/stories/99999/readiness-check")
        assert response.status_code == 404


class TestEpisodeReadinessEndpoint:
    """Tests for POST /stories/{story_id}/episodes/{episode_id}/readiness-check."""

    def test_episode_readiness_all_pass(self, client, db_session):
        """Test readiness check passes for a fully configured episode."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        story = _create_story(db_session, user)
        _create_story_character(db_session, story, vip)
        episode = _create_episode(db_session, story)

        response = client.post(
            f"/api/v1/stories/{story.id}/episodes/{episode.id}/readiness-check"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["can_proceed"] is True
        assert data["story_id"] == story.id
        assert data["episode_id"] == episode.id

    def test_episode_readiness_includes_story_checks(self, client, db_session):
        """Test episode readiness includes story-level checks."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story = _create_story(db_session, user, title="")
        episode = _create_episode(db_session, story)

        response = client.post(
            f"/api/v1/stories/{story.id}/episodes/{episode.id}/readiness-check"
        )

        assert response.status_code == 200
        data = response.json()

        # Should have story check
        check_names = [c["name"] for c in data["checks"]]
        assert "title_present" in check_names

        # Should have episode check
        assert "episode_exists" in check_names

    def test_episode_readiness_episode_exists(self, client, db_session):
        """Test episode_exists check passes for valid episode."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        story = _create_story(db_session, user)
        _create_story_character(db_session, story, vip)
        episode = _create_episode(db_session, story)

        response = client.post(
            f"/api/v1/stories/{story.id}/episodes/{episode.id}/readiness-check"
        )

        assert response.status_code == 200
        data = response.json()

        exists_check = next(c for c in data["checks"] if c["name"] == "episode_exists")
        assert exists_check["passed"] is True
        assert "Episode #1" in exists_check["message"]

    def test_episode_not_found(self, client, db_session):
        """Test 404 for non-existent episode."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story = _create_story(db_session, user)

        response = client.post(
            f"/api/v1/stories/{story.id}/episodes/99999/readiness-check"
        )
        assert response.status_code == 404

    def test_episode_story_mismatch(self, client, db_session):
        """Test 404 when episode doesn't belong to story."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story1 = _create_story(db_session, user, title="Story 1")
        story2 = _create_story(db_session, user, title="Story 2")
        episode = _create_episode(db_session, story2)

        response = client.post(
            f"/api/v1/stories/{story1.id}/episodes/{episode.id}/readiness-check"
        )
        assert response.status_code == 404


class TestReadinessResultFormat:
    """Tests for ReadinessResult response format."""

    def test_result_has_computed_properties(self, client, db_session):
        """Test that computed properties are included in response."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story = _create_story(db_session, user, title="")  # Will have critical failure

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()

        # Computed fields should be present
        assert "critical_issues" in data
        assert "errors" in data
        assert "warnings" in data
        assert "failed_count" in data
        assert "passed_count" in data

        # Critical issues should contain the failed check
        assert len(data["critical_issues"]) > 0

    def test_summary_describes_issues(self, client, db_session):
        """Test that summary contains useful information."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        story = _create_story(db_session, user)  # No characters = critical

        response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert "critical" in data["summary"].lower() or "not ready" in data["summary"].lower()


class TestQuickFixEndpoint:
    """Tests for POST /stories/{story_id}/quick-fix."""

    def test_quick_fix_dry_run(self, client, db_session, monkeypatch):
        """Test quick-fix dry run mode."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        story = _create_story(
            db_session,
            user,
            synopsis="",  # Missing synopsis
            main_conflict="",  # Missing conflict
            setting_time="",  # Missing setting
        )
        _create_story_character(db_session, story, vip)

        # Mock AI generation
        async def mock_generate_text(*args, **kwargs):
            return "A" * 60  # Long enough for synopsis

        from app.services.readiness import story_quick_fix
        monkeypatch.setattr(
            story_quick_fix.StoryQuickFixService,
            "_generate_text",
            mock_generate_text,
        )

        response = client.post(
            f"/api/v1/stories/{story.id}/quick-fix",
            json={"dry_run": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dry_run"] is True
        assert data["story_id"] == story.id
        assert "fixes_applied" in data
        assert "initial_readiness" in data
        assert "final_readiness" in data
        assert "improvement" in data

    def test_quick_fix_applies_changes(self, client, db_session, monkeypatch):
        """Test quick-fix applies changes when not dry run."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        story = _create_story(
            db_session,
            user,
            synopsis="",
            main_conflict="",
            setting_time="",
        )
        _create_story_character(db_session, story, vip)

        generated_synopsis = "A" * 60

        async def mock_generate_text(self, prompt):
            if "synopsis" in prompt.lower():
                return generated_synopsis
            elif "conflict" in prompt.lower():
                return "Hero vs Villain conflict"
            elif "setting" in prompt.lower():
                return "Present day"
            return "Generated content"

        from app.services.readiness import story_quick_fix
        monkeypatch.setattr(
            story_quick_fix.StoryQuickFixService,
            "_generate_text",
            mock_generate_text,
        )

        response = client.post(
            f"/api/v1/stories/{story.id}/quick-fix",
            json={"dry_run": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dry_run"] is False
        assert len(data["fixes_applied"]) > 0

        # Verify improvement
        improvement = data["improvement"]
        assert improvement["fixed_count"] > 0

    def test_quick_fix_story_not_found(self, client, db_session):
        """Test 404 for non-existent story."""
        response = client.post("/api/v1/stories/99999/quick-fix")
        assert response.status_code == 404

    def test_quick_fix_no_fixes_needed(self, client, db_session):
        """Test quick-fix when no fixes are needed."""
        user = db_session.query(User).filter(User.username == "test_admin").first()
        vip = _create_virtual_ip(db_session, user, has_image=True)
        # Create story with all fields filled
        story = _create_story(
            db_session,
            user,
            synopsis="A" * 60,
            main_conflict="Hero vs villain",
            setting_time="Present day",
        )
        _create_story_character(db_session, story, vip)

        response = client.post(f"/api/v1/stories/{story.id}/quick-fix")

        assert response.status_code == 200
        data = response.json()

        # Should have few or no fixes needed
        # (world_building might still be fixable)
        assert data["improvement"]["fixed_count"] <= 1
