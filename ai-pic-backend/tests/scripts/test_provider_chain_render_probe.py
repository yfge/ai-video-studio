import sys
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.provider_chain_render_probe import (  # noqa: E402
    probe_render_output,
)


def test_probe_render_output_records_streams_and_scene_frames(tmp_path, monkeypatch):
    payload = {
        "key_artifacts": {
            "render_job": {"output_url": "https://example.com/render.mp4"}
        }
    }
    args = SimpleNamespace(run_id="probe-run", mode="full-30s")

    def fake_run(command, **_kwargs):
        if command[0] == "ffprobe":
            return CompletedProcess(
                command,
                0,
                stdout="""
                {
                  "streams": [
                    {"index": 0, "codec_type": "video", "duration": "30.125"},
                    {"index": 1, "codec_type": "audio", "duration": "30.080"}
                  ],
                  "format": {"duration": "30.125"}
                }
                """,
                stderr="",
            )
        frame_path = Path(command[-1])
        frame_path.write_bytes(b"frame")
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        "scripts.harness.provider_chain_render_probe.ensure_run_dir",
        lambda _run_id: tmp_path,
    )
    monkeypatch.setattr(
        "scripts.harness.provider_chain_render_probe.subprocess.run",
        fake_run,
    )

    artifact = probe_render_output(args, payload)

    assert artifact["ok"] is True
    assert artifact["video_duration_seconds"] == 30.125
    assert artifact["audio_duration_seconds"] == 30.08
    assert len(artifact["frame_artifacts"]) == 2
    assert Path(artifact["frame_artifacts"][0]).exists()
    assert payload["key_artifacts"]["render_media_probe"] == artifact


def test_probe_render_output_fails_when_audio_stream_missing(tmp_path, monkeypatch):
    payload = {
        "key_artifacts": {
            "render_job": {"output_url": "https://example.com/render.mp4"}
        }
    }
    args = SimpleNamespace(run_id="probe-run", mode="smoke")

    def fake_run(command, **_kwargs):
        if command[0] == "ffprobe":
            return CompletedProcess(
                command,
                0,
                stdout="""
                {
                  "streams": [
                    {"index": 0, "codec_type": "video", "duration": "4.000"}
                  ],
                  "format": {"duration": "4.000"}
                }
                """,
                stderr="",
            )
        frame_path = Path(command[-1])
        frame_path.write_bytes(b"frame")
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        "scripts.harness.provider_chain_render_probe.ensure_run_dir",
        lambda _run_id: tmp_path,
    )
    monkeypatch.setattr(
        "scripts.harness.provider_chain_render_probe.subprocess.run",
        fake_run,
    )

    with pytest.raises(RuntimeError, match="render_media_probe_failed"):
        probe_render_output(args, payload)

    assert payload["key_artifacts"]["render_media_probe"]["ok"] is False
    assert (
        payload["key_artifacts"]["render_media_probe"]["checks"]["has_audio_stream"]
        is False
    )
