from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

from app.prompts.manager import prompt_manager
from app.prompts.template_resolver import resolve_template_name

_TEMPLATE_REF_RE = re.compile(r"{%-?\\s*(?:include|import|from)\\s+[\"']([^\"']+)[\"']")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_within_prompts_dir(prompts_dir: Path, path: Path) -> bool:
    try:
        resolved_prompts = prompts_dir.resolve()
        resolved_path = path.resolve()
    except Exception:  # pragma: no cover - defensive
        return False

    if resolved_path == resolved_prompts:
        return True
    return resolved_prompts in resolved_path.parents


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _collect_template_sources(
    *,
    prompts_dir: Path,
    entry_template: str,
) -> dict[str, str]:
    sources: dict[str, str] = {}
    queue: list[str] = [f"{entry_template}.txt"]
    seen: set[str] = set()

    while queue:
        rel = queue.pop()
        if rel in seen:
            continue
        seen.add(rel)

        candidate = (prompts_dir / rel).resolve()
        if not _is_within_prompts_dir(prompts_dir, candidate):
            continue
        if not candidate.exists():
            continue

        text = _read_text(candidate)
        rel_posix = Path(rel).as_posix()
        sources[rel_posix] = sha256_text(text)

        for match in _TEMPLATE_REF_RE.finditer(text):
            ref = match.group(1).strip()
            if not ref:
                continue
            if ref.startswith(("/", "\\")) or ".." in Path(ref).parts:
                continue
            queue.append(ref)

    return sources


def build_prompt_template_audit(
    template_name: str, *, variables: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return a stable fingerprint for a prompt template (name/version/source hash)."""
    vars_value: Mapping[str, Any] = variables or {}
    resolved = resolve_template_name(
        template_name, vars_value, prompt_manager.prompts_dir
    )
    metadata = prompt_manager.load_metadata(resolved)
    version = metadata.get("version") if isinstance(metadata, dict) else None

    sources = _collect_template_sources(
        prompts_dir=prompt_manager.prompts_dir, entry_template=resolved
    )
    digest_payload = "\n".join(
        f"{path}:{sources[path]}" for path in sorted(sources.keys())
    )

    return {
        "template": template_name,
        "resolved_template": resolved,
        "version": str(version) if version is not None else None,
        "sources_hash": sha256_text(digest_payload),
    }
