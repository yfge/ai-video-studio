# STD-ARCH-003: Legacy Choke Points Are Not Expansion Points

## Intent

The repository tolerates historical hotspots as baseline debt. New work should
not add dependencies on those files unless the change is reducing or splitting
the hotspot itself.

## Scope

Current choke points:

- `ai-pic-backend/app/services/ai_service_manager.py`
- `ai-pic-backend/app/services/script_agent.py`

## Automatic Enforcement

`python scripts/check_repo_contracts.py --mode diff <changed files>` flags new
references to the current choke-point patterns in backend and frontend source.

## Evidence

Contract reports include `standard_id=STD-ARCH-003`, the matched pattern, and
the affected path.

## Repair Path

Depend on focused services, adapters, or repositories instead. If the only
reasonable path is through a choke point, split the relevant behavior out first
or document why the change reduces the hotspot.

## Revision Trigger

Update this standard when a choke point is retired, split, renamed, or when a
new hotspot becomes visible in audit reports.
