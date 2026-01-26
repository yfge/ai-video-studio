"""
Script quality (industrial lint) services.

Provides deterministic lint checks for screenplay-like scripts, focused on
"visual-only" constraints (可拍性、台词长度、钩子/断点等).
"""

from app.services.script_quality.lint_engine import lint_script_content

__all__ = ["lint_script_content"]

