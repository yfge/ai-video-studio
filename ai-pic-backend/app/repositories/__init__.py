"""
Repository pattern for data access layer.

This package provides base repository classes and concrete implementations
for database access, enabling clean separation between business logic and
data access.

Usage:
    from app.repositories import BaseRepository
    from app.repositories.user_repository import UserRepository
"""

from app.repositories.base import BaseRepository
from app.repositories.virtual_ip_repository import VirtualIPRepository

__all__ = ["BaseRepository", "VirtualIPRepository"]
