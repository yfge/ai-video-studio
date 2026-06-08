import importlib.util
from pathlib import Path


def _load_contract_audit_core():
    module_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "contract_audit_core.py"
    )
    spec = importlib.util.spec_from_file_location("contract_audit_core", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract_audit_core = _load_contract_audit_core()


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

    assert contract_audit_core.longest_route_handler(text) == 4


def test_diff_collectors_flag_direct_queries(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path
    monkeypatch.setattr(contract_audit_core, "REPO_ROOT", repo_root)

    path = _write_source(
        repo_root,
        "ai-pic-backend/app/api/v1/endpoints/demo.py",
        [
            "from app.core.database import SessionLocal",
            "",
            "@router.get('/demo')",
            "async def demo():",
            "    result = session.query(Model).all()",
            "    return result",
        ],
    )

    violations = contract_audit_core.collect_direct_queries([path], mode="diff")

    assert violations == [
        {
            "path": "ai-pic-backend/app/api/v1/endpoints/demo.py",
            "query_hits": 1,
            "baseline_exemption": False,
            "allowed_limit": None,
        }
    ]


def test_diff_collectors_allow_legacy_baseline_debt(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path
    rel = "ai-pic-backend/app/api/v1/endpoints/baseline_debt.py"
    monkeypatch.setattr(contract_audit_core, "REPO_ROOT", repo_root)
    monkeypatch.setattr(contract_audit_core, "HANDLER_LIMIT", 1)
    monkeypatch.setattr(contract_audit_core, "ALLOWED_ROUTE_HANDLERS", {rel: 4})
    monkeypatch.setattr(contract_audit_core, "ALLOWED_DIRECT_QUERIES", {rel: 1})

    path = _write_source(
        repo_root,
        rel,
        [
            "@router.get('/demo')",
            "async def demo():",
            "    result = session.query(Model).all()",
            "    if result:",
            "        return result",
        ],
    )

    assert contract_audit_core.collect_route_handlers([path], mode="diff") == []
    assert contract_audit_core.collect_direct_queries([path], mode="diff") == []

    assert contract_audit_core.collect_route_handlers([path], mode="audit") == [
        {
            "path": rel,
            "handler_lines": 4,
            "limit": 1,
            "baseline_exemption": True,
            "allowed_limit": 4,
        }
    ]
    assert contract_audit_core.collect_direct_queries([path], mode="audit") == [
        {
            "path": rel,
            "query_hits": 1,
            "baseline_exemption": True,
            "allowed_limit": 1,
        }
    ]


def _write_source(repo_root: Path, rel: str, lines: list[str]) -> Path:
    path = repo_root / rel
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return path
