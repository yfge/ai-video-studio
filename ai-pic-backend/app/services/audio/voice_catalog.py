"""
Compatibility export for the shared system voice catalog.

Use ``app.services.voice_catalog`` as the canonical source of truth.
"""

from app.services.voice_catalog import SYSTEM_VOICE_CATALOG

__all__ = ["SYSTEM_VOICE_CATALOG"]
