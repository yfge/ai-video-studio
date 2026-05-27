"""System API calls for provider chain regression."""

from __future__ import annotations

import argparse
import hashlib
from typing import Any

import requests

from scripts.harness.provider_chain_payloads import (
    IMAGE_MODEL,
    SEEDANCE_CANONICAL,
    TEXT_MODEL,
    VIDEO_MODEL,
    build_script_prompt,
    extract_structured_script,
    scene_durations,
)


def record_response(
    chain: list[dict[str, Any]], response: requests.Response, *, label: str
) -> None:
    elapsed_seconds = None
    if response.elapsed is not None:
        elapsed_seconds = round(response.elapsed.total_seconds(), 3)
    entry = {
        "label": label,
        "method": response.request.method,
        "url": response.url,
        "status_code": response.status_code,
        "request_id": response.headers.get("x-request-id"),
        "harness_run_id": response.headers.get("x-harness-run-id"),
    }
    if elapsed_seconds is not None:
        entry["duration_seconds"] = elapsed_seconds
    if response.status_code >= 400:
        entry["response_body"] = response.text[:2000]
    chain.append(entry)


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    chain: list[dict[str, Any]],
    label: str,
    timeout: int,
    **kwargs: Any,
) -> dict[str, Any]:
    response = session.request(method, url, timeout=timeout, **kwargs)
    record_response(chain, response, label=label)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = response.text[:2000] if response.text else ""
        suffix = f" | response_body={body}" if body else ""
        raise requests.HTTPError(
            f"{exc}{suffix}",
            response=response,
            request=response.request,
        ) from exc
    return response.json() if response.content else {}


def login(session: requests.Session, args: argparse.Namespace, payload: dict[str, Any]) -> None:
    response = session.post(
        f"{args.api_url.rstrip('/')}/api/v1/auth/login",
        data={"username": args.username, "password": args.password},
        headers={
            "x-harness-run-id": args.run_id,
            "x-client-request-id": f"{args.run_id}-login",
        },
        timeout=15,
    )
    record_response(payload["request_chain"], response, label="login")
    response.raise_for_status()
    body = response.json()
    session.headers["Authorization"] = f"Bearer {body['access_token']}"
    session.headers["x-harness-run-id"] = args.run_id
    payload["key_artifacts"]["auth"] = {"token_type": body.get("token_type")}


def confirm_models(
    session: requests.Session, args: argparse.Namespace, payload: dict[str, Any]
) -> None:
    targets = {
        "text_generation": {f"deepseek:{TEXT_MODEL}", TEXT_MODEL},
        "text_to_image": {
            IMAGE_MODEL,
            "openai:gpt-image-2",
            "chatgpt-img-2",
            "gpt-image-2",
        },
        "text_to_video": {f"volcengine:{SEEDANCE_CANONICAL}", SEEDANCE_CANONICAL},
        "image_to_video": {f"volcengine:{VIDEO_MODEL}", VIDEO_MODEL},
    }
    found: dict[str, list[dict[str, Any]]] = {}
    for model_type, wanted in targets.items():
        body = request_json(
            session,
            "GET",
            f"{args.api_url.rstrip('/')}/api/v1/ai/models/available",
            params={"model_type": model_type},
            chain=payload["request_chain"],
            label=f"models-{model_type}",
            timeout=30,
        )
        models = ((body.get("data") or {}).get("models") or []) if body.get("success") else []
        matches = [
            {key: item.get(key) for key in ("model_id", "id", "provider", "type")}
            for item in models
            if {str(item.get("model_id", "")), str(item.get("id", ""))} & wanted
        ]
        if not matches:
            raise RuntimeError(f"required model unavailable for {model_type}: {sorted(wanted)}")
        found[model_type] = matches
    payload["key_artifacts"]["models"] = found


def generate_script(
    session: requests.Session, args: argparse.Namespace, payload: dict[str, Any]
) -> dict[str, Any]:
    body = request_json(
        session,
        "POST",
        f"{args.api_url.rstrip('/')}/api/v1/ai/generate/text",
        json={
            "prompt": build_script_prompt(
                args.mode,
                getattr(args, "script_premise", None),
            ),
            "model": TEXT_MODEL,
            "prefer_provider": "deepseek",
            "system_prompt": "You are a strict JSON writer. Output JSON only.",
            "temperature": 0.4,
            "max_tokens": 2200,
        },
        chain=payload["request_chain"],
        label="deepseek-script",
        timeout=args.timeout_seconds,
    )
    data = body.get("data") or {}
    if data.get("provider") != "deepseek" or data.get("model") != TEXT_MODEL:
        raise RuntimeError(
            f"unexpected text provider/model: {data.get('provider')} {data.get('model')}"
        )
    script = extract_structured_script(
        str(data.get("content") or ""), len(scene_durations(args.mode))
    )
    payload["key_artifacts"]["script"] = {
        "provider": data.get("provider"),
        "model": data.get("model"),
        "title": script.get("title"),
        "scene_count": len(script["scenes"]),
        "raw_content": data.get("content"),
    }
    return script


