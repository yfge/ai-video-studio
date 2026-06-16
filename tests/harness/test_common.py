from pathlib import Path

from scripts.harness import _common


def test_slugify_normalizes_workspace_names() -> None:
    assert _common.slugify("AI Video Studio / Main") == "ai-video-studio-main"
    assert _common.slugify("___") == "workspace"


def test_update_summary_creates_run_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_common, "ARTIFACTS_ROOT", tmp_path / "runs")

    run_dir = _common.ensure_run_dir("run-123")
    summary = _common.update_summary(run_dir, status="ok", checks=2)

    assert run_dir == tmp_path / "runs" / "run-123"
    assert (run_dir / "screenshots").is_dir()
    assert summary == {"checks": 2, "status": "ok"}
    assert _common.read_json(run_dir / "summary.json") == summary


def test_standard_fields_returns_stable_standard_refs() -> None:
    fields = _common.standard_fields("STD-EVIDENCE-001", "STD-EVIDENCE-001")

    assert fields["standard_ids"] == ["STD-EVIDENCE-001"]
    assert fields["standard_refs"][0]["standard_doc"] == (
        "docs/standards/STD-EVIDENCE-001.md"
    )


def test_read_env_file_skips_comments(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "HARNESS_RUN_ID=test-run",
                " NEXT_PUBLIC_API_URL = http://localhost:9300 ",
                "",
            ]
        ),
        encoding="utf-8",
    )

    values = _common.read_env_file(env_file)

    assert values == {
        "HARNESS_RUN_ID": "test-run",
        "NEXT_PUBLIC_API_URL": "http://localhost:9300",
    }
