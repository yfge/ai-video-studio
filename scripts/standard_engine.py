#!/usr/bin/env python3
"""Shared standard catalog for repository contract checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Standard:
    id: str
    title: str
    owner_doc: str
    enforcement: str
    evidence: str
    suggested_direction: str


STANDARDS: dict[str, Standard] = {
    "STD-ARCH-001": Standard(
        id="STD-ARCH-001",
        title="Source files stay below size limits",
        owner_doc="docs/standards/STD-ARCH-001.md",
        enforcement="scripts/check_repo_contracts.py oversized_files",
        evidence="line_count, limit, baseline_exemption",
        suggested_direction=(
            "Split oversized files along existing service, hook, component, "
            "fixture, or helper boundaries."
        ),
    ),
    "STD-ARCH-002": Standard(
        id="STD-ARCH-002",
        title="API route handlers stay thin",
        owner_doc="docs/standards/STD-ARCH-002.md",
        enforcement="scripts/check_repo_contracts.py route_handlers",
        evidence="handler_lines, limit, baseline_exemption",
        suggested_direction=(
            "Move orchestration into services and persistence into repositories."
        ),
    ),
    "STD-DATA-001": Standard(
        id="STD-DATA-001",
        title="SQLAlchemy queries stay inside repositories",
        owner_doc="docs/standards/STD-DATA-001.md",
        enforcement="scripts/check_repo_contracts.py direct_queries",
        evidence="query_hits, baseline_exemption",
        suggested_direction=(
            "Add or reuse a repository method instead of calling session.query "
            "from API or service code."
        ),
    ),
    "STD-ARCH-003": Standard(
        id="STD-ARCH-003",
        title="Legacy choke points are not expansion points",
        owner_doc="docs/standards/STD-ARCH-003.md",
        enforcement="scripts/check_repo_contracts.py legacy_references",
        evidence="legacy reference pattern and path",
        suggested_direction=(
            "Depend on focused services or split the choke point before adding "
            "new references."
        ),
    ),
    "STD-DOCS-001": Standard(
        id="STD-DOCS-001",
        title="Repository docs and agent mirrors stay synchronized",
        owner_doc="docs/standards/STD-DOCS-001.md",
        enforcement="scripts/check_repo_docs.py",
        evidence="docs drift errors",
        suggested_direction=(
            "Update the source-of-truth doc, docs index, or AGENTS mirrors in "
            "the same change."
        ),
    ),
    "STD-EVIDENCE-001": Standard(
        id="STD-EVIDENCE-001",
        title="Agent changes include durable validation evidence",
        owner_doc="docs/standards/STD-EVIDENCE-001.md",
        enforcement="scripts/check_agent_chats.py and review",
        evidence="agent_chats entry, commands, browser path, artifact run_id",
        suggested_direction=(
            "Record the prompt, goals, changes, validation, next steps, and "
            "linked commits in the required ledger format."
        ),
    ),
    "STD-SCRIPT-001": Standard(
        id="STD-SCRIPT-001",
        title="Production scripts satisfy beat-level quality gates",
        owner_doc="docs/standards/STD-SCRIPT-001.md",
        enforcement="beat contract tests and production quality harnesses",
        evidence="structured_script_contract, failed_checks, harness artifacts",
        suggested_direction=(
            "Repair the beat contract, prompt, or quality gate instead of "
            "persisting structurally weak production scripts."
        ),
    ),
    "STD-TIMELINE-001": Standard(
        id="STD-TIMELINE-001",
        title="Timeline-first provider chain preserves media lineage",
        owner_doc="docs/standards/STD-TIMELINE-001.md",
        enforcement="production quality provider-chain harnesses",
        evidence=(
            "timeline_order, render_structure, character_consistency, "
            "quality_report artifacts"
        ),
        suggested_direction=(
            "Repair Timeline ordering, render output, clip lineage, or visual "
            "evidence before treating a provider-chain sample as trial-ready."
        ),
    ),
}

CATEGORY_TO_STANDARD_ID = {
    "oversized_files": "STD-ARCH-001",
    "route_handlers": "STD-ARCH-002",
    "direct_queries": "STD-DATA-001",
    "legacy_references": "STD-ARCH-003",
    "docs_drift": "STD-DOCS-001",
}


def standard_for_category(category: str) -> Standard:
    standard_id = CATEGORY_TO_STANDARD_ID[category]
    return STANDARDS[standard_id]


def standard_catalog_payload() -> dict[str, dict[str, str]]:
    return {
        standard_id: asdict(standard)
        for standard_id, standard in sorted(STANDARDS.items())
    }


def standard_reference(standard_id: str) -> dict[str, str]:
    standard = STANDARDS[standard_id]
    return {
        "standard_id": standard.id,
        "standard_title": standard.title,
        "standard_doc": standard.owner_doc,
        "standard_evidence": standard.evidence,
        "suggested_direction": standard.suggested_direction,
    }


def annotate_violation(category: str, violation: dict[str, Any]) -> dict[str, Any]:
    return {
        **violation,
        **standard_reference(standard_for_category(category).id),
    }


def annotate_violation_map(
    violations: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        category: [annotate_violation(category, item) for item in items]
        for category, items in violations.items()
    }
