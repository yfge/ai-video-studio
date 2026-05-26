"""System API calls for provider chain regression."""

from __future__ import annotations

import argparse
from typing import Any

import requests

from scripts.harness.provider_chain_payloads import (
    IMAGE_MODEL,
    SEEDANCE_CANONICAL,
    TEXT_MODEL,
    VIDEO_MODEL,
    build_script_prompt,
    character_image_prompt,
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
    response.raise_for_status()
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
            "prompt": build_script_prompt(args.mode),
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
    script: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    character = script["characters"][0]
    name = f"provider-chain-{args.run_id[-12:]}"
    body = request_json(
        session,
        "POST",
        f"{args.api_url.rstrip('/')}/api/v1/virtual-ips/",
        json={
            "name": name,
            "description": character.get("appearance_prompt") or "3D cartoon robot character",
            "tags": ["provider-chain-regression", "cartoon"],
            "background_story": script.get("logline"),
            "style_prompt": character.get("consistency_anchor"),
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
    script: dict[str, Any],
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
            "additional_prompts": [character_image_prompt(script)],
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
    }
    return {"image_url": image_url, "image_id": body.get("id")}
