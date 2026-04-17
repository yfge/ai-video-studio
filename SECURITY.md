# Security

## Credentials

- Never commit provider keys, tokens, or copied `.env` files.
- Test credentials belong in runtime env only; treat them as operational secrets even if they are non-production.

## Logging

- Harness logs should carry trace ids, not secrets.
- Request body logging should stay truncated and avoid binary payload dumps.
- Browser artifacts may contain app data; keep them under `artifacts/` and out of commits.

## Uploads And Downloads

- Media persistence and export flows must keep OSS/local paths traceable without leaking secret endpoints.
- Download links and generated file paths should be treated as runtime data, not documentation constants.
