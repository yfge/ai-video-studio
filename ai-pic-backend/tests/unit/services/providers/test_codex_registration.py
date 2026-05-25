from types import SimpleNamespace

from app.services.providers import codex_registration


def _manager():
    return SimpleNamespace(
        provider_classes={},
        providers={},
        config=SimpleNamespace(providers={}, provider_weights={}),
    )


def test_codex_registration_requires_explicit_auth_path(monkeypatch):
    monkeypatch.setattr(codex_registration.settings, "CODEX_AUTH_PATH", None)
    manager = _manager()

    codex_registration.install_codex_provider(manager)

    assert "codex" not in manager.providers


def test_codex_registration_installs_when_auth_path_exists(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    auth_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(codex_registration.settings, "CODEX_AUTH_PATH", str(auth_path))
    monkeypatch.setattr(codex_registration.settings, "CODEX_RESPONSES_URL", None)
    monkeypatch.setattr(codex_registration.settings, "CODEX_DEFAULT_MODEL", "gpt-5.4")
    manager = _manager()

    codex_registration.install_codex_provider(manager)

    assert "codex" in manager.providers
    assert manager.config.providers["codex"].api_key == str(auth_path)
    assert manager.config.provider_weights["codex"].enabled is True
