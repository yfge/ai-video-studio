"""System API quality checks for production quality regression."""

from __future__ import annotations

import argparse
import asyncio
from types import SimpleNamespace
from typing import Any

import requests

from scripts.harness.production_quality_script import (
    lint_script_async,
    provider_chain_script_text,
)

TEXT_MODEL = "deepseek-v4-flash"


def lint_script_via_api(
    args: argparse.Namespace, payload: dict[str, Any], request_suffix: str
) -> dict[str, Any]:
    try:
        manager = _ApiTextManager(args, request_suffix)
        return asyncio.run(
            lint_script_async(
                payload,
                ai_manager=manager,
                model=TEXT_MODEL,
                prefer_provider="deepseek",
            )
        )
    except Exception as exc:  # noqa: BLE001 - lint failure is evidence
        return {
            "status": "failed",
            "provider": "deepseek",
            "model": TEXT_MODEL,
            "error": f"{type(exc).__name__}: {exc}",
            "passed": False,
        }


def score_script_via_api(
    args: argparse.Namespace, payload: dict[str, Any], request_suffix: str
) -> dict[str, Any]:
    try:
        with requests.Session() as session:
            token = _login_for_score(session, args)
            session.headers["Authorization"] = f"Bearer {token}"
            session.headers["x-harness-run-id"] = args.run_id
            response = session.post(
                f"{args.api_url.rstrip('/')}/api/v1/scoring/score",
                json=_score_payload(payload),
                headers={
                    "x-client-request-id": (
                        f"{args.run_id}-script-score-{request_suffix}"
                    )
                },
                timeout=args.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            data["provider"] = "deepseek"
            data["model"] = TEXT_MODEL
            return data
    except Exception as exc:  # noqa: BLE001 - scoring failure is evidence
        return {
            "status": "failed",
            "provider": "deepseek",
            "model": TEXT_MODEL,
            "error": f"{type(exc).__name__}: {exc}",
        }


class _ApiTextManager:
    def __init__(self, args: argparse.Namespace, request_suffix: str) -> None:
        self.args = args
        self.request_suffix = request_suffix
        self.calls: list[dict[str, Any]] = []

    async def generate_text(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        try:
            with requests.Session() as session:
                token = _login_for_score(session, self.args)
                session.headers["Authorization"] = f"Bearer {token}"
                session.headers["x-harness-run-id"] = self.args.run_id
                response = session.post(
                    f"{self.args.api_url.rstrip('/')}/api/v1/ai/generate/text",
                    json={
                        "prompt": kwargs.get("prompt"),
                        "model": kwargs.get("model"),
                        "prefer_provider": kwargs.get("prefer_provider"),
                        "system_prompt": kwargs.get("system_prompt"),
                        "temperature": kwargs.get("temperature", 0.0),
                        "max_tokens": kwargs.get("max_tokens", 1000),
                    },
                    headers={
                        "x-client-request-id": (
                            f"{self.args.run_id}-script-lint-{self.request_suffix}"
                        )
                    },
                    timeout=self.args.timeout_seconds,
                )
                response.raise_for_status()
                body = response.json()
                data = body.get("data") or {}
                return SimpleNamespace(
                    success=bool(body.get("success")),
                    data=data.get("content"),
                    provider=data.get("provider"),
                    model=data.get("model"),
                    error=None,
                )
        except Exception as exc:  # noqa: BLE001
            return SimpleNamespace(
                success=False,
                data=None,
                provider="deepseek",
                model=TEXT_MODEL,
                error=f"{type(exc).__name__}: {exc}",
            )


def _login_for_score(session: requests.Session, args: argparse.Namespace) -> str:
    response = session.post(
        f"{args.api_url.rstrip('/')}/api/v1/auth/login",
        data={"username": args.username, "password": args.password},
        headers={
            "x-harness-run-id": args.run_id,
            "x-client-request-id": f"{args.run_id}-score-login",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _score_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "script_content": provider_chain_script_text(payload),
        "story_title": "Timeline-first production quality regression",
        "story_genre": "cartoon_short_drama",
        "market_region": "CN",
        "micro_genre": "workplace-ai-production",
        "prefer_provider": "deepseek",
        "prefer_model": TEXT_MODEL,
    }
