"""Codex CLI authentication helpers.

Reads the local Codex CLI auth file and extracts ChatGPT OAuth tokens for
the ChatGPT Codex responses endpoint. Token values must never be logged.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CODEX_AUTH_PATH = Path.home() / ".codex" / "auth.json"
CODEX_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"


class CodexAuthError(RuntimeError):
    """Raised when Codex auth cannot be loaded or refreshed."""


@dataclass(frozen=True)
class CodexAuth:
    access_token: str
    auth_mode: str = "chatgpt"
    refresh_token: str | None = None
    id_token: str | None = None
    account_id: str | None = None
    last_refresh: str | None = None
    source_path: Path = DEFAULT_CODEX_AUTH_PATH


def resolve_codex_auth_path(path: str | Path | None = None) -> Path:
    return Path(path).expanduser() if path else DEFAULT_CODEX_AUTH_PATH


def read_codex_auth(path: str | Path | None = None) -> CodexAuth:
    auth_path = resolve_codex_auth_path(path)
    if not auth_path.is_file():
        raise CodexAuthError(
            f"Codex auth file not found at {auth_path}. Run `codex login` first."
        )

    try:
        raw = auth_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CodexAuthError(f"Cannot read {auth_path}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CodexAuthError(f"{auth_path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CodexAuthError(f"{auth_path} must contain a JSON object")

    tokens = data.get("tokens") or {}
    access_token = tokens.get("access_token")
    if not access_token:
        raise CodexAuthError(
            f"{auth_path} has no tokens.access_token. Run `codex login` to refresh it."
        )

    return CodexAuth(
        access_token=access_token,
        auth_mode=data.get("auth_mode", "chatgpt"),
        refresh_token=tokens.get("refresh_token"),
        id_token=tokens.get("id_token"),
        account_id=tokens.get("account_id"),
        last_refresh=data.get("last_refresh"),
        source_path=auth_path,
    )


def refresh_codex_auth(
    path: str | Path | None = None,
    *,
    token_url: str = CODEX_OAUTH_TOKEN_URL,
    client_id: str = CODEX_CLIENT_ID,
    timeout_s: int = 30,
) -> CodexAuth:
    auth_path = resolve_codex_auth_path(path)
    data, raw_before = _read_auth_payload(auth_path)
    tokens = data.get("tokens") or {}
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise CodexAuthError(
            f"{auth_path} has no tokens.refresh_token; run `codex login` again."
        )

    refreshed = _request_token_refresh(
        token_url=token_url,
        client_id=client_id,
        refresh_token=refresh_token,
        timeout_s=timeout_s,
    )

    current_raw = auth_path.read_text(encoding="utf-8")
    if current_raw != raw_before:
        return read_codex_auth(auth_path)

    access_token = refreshed.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise CodexAuthError(
            "Codex token refresh response did not include access_token"
        )

    updated_tokens = dict(tokens)
    updated_tokens["access_token"] = access_token
    for key in ("refresh_token", "id_token"):
        value = refreshed.get(key)
        if isinstance(value, str) and value:
            updated_tokens[key] = value

    account_id = (
        refreshed.get("account_id")
        or refreshed.get("chatgpt_account_id")
        or refreshed.get("chatgptAccountId")
    )
    if isinstance(account_id, str) and account_id:
        updated_tokens["account_id"] = account_id

    data["tokens"] = updated_tokens
    if "OPENAI_API_KEY" in data:
        data["OPENAI_API_KEY"] = access_token
    data["last_refresh"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    _write_auth_payload(auth_path, data)
    return read_codex_auth(auth_path)


def _read_auth_payload(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CodexAuthError(f"Cannot read {path}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CodexAuthError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CodexAuthError(f"{path} must contain a JSON object")
    return data, raw


def _request_token_refresh(
    *,
    token_url: str,
    client_id: str,
    refresh_token: str,
    timeout_s: int,
) -> dict[str, Any]:
    form = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise CodexAuthError(
            f"Codex token refresh returned HTTP {exc.code}: {_redact_token_body(body)}"
        ) from exc
    except urllib.error.URLError as exc:
        raise CodexAuthError(
            f"Codex token refresh transport failed: {exc.reason}"
        ) from exc

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise CodexAuthError("Codex token refresh response was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise CodexAuthError("Codex token refresh response must be a JSON object")
    return payload


def _write_auth_payload(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, path)


def _redact_token_body(body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        _redact_token_fields(payload)
        return json.dumps(payload, ensure_ascii=False)

    redacted = body
    for marker in ("access_token", "refresh_token", "id_token"):
        redacted = re.sub(
            rf'("{re.escape(marker)}"\s*:\s*")[^"]+(")',
            r"\1<redacted>\2",
            redacted,
        )
        redacted = re.sub(
            rf"({re.escape(marker)}=)[^&\s]+",
            r"\1<redacted>",
            redacted,
        )
    return redacted


def _redact_token_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"access_token", "refresh_token", "id_token"}:
                value[key] = "<redacted>"
            else:
                _redact_token_fields(item)
    elif isinstance(value, list):
        for item in value:
            _redact_token_fields(item)
