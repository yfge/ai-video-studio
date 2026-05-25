from app.services.providers.codex_auth import _redact_token_body


def test_codex_auth_redacts_token_values_from_json_error_body():
    redacted = _redact_token_body(
        '{"error":"bad","access_token":"secret-a",'
        '"tokens":{"refresh_token":"secret-b"}}'
    )

    assert "secret-a" not in redacted
    assert "secret-b" not in redacted
    assert "<redacted>" in redacted
