# STD-NARRATIVE-001: Generic narrative consistency stays topic neutral

## Intent

The V5 consistency core must execute Story-scoped schemas without learning a
fixed topic vocabulary or taking dependencies on application orchestration.

## Scope

`ai-pic-backend/app/services/narrative_consistency/`

## Automatic enforcement

`python scripts/check_repo_contracts.py` rejects core imports from API, models,
repositories, providers, Story Novel services, FastAPI, or SQLAlchemy. It also
rejects the V2-V4 state vocabulary `location_transitions`, `knowledge_grants`,
`possessions`, and `owner_id` inside the core.

## Evidence and repair

Reports list the file, forbidden imports, and legacy state terms. Move
persistence/provider/orchestration code to Story Novel services and put legacy
translation in a version-specific adapter rather than adding an exception.

## Revision trigger

Update this standard when a production V5 failure proves another application or
topic dependency can enter the core undetected.