def create_virtual_ip(
    session: requests.Session,
    args: argparse.Namespace,
    timeline: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    anchor = _timeline_character_anchor(timeline)
    name = f"provider-chain-{_run_name_suffix(args.run_id)}"
    body = request_json(
        session,
        "POST",
        f"{args.api_url.rstrip('/')}/api/v1/virtual-ips/",
        json={
            "name": name,
            "description": anchor,
            "tags": ["provider-chain-regression", "cartoon"],
            "background_story": _timeline_plot_summary(timeline),
            "style_prompt": anchor,
            "is_public": False,
        },
        chain=payload["request_chain"],
        label="virtual-ip-create",
        timeout=30,
    )
    vip = body.get("data") or {}
    if not vip.get("id"):
        raise RuntimeError("virtual_ip_create_missing_id")
    payload["key_artifacts"]["virtual_ip"] = {"id": vip["id"], "name": name}
    return vip


def generate_character_image(
    session: requests.Session,
    args: argparse.Namespace,
    timeline: dict[str, Any],
    vip: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    body = request_json(
        session,
        "POST",
        f"{args.api_url.rstrip('/')}/api/v1/virtual-ips/{vip['id']}/images/generate",
        json={
            "model_id": IMAGE_MODEL,
            "style": "cartoon",
            "category": "portrait",
            "count": 1,
            "size": "1024x1536",
            "aspect_ratio": "9:16",
            "additional_prompts": [_timeline_character_image_prompt(timeline)],
            "is_default": True,
        },
        chain=payload["request_chain"],
        label="openai-character-image",
        timeout=args.timeout_seconds,
    )
    image_url = body.get("oss_url")
    if not isinstance(image_url, str) or not image_url.startswith(("http://", "https://")):
        raise RuntimeError("image_generation_missing_public_oss_url")
    payload["key_artifacts"]["image"] = {
        "id": body.get("id"),
        "provider": "openai",
        "model": body.get("ai_model"),
        "oss_url": image_url,
        "file_path": body.get("file_path"),
        "source": "timeline_shot_plan",
    }
    return {"image_url": image_url, "image_id": body.get("id")}


def _timeline_shot_plans(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for track in (timeline.get("spec") or {}).get("tracks") or []:
        if not isinstance(track, dict) or track.get("track_type") != "video":
            continue
        for clip in track.get("clips") or []:
            refs = clip.get("source_refs") if isinstance(clip, dict) else {}
            plan = refs.get("timeline_shot_plan") if isinstance(refs, dict) else None
            if isinstance(plan, dict):
                plans.append(plan)
    if not plans:
        raise RuntimeError("timeline_shot_plan_missing_for_character_image")
    return plans


def _run_name_suffix(run_id: str) -> str:
    digest = hashlib.sha1(run_id.encode("utf-8")).hexdigest()[:12]
    return digest


def _timeline_character_anchor(timeline: dict[str, Any]) -> str:
    for plan in _timeline_shot_plans(timeline):
        anchor = plan.get("character_anchor")
        if isinstance(anchor, str) and anchor.strip():
            return anchor.strip()
    return "non-real 3D cartoon robot character"


def _timeline_plot_summary(timeline: dict[str, Any]) -> str:
    plots = [
        str(plan.get("plot")).strip()
        for plan in _timeline_shot_plans(timeline)
        if str(plan.get("plot") or "").strip()
    ]
    return " / ".join(plots[:3])


def _timeline_character_image_prompt(timeline: dict[str, Any]) -> str:
    plans = _timeline_shot_plans(timeline)
    anchor = _timeline_character_anchor(timeline)
    visual_prompts = [
        str(plan.get("visual_prompt")).strip()
        for plan in plans
        if str(plan.get("visual_prompt") or "").strip()
    ]
    return (
        f"{anchor}. "
        f"Timeline visual source: {' / '.join(visual_prompts[:2])}. "
        "High quality 3D cartoon character reference sheet, expressive LED eyes, "
        "cinematic lighting, clean silhouette, non-real robot, no photorealistic human."
    )
