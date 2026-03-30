# Agent Validation Workflow

This document is the shared reference for the repo-local testing skills under `/.codex/skills/`.

## Explicit Skill Invocation

These skills are versioned in the repository and are meant to be invoked explicitly by path:

- `Use $ai-video-studio-backend-test at /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-backend-test`
- `Use $ai-video-studio-frontend-test at /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-frontend-test`
- `Use $ai-video-studio-mcp-e2e at /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-mcp-e2e`

## Validation Matrix

| Change type                                                                 | Minimum validation                                                             | Escalate when                                                                |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| Backend service, repository, prompt, validator                              | `cd ai-pic-backend && pytest <path-or-node> -v` or `python run_tests.py quick` | Multiple modules, shared contracts, task orchestration, or uncertainty       |
| Backend API, auth, model, migration                                         | `cd ai-pic-backend && pytest`                                                  | Always pair with browser validation when the change is user-visible          |
| Frontend page, component, hook, API client                                  | `cd ai-pic-frontend && npm run lint`                                           | Add `npm run test` for behavior/state changes                                |
| Frontend route, layout, config, auth redirect, hydration risk               | `cd ai-pic-frontend && npm run lint` plus `npm run build`                      | Pair with MCP E2E for user-visible flows                                     |
| Login, AI generation, image/video flow, or any frontend/backend interaction | Relevant backend/frontend checks plus MCP E2E                                  | Do not treat browser validation alone as sufficient                          |
| Docs or testing skills only                                                 | Validate changed docs and skills directly                                      | Browser validation is not required unless the task also changes app behavior |

## MCP Minimum Checklist

When MCP E2E is required:

1. Read `AGENTS.md` for the current validation requirement and test account.
2. Open the local app and log in when needed.
3. Execute the smallest real path that proves the change.
4. Check Console for errors or warnings that materially affect the path.
5. Check the decisive Network request or response.
6. Record the path and evidence in `agent_chats`.

Fallback policy:

- Retry Chrome DevTools once before switching tools.
- If DevTools is still unavailable, use Selenium, Playwright, or API/curl reproduction.
- When falling back, record why MCP failed and how the alternate reproduction corrected or confirmed the hypothesis.

## `agent_chats` Validation Template

Use this structure inside `## Validation`:

```md
1. Local checks:

- `cd ... && <command>` -> pass/fail summary

2. Browser or MCP validation:

- Entry URL:
- User path:
- Console:
- Network:
- Result:

3. Conflict signals and corrections:

- Initial assumption:
- Contradicting evidence:
- Reproduction and fix:
- Final verified state:
```

Do not write vague summaries such as "已验证" or "looks good".

## "不要嘴硬" Recording Rule

If logs, requests, or user evidence contradict your guess:

- state the uncertainty explicitly
- reproduce with a real request or browser path
- record the wrong assumption
- record the evidence that disproved it
- record the corrective action and rerun result

This applies to both success and failure cases.
