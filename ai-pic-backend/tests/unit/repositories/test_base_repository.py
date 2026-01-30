"""
Tests for base repository pattern.
"""

import pytest
from app.core.exceptions import NotFoundError
from app.models.base import SoftDeleteBusinessMixin
from app.repositories.base import BaseRepository
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create test base and engine
Base = declarative_base()


class TestModel(Base, SoftDeleteBusinessMixin):
    """Test model for repository tests."""

    __tablename__ = "test_model"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)


@pytest.fixture(scope="function")
def session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repo(session):
    """Create test repository."""
    return BaseRepository(TestModel, session)


class TestBaseRepositoryCreate:
    """Test create operations."""

    def test_create(self, repo, session):
        """Test creating new entity."""
        entity = repo.create(name="Test", email="test@example.com")
        session.commit()

        assert entity.id is not None
        assert entity.name == "Test"
        assert entity.email == "test@example.com"
        assert entity.is_active is True


class TestBaseRepositoryRead:
    """Test read operations."""

    @pytest.fixture
    def sample_data(self, repo, session):
        """Create sample data for read tests."""
        repo.create(name="Alice", email="alice@example.com", is_active=True)
        repo.create(name="Bob", email="bob@example.com", is_active=False)
        repo.create(name="Charlie", email="charlie@example.com", is_active=True)
        session.commit()

    def test_get_by_id(self, repo, session, sample_data):
        """Test getting entity by ID."""
        entity = repo.get_by_id(1)
        assert entity is not None
        assert entity.name == "Alice"

    def test_get_by_id_not_found(self, repo, sample_data):
        """Test getting non-existent entity returns None."""
        entity = repo.get_by_id(999)
        assert entity is None

    def test_get_by_id_or_fail(self, repo, sample_data):
        """Test getting entity by ID or raising error."""
        entity = repo.get_by_id_or_fail(1)
        assert entity.name == "Alice"

    def test_get_by_id_or_fail_not_found(self, repo, sample_data):
        """Test get_by_id_or_fail raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            repo.get_by_id_or_fail(999)
        assert exc_info.value.status_code == 404

    def test_get_by(self, repo, sample_data):
        """Test getting entity by filter."""
        entity = repo.get_by(email="bob@example.com")
        assert entity is not None
        assert entity.name == "Bob"

    def test_get_by_not_found(self, repo, sample_data):
        """Test get_by returns None when not found."""
        entity = repo.get_by(email="nonexistent@example.com")
        assert entity is None

    def test_list_by(self, repo, sample_data):
        """Test listing entities by filter."""
        entities = repo.list_by(is_active=True)
        assert len(entities) == 2
        names = [e.name for e in entities]
        assert "Alice" in names
        assert "Charlie" in names

    def test_list_all(self, repo, sample_data):
        """Test listing all entities."""
        entities = repo.list_all()
        assert len(entities) == 3

    def test_list_all_with_pagination(self, repo, sample_data):
        """Test listing with limit and offset."""
        entities = repo.list_all(limit=2, offset=1)
        assert len(entities) == 2

    def test_count(self, repo, sample_data):
        """Test counting entities."""
        total = repo.count()
        assert total == 3

        active_count = repo.count(is_active=True)
        assert active_count == 2

    def test_exists(self, repo, sample_data):
        """Test checking entity existence."""
        assert repo.exists(email="alice@example.com") is True
        assert repo.exists(email="nonexistent@example.com") is False


class TestBaseRepositoryUpdate:
    """Test update operations."""

    @pytest.fixture
    def sample_entity(self, repo, session):
        """Create sample entity for update tests."""
        entity = repo.create(name="Test", email="test@example.com")
        session.commit()
        return entity

    def test_update(self, repo, session, sample_entity):
        """Test updating entity."""
        repo.update(sample_entity, name="Updated")
        session.commit()

        updated = repo.get_by_id(sample_entity.id)
        assert updated.name == "Updated"
        assert updated.email == "test@example.com"

    def test_update_by_id(self, repo, session, sample_entity):
        """Test updating entity by ID."""
        repo.update_by_id(sample_entity.id, email="new@example.com")
        session.commit()

        updated = repo.get_by_id(sample_entity.id)
        assert updated.email == "new@example.com"

    def test_update_by_id_not_found(self, repo):
        """Test update_by_id raises error for non-existent entity."""
        with pytest.raises(NotFoundError):
            repo.update_by_id(999, name="Test")


class TestBaseRepositoryDelete:
    """Test delete operations."""

    @pytest.fixture
    def sample_entity(self, repo, session):
        """Create sample entity for delete tests."""
        entity = repo.create(name="Test", email="test@example.com")
        session.commit()
        return entity

    def test_delete(self, repo, session, sample_entity):
        """Test hard deleting entity."""
        entity_id = sample_entity.id
        repo.delete(sample_entity)
        session.commit()

        deleted = repo.get_by_id(entity_id)
        assert deleted is None

    def test_delete_by_id(self, repo, session, sample_entity):
        """Test hard deleting entity by ID."""
        entity_id = sample_entity.id
        repo.delete_by_id(entity_id)
        session.commit()

        deleted = repo.get_by_id(entity_id)
        assert deleted is None

    def test_soft_delete(self, repo, session, sample_entity):
        """Test soft deleting entity."""
        repo.soft_delete(sample_entity, user_id=123, reason="Test deletion")
        session.commit()

        entity = repo.get_by_id(sample_entity.id)
        assert entity is not None  # Still in database
        assert entity.is_deleted is True
        assert entity.deleted_by == 123
        assert entity.deleted_reason == "Test deletion"

    def test_soft_delete_by_id(self, repo, session, sample_entity):
        """Test soft deleting entity by ID."""
        entity_id = sample_entity.id
        repo.soft_delete_by_id(entity_id, user_id=456)
        session.commit()

        entity = repo.get_by_id(entity_id)
        assert entity.is_deleted is True
        assert entity.deleted_by == 456


class TestBaseRepositoryTransactions:
    """Test transaction management."""

    def test_commit(self, repo, session):
        """Test committing changes."""
        entity = repo.create(name="Test")
        repo.commit()

        # Verify persisted
        assert repo.get_by_id(entity.id) is not None

    def test_rollback(self, repo, session):
        """Test rolling back changes."""
        entity = repo.create(name="Test")
        entity_id = entity.id
        repo.rollback()

        # Verify not persisted
        assert repo.get_by_id(entity_id) is None

    def test_refresh(self, repo, session):
        """Test refreshing entity from database."""
        entity = repo.create(name="Original")
        session.commit()

        # Modify without updating DB
        entity.name = "Modified"

        # Refresh should revert to DB value
        repo.refresh(entity)
        assert entity.name == "Original"
