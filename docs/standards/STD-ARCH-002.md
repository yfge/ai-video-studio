# STD-ARCH-002: API Route Handlers Stay Thin

## Intent

FastAPI route handlers should translate HTTP input and output. Business
orchestration belongs in services; persistence belongs in repositories.

## Scope

Backend endpoint modules under `ai-pic-backend/app/api/v1/endpoints/`.

## Automatic Enforcement

`python scripts/check_repo_contracts.py --mode diff <changed files>` fails when
a route handler grows beyond the current handler line limit. `--mode audit`
keeps historical debt visible.

## Evidence

Contract reports include `standard_id=STD-ARCH-002`, `handler_lines`, `limit`,
`baseline_exemption`, and the affected path.

## Repair Path

Move orchestration into a service method and move database access into a
repository method. Keep request parsing, dependency wiring, permission checks,
and response shaping in the route.

## Revision Trigger

Update this standard if the API layer gains a new routing framework, if handler
limits change, or if audit evidence shows recurring route-level orchestration
that is not caught by line count alone.
