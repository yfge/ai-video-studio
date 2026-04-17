#!/usr/bin/env python3
"""Lite harness doctor for ai-video-studio."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

import requests

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary, write_json


def can_connect(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, port)) == 0


def check_url(url: str) -> dict[str, object]:
    try:
        response = requests.get(url, timeout=5)
        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "url": url,
            "snippet": response.text[:200],
        }
    except requests.RequestException as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--nginx-url", default="http://localhost:8089")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--frontend-url", default="http://localhost:3000")
    parser.add_argument(
        "--env-file",
        default="docker/.env.lite",
        help="Env file used to launch the harness stack",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = ensure_run_dir(args.run_id)
    env_path = Path(args.env_file)

    ports = {
        "frontend": can_connect("127.0.0.1", int(args.frontend_url.rsplit(":", 1)[1])),
        "api": can_connect("127.0.0.1", int(args.api_url.rsplit(":", 1)[1])),
        "nginx": can_connect("127.0.0.1", int(args.nginx_url.rsplit(":", 1)[1])),
    }
    checks = {
        "env_file_exists": env_path.exists(),
        "frontend_port": ports["frontend"],
        "api_port": ports["api"],
        "nginx_port": ports["nginx"],
        "frontend_root": check_url(args.frontend_url),
        "api_health": check_url(f"{args.api_url}/health"),
        "nginx_login": check_url(f"{args.nginx_url}/login"),
    }
    healthy = all(
        [
            checks["env_file_exists"],
            ports["frontend"],
            ports["api"],
            ports["nginx"],
            checks["api_health"]["ok"],
            checks["nginx_login"]["ok"],
        ]
    )

    write_json(run_dir / "doctor.json", checks)
    update_summary(
        run_dir,
        doctor_status="passed" if healthy else "failed",
        nginx_url=args.nginx_url,
        api_url=args.api_url,
        frontend_url=args.frontend_url,
    )

    if healthy:
        print("doctor: ok")
        return 0

    print("doctor: failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
