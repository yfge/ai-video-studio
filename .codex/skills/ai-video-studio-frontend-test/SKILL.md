---
name: ai-video-studio-frontend-test
description: Frontend validation workflow for ai-video-studio. Use when changing Next.js pages, components, hooks, API client code, route guards, auth flows, or when deciding whether lint, tests, build, and browser verification are required. Chooses between mandatory lint, conditional frontend tests, and risk-driven builds while deferring user-visible flow checks to the MCP E2E skill.
---

# AI Video Studio Frontend Test

Use this skill to decide the right frontend validation depth without diluting the minimum gate. `npm run lint` is the baseline; `npm run test` and `npm run build` are added when the change risk justifies them.

## Read First

- `AGENTS.md`
- `docs/testing/agent-validation-workflow.md`
- `README.md`
- `ai-pic-frontend/package.json`

## Command Matrix

- Always run the minimum frontend gate:
  ```bash
  cd ai-pic-frontend && npm run lint
  ```
- Add tests when the change touches hooks, state logic, utilities, API client code, component behavior, or existing test files:
  ```bash
  cd ai-pic-frontend && npm run test
  ```
- Add a build for route, layout, config, auth, hydration, bundling, or SSR-sensitive changes:
  ```bash
  cd ai-pic-frontend && npm run build
  ```

## Decision Rules

- Treat `npm run lint` as non-optional for frontend changes.
- Add `npm run test` whenever the change modifies behavior rather than only copy, docs, or passive styling.
- Add `npm run build` when the change can affect routing, layouts, server/client boundaries, config, auth redirects, or hydration.
- `npm run build` is a risk-driven frontend gate. It does not replace the repository-wide `./docker/build_prod_images.sh` requirement before commit.
- If the change is user-visible or login-related, pair this skill with `ai-video-studio-mcp-e2e`.

## Reporting Requirements

- Report the exact frontend commands that were run and why they were sufficient.
- When tests or build were omitted, state the risk assessment explicitly.
- In `agent_chats`, put frontend evidence under `## Validation` before or alongside browser validation notes.
- Do not collapse lint, tests, build, and browser checks into a vague sentence like "frontend verified".

## Explicit Invocation

Use this skill explicitly from the repo path:

```text
Use $ai-video-studio-frontend-test at /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-frontend-test
```
