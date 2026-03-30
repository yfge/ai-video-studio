---
name: ai-video-studio-mcp-e2e
description: Chrome DevTools E2E workflow for ai-video-studio. Use when a change affects login, frontend/backend integration, AI generation, image or video flows, or any user-visible path that AGENTS.md requires to be verified in a real browser. Reads AGENTS.md for the current validation policy and account, follows the shared validation matrix, captures console and network evidence, and produces an agent_chats-ready Validation section.
---

# AI Video Studio MCP E2E

Use this skill to execute the repository's required real-browser verification path. Do not repeat test credentials from memory; read the current account and mandatory validation requirements from `AGENTS.md` every time.

## Read First

- `AGENTS.md`
- `docs/testing/agent-validation-workflow.md`
- Relevant feature docs or recent `agent_chats` entries for the area being changed

## Standard Flow

1. Read `AGENTS.md` to confirm the current browser-validation requirement and test account.
2. Open the local app entrypoint and log in if the flow requires auth.
3. Run the smallest real path that proves the changed behavior, not just a page refresh.
4. Inspect Console for errors or warnings that materially affect the path.
5. Inspect the key Network request or response that proves the backend/frontend contract.
6. Record the exact path, evidence, and result in `agent_chats`.

## Minimum Checks

- Confirm the route or dialog actually loads.
- Confirm the intended user action can be triggered.
- Confirm the decisive Console or Network evidence for the changed behavior.
- Confirm the final user-visible result, including failure states when relevant.
- If the change spans backend and frontend, pair this skill with the backend or frontend testing skill instead of treating browser validation as sufficient by itself.

## Fallback Rules

- Default to Chrome DevTools MCP.
- If the DevTools transport fails, retry with a fresh page or reconnect once before switching tools.
- If MCP remains unavailable, use Selenium, Playwright, or direct API/curl reproduction only after stating why the browser flow could not continue.
- When a fallback is used, write the reason, reproduction path, and corrective interpretation in `agent_chats`. Do not silently downgrade and still write "Chrome verified".

## Validation Output Contract

Produce `agent_chats`-ready validation notes that include:

- environment and entry URL
- actual browser path
- decisive Console and Network observations
- success or failure result
- any conflict signal, wrong assumption, and correction that happened during debugging

## Explicit Invocation

Use this skill explicitly from the repo path:

```text
Use $ai-video-studio-mcp-e2e at /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-mcp-e2e
```
