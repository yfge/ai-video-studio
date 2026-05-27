"""IO helpers for production quality regression artifacts."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.harness._common import ARTIFACTS_ROOT, write_json


def resolve_provider_chain_path(input_run: str) -> Path:
    path = Path(input_run)
    if path.is_file():
        return path
    if path.is_dir():
        return path / "provider_chain.json"
    return ARTIFACTS_ROOT / input_run / "provider_chain.json"


def load_provider_chain(input_run: str) -> dict[str, Any]:
    path = resolve_provider_chain_path(input_run)
    if not path.exists():
        raise FileNotFoundError(f"provider_chain_not_found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_quality_outputs(run_dir: Path, report: dict[str, Any]) -> None:
    write_json(run_dir / "quality_report.json", report)
    write_samples_csv(run_dir / "samples.csv", report.get("samples") or [])
    write_review_pack(run_dir / "review_pack.md", report)


def write_samples_csv(path: Path, samples: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "sample_id",
        "attempt",
        "passed",
        "timeline_id",
        "final_url",
        "hard_failures",
        "script_failures",
        "provider_chain_artifact",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "sample_id": sample.get("sample_id"),
                    "attempt": sample.get("attempt"),
                    "passed": sample.get("passed"),
                    "timeline_id": sample.get("timeline_id"),
                    "final_url": sample.get("final_url"),
                    "hard_failures": ";".join(sample.get("hard_failures") or []),
                    "script_failures": ";".join(sample.get("script_failures") or []),
                    "provider_chain_artifact": sample.get("provider_chain_artifact"),
                }
            )


def write_review_pack(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Timeline-First Production Quality Review",
        "",
        f"- Verdict: `{report.get('aggregate', {}).get('verdict')}`",
        f"- Samples: {report.get('aggregate', {}).get('sample_count')}",
        "",
        "## Samples",
    ]
    for sample in report.get("samples") or []:
        character = sample.get("character_consistency") or {}
        lines.extend(
            [
                "",
                f"### {sample.get('sample_id')} attempt {sample.get('attempt')}",
                f"- Passed: `{sample.get('passed')}`",
                f"- Timeline: `{sample.get('timeline_id')}`",
                f"- Final URL: {sample.get('final_url') or '-'}",
                f"- Contact sheet: {character.get('contact_sheet') or '-'}",
                _list_line("Hard failures", sample.get("hard_failures") or []),
                _list_line("Script failures", sample.get("script_failures") or []),
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_clip_frames(
    videos: list[dict[str, Any]],
    *,
    frame_dir: Path,
    offsets: tuple[float, ...] = (2.0, 7.5, 13.0),
) -> list[str]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames: list[str] = []
    for clip in videos:
        ordinal = int(clip.get("ordinal") or len(frames) + 1)
        video_url = str(clip.get("video_url") or "")
        if not video_url.startswith(("http://", "https://")):
            continue
        for offset in offsets:
            path = frame_dir / f"clip_{ordinal:02d}_{round(offset * 1000)}ms.jpg"
            _extract_one_frame(video_url, path, offset, ordinal)
            frames.append(str(path))
    return frames


def make_contact_sheet(frame_paths: list[str], output_path: Path) -> str | None:
    if not frame_paths:
        return None
    try:
        from PIL import Image, ImageDraw
    except Exception:  # noqa: BLE001 - review aid, not lineage source of truth
        return None
    images = [Image.open(path).convert("RGB") for path in frame_paths]
    thumb_w, thumb_h = 220, 390
    padding = 12
    columns = min(3, max(1, len(images)))
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (
            columns * thumb_w + (columns + 1) * padding,
            rows * (thumb_h + 24) + (rows + 1) * padding,
        ),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, image in enumerate(images):
        image.thumbnail((thumb_w, thumb_h))
        col = index % columns
        row = index // columns
        x = padding + col * (thumb_w + padding)
        y = padding + row * (thumb_h + 24 + padding)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_h + 4), Path(frame_paths[index]).name, fill="black")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return str(output_path)


def _extract_one_frame(video_url: str, path: Path, offset: float, ordinal: int) -> None:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{offset:.3f}",
            "-i",
            video_url,
            "-frames:v",
            "1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0 or not path.exists():
        raise RuntimeError(
            "quality_frame_extract_failed: "
            f"clip={ordinal} offset={offset} stderr={completed.stderr.strip()}"
        )


def _list_line(label: str, values: list[str]) -> str:
    return f"- {label}: {', '.join(values) if values else '-'}"
