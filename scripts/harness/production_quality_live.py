"""Live sample runner for production quality regression."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from scripts.harness._common import ensure_run_dir
from scripts.harness.production_quality_api_checks import (
    lint_script_via_api,
    score_script_via_api,
)
from scripts.harness.production_quality_report import (
    aggregate_quality_report,
    evaluate_provider_chain_sample,
    extract_clip_frames,
    load_provider_chain,
    make_contact_sheet,
    write_quality_outputs,
)

DEFAULT_PREMISES = [
    "夜班卡通机器人发现奖金清零，必须在倒计时内找出是谁改了时间轴。",
    "卡通机甲剪辑师上线错误资产，客户马上验收，队友却说这是唯一证据。",
    "蓝色卡通机器人收到被删除的对白，发现它才是真正的合同条款。",
    "卡通角色导演坚持不用真人素材，却被要求十分钟交付一条安全样片。",
    "素材库里的卡通角色突然换脸，主角必须证明这是供应商回调问题。",
    "机器人制片助理发现第二段视频没有角色，必须阻止整片发布。",
    "卡通工作室的配音文件错位，主角通过一句台词识破内鬼。",
    "一张角色参考图被所有镜头复用，却在最后一帧露出隐藏标记。",
    "机器人项目经理要在客户关单前修好 Timeline 回填，否则全组白做。",
    "卡通审片员发现成片没有剧情钩子，三秒内重排出真正的反转。",
]


def run_live_samples(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    if not args.episode_id or not args.script_id:
        raise SystemExit("live-10 requires --episode-id and --script-id")
    samples: list[dict[str, Any]] = []
    report = _base_live_report(args, samples)
    write_quality_outputs(run_dir, report)
    for sample_index in range(1, args.sample_count + 1):
        sample_id = f"sample-{sample_index:02d}"
        premise = DEFAULT_PREMISES[(sample_index - 1) % len(DEFAULT_PREMISES)]
        for attempt in range(1, args.max_retries + 2):
            sample = run_live_sample(
                args,
                run_dir=run_dir,
                child_run_id=f"{args.run_id}-{sample_id}-attempt-{attempt}",
                sample_id=sample_id,
                premise=premise,
                attempt=attempt,
            )
            samples.append(sample)
            write_quality_outputs(run_dir, _base_live_report(args, samples))
            if sample.get("passed"):
                break
    return _base_live_report(args, samples)


def run_live_sample(
    args: argparse.Namespace,
    *,
    run_dir: Path,
    child_run_id: str,
    sample_id: str,
    premise: str,
    attempt: int,
) -> dict[str, Any]:
    provider_artifact = ensure_run_dir(child_run_id) / "provider_chain.json"
    started = time.monotonic()
    command = _provider_chain_command(args, child_run_id, premise)
    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=max(args.timeout_seconds * 5, 1800),
        check=False,
    )
    log_path = _write_provider_log(run_dir, sample_id, attempt, command, completed)
    if not provider_artifact.exists():
        return failed_sample(
            sample_id,
            attempt,
            str(provider_artifact),
            "provider_chain_artifact_missing",
            str(log_path),
            round(time.monotonic() - started, 3),
        )
    payload = load_provider_chain(str(provider_artifact))
    frames, sheet, frame_error = _collect_frames(payload, run_dir, sample_id, attempt)
    sample = evaluate_provider_chain_sample(
        payload,
        provider_chain_artifact=str(provider_artifact),
        script_lint=lint_script_via_api(args, payload, f"{sample_id}-{attempt}"),
        script_score=score_script_via_api(args, payload, f"{sample_id}-{attempt}"),
        frame_artifacts=frames,
        contact_sheet=sheet,
        sample_id=sample_id,
        attempt=attempt,
    )
    sample["subprocess"] = _subprocess_summary(completed, log_path, started)
    sample["script_premise"] = premise
    if frame_error:
        sample["hard_failures"].append("frame_extraction")
        sample["passed"] = False
        sample["frame_extraction_error"] = frame_error
    return sample


def failed_sample(
    sample_id: str,
    attempt: int,
    provider_artifact: str,
    reason: str,
    log_path: str,
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "attempt": attempt,
        "provider_chain_artifact": provider_artifact,
        "provider_chain_ok": False,
        "passed": False,
        "hard_failures": ["provider_chain"],
        "script_failures": [],
        "failure_categories": [reason],
        "subprocess": {"log_path": log_path, "elapsed_seconds": elapsed_seconds},
        "timeline_order": {"passed": False, "missing_labels": []},
        "render_structure": {"passed": False},
        "character_consistency": {"passed": False},
        "script_lint": {"status": "skipped", "passed": False},
        "script_score": {"status": "skipped", "passed": False},
        "structured_script_score": {"status": "skipped", "passed": False},
    }


def _provider_chain_command(
    args: argparse.Namespace, child_run_id: str, premise: str
) -> list[str]:
    command = [
        sys.executable,
        "scripts/harness/provider_chain_regression.py",
        "--mode",
        "full-30s",
        "--run-id",
        child_run_id,
        "--api-url",
        args.api_url,
        "--username",
        args.username,
        "--password",
        args.password,
        "--episode-id",
        str(args.episode_id),
        "--script-id",
        str(args.script_id),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--poll-interval-seconds",
        str(args.poll_interval_seconds),
        "--video-concurrency",
        str(args.video_concurrency),
        "--script-premise",
        premise,
    ]
    if args.keep_temp_ip:
        command.append("--keep-temp-ip")
    return command


def _collect_frames(
    payload: dict[str, Any],
    run_dir: Path,
    sample_id: str,
    attempt: int,
) -> tuple[list[str], str | None, str | None]:
    try:
        videos = (payload.get("key_artifacts") or {}).get("videos") or []
        frames = extract_clip_frames(
            videos,
            frame_dir=run_dir / "frames" / f"{sample_id}-attempt-{attempt}",
        )
        sheet = make_contact_sheet(
            frames,
            run_dir / "frames" / f"{sample_id}-attempt-{attempt}-contact-sheet.jpg",
        )
        return frames, sheet, None
    except Exception as exc:  # noqa: BLE001 - evidence records failure
        return [], None, f"{type(exc).__name__}: {exc}"


def _base_live_report(args: argparse.Namespace, samples: list[dict[str, Any]]) -> dict:
    return {
        "contract_version": 1,
        "mode": "live-10",
        "run_id": args.run_id,
        "api_url": args.api_url,
        "episode_id": args.episode_id,
        "script_id": args.script_id,
        "sample_count": args.sample_count,
        "duration_plan": args.duration_plan,
        "video_concurrency": args.video_concurrency,
        "samples": samples,
        "aggregate": aggregate_quality_report(
            samples,
            expected_sample_count=args.sample_count,
        ),
    }


def _write_provider_log(
    run_dir: Path,
    sample_id: str,
    attempt: int,
    command: list[str],
    completed: subprocess.CompletedProcess[str],
) -> Path:
    log_path = run_dir / f"{sample_id}-attempt-{attempt}-provider-chain.log"
    log_path.write_text(
        f"$ {' '.join(command)}\n\nSTDOUT:\n{completed.stdout}\n\n"
        f"STDERR:\n{completed.stderr}\n",
        encoding="utf-8",
    )
    return log_path


def _subprocess_summary(
    completed: subprocess.CompletedProcess[str], log_path: Path, started: float
) -> dict[str, Any]:
    return {
        "returncode": completed.returncode,
        "log_path": str(log_path),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
