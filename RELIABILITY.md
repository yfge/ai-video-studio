# Reliability

## Runtime Modes

- `lite`: SQLite, eager Celery, optional mock providers. This is the default harness mode.
- `dev`: full MySQL/Redis/Celery stack.

## Harness Entry Points

- `scripts/harness/bootstrap_worktree.sh`
- `python scripts/harness/doctor.py --run-id <id>`
- `python scripts/harness/browser_flow.py --scenario <name> --run-id <id>`
- `python scripts/harness/run_golden_path.py --scenario <name> --run-id <id>`
- `python scripts/harness/trace_run.py --run-id <id>`
- `python scripts/harness/trace_task.py --task-id <id>`

## Logging And Trace

- Backend responses expose `X-Request-ID` and `X-Harness-Run-ID`.
- Frontend API wrappers send `X-Client-Request-ID` and `X-Harness-Run-ID`.
- Structured JSONL logs are written to `logs/ai-video-studio.jsonl`.
- Harness artifacts are written to `artifacts/runs/<run_id>/`.

## Browser Evidence Policy

- Preferred order: Chrome DevTools MCP, then Playwright, then Selenium.
- Any fallback must be written to artifacts and the validation summary.
- Do not claim Chrome verification when the run actually used a fallback engine.
