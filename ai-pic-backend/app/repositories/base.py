"""
Base repository pattern for data access layer.

This module provides abstract base repositories that encapsulate all database
access logic, enabling clean separation between business logic (services) and
data access (repositories).

Usage:
    class UserRepository(BaseRepository[User]):
        pass

    # In service:
    users = await user_repo.list_by(email="test@example.com")
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError

# Type variable for model classes
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing CRUD operations for any model.

    This is a synchronous repository for use with SQLAlchemy ORM.
    For async operations, use AsyncBaseRepository.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages

    Attributes:
        model: The SQLAlchemy model class
        session: Database session

    Example:
        class ScriptRepository(BaseRepository[Script]):
            def find_by_virtual_ip(self, virtual_ip_id: int) -> List[Script]:
                return self.list_by(virtual_ip_id=virtual_ip_id)
    """

    def __init__(self, model: Type[ModelType], session: Session):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get entity by primary key ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_by_id_or_fail(self, id: int, resource_name: Optional[str] = None) -> ModelType:
        """
        Get entity by ID or raise NotFoundError.

        Args:
            id: Primary key value
            resource_name: Resource type name for error message (defaults to model name)

        Returns:
            Model instance

        Raises:
            NotFoundError: If entity not found
        """
        entity = self.get_by_id(id)
        if entity is None:
            name = resource_name or self.model.__name__
            raise NotFoundError(name, id)
        return entity

    def get_by(self, **filters) -> Optional[ModelType]:
        """
        Get first entity matching filters.

        Args:
            **filters: Field name -> value pairs

        Returns:
            Model instance or None if not found

        Example:
            user = repo.get_by(email="test@example.com")
        """
        query = self.session.query(self.model)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.first()

    def list_by(self, **filters) -> List[ModelType]:
        """
        List all entities matching filters.

        Args:
            **filters: Field name -> value pairs

        Returns:
            List of model instances

        Example:
            scripts = repo.list_by(user_id=123, is_deleted=False)
        """
        query = self.session.query(self.model)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.all()

    def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """
        List all entities with pagination.

        Args:
            limit: Maximum number of results (None = no limit)
            offset: Number of results to skip

        Returns:
            List of model instances
        """
        query = self.session.query(self.model).offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def count(self, **filters) -> int:
        """
        Count entities matching filters.

        Args:
            **filters: Field name -> value pairs

        Returns:
            Number of matching entities

        Example:
            total = repo.count(is_deleted=False)
        """
        query = self.session.query(func.count(self.model.id))
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.scalar() or 0

    def exists(self, **filters) -> bool:
        """
        Check if any entity matches filters.

        Args:
            **filters: Field name -> value pairs

        Returns:
            True if at least one match exists

        Example:
            if repo.exists(email="test@example.com"):
                raise DuplicateError("邮箱", email)
        """
        return self.count(**filters) > 0

    def create(self, **data) -> ModelType:
        """
        Create new entity.

        Args:
            **data: Field name -> value pairs

        Returns:
            Created model instance

        Note:
            Does NOT commit. Caller must commit the session.

        Example:
            user = repo.create(username="test", email="test@example.com")
            session.commit()
        """
        entity = self.model(**data)
        self.session.add(entity)
        return entity

    def update(self, entity: ModelType, **data) -> ModelType:
        """
        Update existing entity.

        Args:
            entity: Model instance to update
            **data: Field name -> value pairs

        Returns:
            Updated model instance

        Note:
            Does NOT commit. Caller must commit the session.

        Example:
            user = repo.get_by_id(123)
            repo.update(user, email="new@example.com")
            session.commit()
        """
        for key, value in data.items():
            setattr(entity, key, value)
        return entity

    def update_by_id(self, id: int, **data) -> ModelType:
        """
        Update entity by ID.

        Args:
            id: Primary key value
            **data: Field name -> value pairs

        Returns:
            Updated model instance

        Raises:
            NotFoundError: If entity not found

        Note:
            Does NOT commit. Caller must commit the session.
        """
        entity = self.get_by_id_or_fail(id)
        return self.update(entity, **data)

    def delete(self, entity: ModelType) -> None:
        """
        Hard delete entity.

        Args:
            entity: Model instance to delete

        Note:
            Does NOT commit. Caller must commit the session.
        """
        self.session.delete(entity)

    def delete_by_id(self, id: int) -> None:
        """
        Hard delete entity by ID.

        Args:
            id: Primary key value

        Raises:
            NotFoundError: If entity not found

        Note:
            Does NOT commit. Caller must commit the session.
        """
        entity = self.get_by_id_or_fail(id)
        self.delete(entity)

    def soft_delete(self, entity: ModelType, user_id: Optional[int] = None, reason: Optional[str] = None) -> ModelType:
        """
        Soft delete entity (if model supports it).

        Args:
            entity: Model instance to soft delete
            user_id: ID of user performing deletion
            reason: Reason for deletion

        Returns:
            Soft-deleted model instance

        Raises:
            AttributeError: If model doesn't have soft_delete method

        Note:
            Does NOT commit. Caller must commit the session.
            Requires model to have SoftDeleteBusinessMixin.
        """
        if not hasattr(entity, "soft_delete"):
            raise AttributeError(f"{self.model.__name__} does not support soft delete")
        entity.soft_delete(user_id=user_id, reason=reason)
        return entity

    def soft_delete_by_id(
        self,
        id: int,
        user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> ModelType:
        """
        Soft delete entity by ID.

        Args:
            id: Primary key value
            user_id: ID of user performing deletion
            reason: Reason for deletion

        Returns:
            Soft-deleted model instance

        Raises:
            NotFoundError: If entity not found
            AttributeError: If model doesn't support soft delete

        Note:
            Does NOT commit. Caller must commit the session.
        """
        entity = self.get_by_id_or_fail(id)
        return self.soft_delete(entity, user_id=user_id, reason=reason)

    def refresh(self, entity: ModelType) -> ModelType:
        """
        Refresh entity from database.

        Args:
            entity: Model instance to refresh

        Returns:
            Refreshed model instance
        """
        self.session.refresh(entity)
        return entity

    def commit(self) -> None:
        """
        Commit current session.

        Note:
            Generally, services should handle transaction management.
            This is provided for convenience in simple cases.
        """
        self.session.commit()

    def rollback(self) -> None:
        """
        Rollback current session.

        Note:
            Generally, services should handle transaction management.
            This is provided for convenience in error handling.
        """
        self.session.rollback()
