# File Size And Structure Limits

These limits are strict defaults. Exceptions require explicit approval and must not become the new norm.

## File Size Limits

- Python files: target `150-250` lines, hard limit `300`
- Backend service files: target `150-220` lines, hard limit `250`
- TypeScript and TSX files: target `100-200` lines, hard limit `250`
- Next.js page files: target `100-180` lines, hard limit `200`
- FastAPI route handlers: hard limit `50` lines

## Mandatory Refactor Triggers

Refactor before continuing when any of these are true:

- a file exceeds its limit
- a function exceeds 50 lines
- the same logic appears in 3 or more places
- nested conditionals go deeper than 3 levels
- a module becomes a god object
- import cycles appear

## Backend Structure Rules

- Keep endpoints thin. Push business logic into services.
- Use repositories for database access.
- Keep providers, validators, repositories, and services separate.
- Avoid direct `.query(...)` outside repository modules.

## Frontend Structure Rules

- Keep pages focused on route wiring, layout, and data coordination.
- Move reusable state into hooks or context before a page grows further.
- Place reusable primitives in `src/components/ui/`.
- Place cross-feature components in `src/components/shared/`.
- Place feature-specific components in `src/components/features/<domain>/`.

## Legibility Goal

The point of these limits is not aesthetics. Small, focused files make the repository easier for agents to search, reason about, validate, and refactor without spreading entropy.
