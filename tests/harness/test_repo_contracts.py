from pathlib import Path

from scripts import check_repo_contracts


def test_longest_route_handler_counts_route_body_lines() -> None:
    text = """
@router.get("/health")
async def health():
    value = 1
    if value:
        return {"ok": True}


def helper():
    return None
""".strip()

    assert check_repo_contracts.longest_route_handler(text) == 4


def test_check_changed_files_flags_direct_queries(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path
    monkeypatch.setattr(check_repo_contracts, "REPO_ROOT", repo_root)

    scenario_dir = repo_root / "scripts" / "harness"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "scenarios.py").write_text(
        'BROWSER_SCENARIOS = {"login_smoke": {}, "episode_timeline_smoke": {}}\n',
        encoding="utf-8",
    )

    endpoint = repo_root / "ai-pic-backend" / "app" / "api" / "v1" / "endpoints"
    endpoint.mkdir(parents=True)
    path = endpoint / "demo.py"
    path.write_text(
        "\n".join(
            [
                "from app.core.database import SessionLocal",
                "",
                "@router.get('/demo')",
                "async def demo():",
                "    result = session.query(Model).all()",
                "    return result",
            ]
        ),
        encoding="utf-8",
    )

    errors: list[str] = []
    check_repo_contracts.check_changed_files([path], errors)

    assert errors == [
        "ai-pic-backend/app/api/v1/endpoints/demo.py uses direct SQLAlchemy queries outside repositories"
    ]
