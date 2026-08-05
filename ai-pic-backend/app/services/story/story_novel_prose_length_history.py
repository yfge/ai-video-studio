"""Historical observations for the closed-loop prose length controller."""

from __future__ import annotations

import copy

from app.repositories.story_novel_repository import StoryNovelRepository

from .story_novel_prose_length_evidence import reconstruct_initial_prose

_BASELINE_WINDOW = 5


def length_observations(
    db,
    revision,
    position: int,
    model: str | None,
    policy_schema: str,
    prompt_contract_version: int,
) -> list[dict]:
    baseline = copy.deepcopy(
        ((revision.continuity_ledger or {}).get("prose_length_control") or {}).get(
            "baseline_samples"
        )
        or []
    )
    return [
        *[item for item in baseline if _valid_observation(item)],
        *_revision_observations(
            db,
            revision,
            position,
            model,
            policy_schema,
            prompt_contract_version,
        ),
    ]


def prior_revision_length_samples(
    db,
    revision,
    policy_schema: str,
    prompt_contract_version: int,
) -> list[dict]:
    """Freeze recent same-model calibration when a new revision first writes prose."""
    story_id = getattr(revision, "story_id", None)
    revision_id = getattr(revision, "id", None)
    if not db or not story_id or not revision_id:
        return []
    model = _revision_model(revision)
    candidates = sorted(
        (
            item
            for item in StoryNovelRepository(db).story_revisions(story_id)
            if item.id < revision_id
        ),
        key=lambda item: (item.revision_number, item.id),
    )
    result = []
    for source in candidates:
        for item in _revision_observations(
            db,
            source,
            10**9,
            model,
            policy_schema,
            prompt_contract_version,
        ):
            result.append(
                {
                    **item,
                    "source_revision_business_id": source.business_id,
                }
            )
    controlled = [item for item in result if item["controlled"]]
    return copy.deepcopy((controlled or result)[-_BASELINE_WINDOW:])


def _revision_observations(
    db,
    revision,
    position: int,
    model: str | None,
    policy_schema: str,
    prompt_contract_version: int,
) -> list[dict]:
    chapters = (revision.continuity_ledger or {}).get("chapters") or {}
    plans = {
        int(item["position"]): item
        for item in (revision.generation_plan or {}).get("chapters") or []
    }
    result = []
    for key, entry in sorted(chapters.items(), key=lambda item: int(item[0])):
        chapter_position = int(key)
        if chapter_position >= position or entry.get("status") != "ready":
            continue
        prose_metric = (entry.get("stage_metrics") or {}).get("prose") or {}
        attempt_model = metric_model(prose_metric)
        if model and (not attempt_model or not same_model(model, attempt_model)):
            continue
        stored = prose_metric.get("length_control") or {}
        expected_count = len(entry.get("blocks") or []) or len(
            (entry.get("chapter_brief") or {}).get("beats") or []
        )
        reconstructed = reconstruct_initial_prose(
            db,
            revision.business_id,
            chapter_position,
            prose_metric,
            expected_count,
        )
        if reconstructed is None:
            continue
        stored_version = int(stored.get("prompt_contract_version") or 1)
        if (
            stored.get("schema") == policy_schema
            and stored_version == prompt_contract_version
            and same_model(str(stored.get("model") or ""), str(model or ""))
        ):
            requested = int(
                (stored.get("requested_length") or {}).get("target_chars") or 0
            )
            actual = int(reconstructed["observed_output_chars"])
            if requested > 0 and all(
                stored.get(key) == value for key, value in reconstructed.items()
            ):
                result.append(
                    _observation(
                        entry,
                        prose_metric,
                        chapter_position,
                        requested,
                        actual,
                        controlled=True,
                        request_scale=stored.get("request_scale"),
                        prompt_input_hash=stored.get("prompt_input_hash"),
                    )
                )
            continue
        plan = plans.get(chapter_position) or {}
        requested = int(plan.get("target_chars") or 0)
        actual = int(reconstructed["observed_output_chars"])
        if requested > 0 and actual > 0:
            result.append(
                _observation(
                    entry,
                    prose_metric,
                    chapter_position,
                    requested,
                    actual,
                    controlled=False,
                    invocation_ids=reconstructed["source_invocation_ids"],
                )
            )
    return result


def _revision_model(revision) -> str | None:
    return ((revision.generation_plan or {}).get("model_policy") or {}).get(
        "prose_model"
    ) or revision.model


def _valid_observation(item) -> bool:
    return bool(
        isinstance(item, dict)
        and int(item.get("requested_chars") or 0) > 0
        and int(item.get("actual_chars") or 0) > 0
        and isinstance(item.get("controlled"), bool)
    )


def metric_model(metric: dict) -> str | None:
    attempts = metric.get("attempts") or []
    if not attempts:
        return None
    item = attempts[-1]
    provider, model = item.get("provider"), item.get("model")
    return f"{provider}:{model}" if provider and model else model


def same_model(left: str, right: str) -> bool:
    return bool(left and right and left == right)


def _observation(
    entry: dict,
    prose_metric: dict,
    position: int,
    requested: int,
    actual: int,
    *,
    controlled: bool,
    invocation_ids: list[int] | None = None,
    request_scale=None,
    prompt_input_hash=None,
) -> dict:
    return {
        "requested_chars": requested,
        "actual_chars": actual,
        "controlled": controlled,
        "request_scale": request_scale,
        "position": position,
        "body_hash": entry.get("body_hash"),
        "source_hash": entry.get("source_hash"),
        "invocation_ids": list(
            invocation_ids
            if invocation_ids is not None
            else prose_metric.get("invocation_ids") or []
        ),
        "prompt_input_hash": prompt_input_hash,
    }
