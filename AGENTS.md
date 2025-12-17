# Agents Guidance for ai-video-studio

This document is the single source of truth for every coding assistant (Claude Code, Codex, Gemini, Cursor, etc.) that collaborates on this repository. Keep this file authoritative and avoid duplicating instructions elsewhere; all agent-specific instruction files must reference this document.

## Instruction Precedence & Mirrors

- Respect instruction order: system / developer → user → this file → everything else.
- The following files must be kept as symlinks (or exact copies) of `AGENTS.md`: `CLAUDE.md`, `GEMINI.md`.
- When this file is updated, ensure mirrored files stay in sync within the same commit.

## Atomic Commit Discipline (Critical)

- Stage and commit every atomic change **immediately** after completing validation; do not carry pending edits while starting new tasks.
- Pair each commit with its corresponding `agent_chats` ledger entry inside the same commit.
- Keep the working tree clean at all times—no stray modifications or half-staged files between commits.
- If a change cannot be validated yet, park it on a feature branch instead of leaving it unstaged.

## Mission & Scope

ai-video-studio is an AI-powered virtual IP production platform composed of:

- `ai-pic-backend/`: FastAPI + SQLAlchemy service orchestrating AI image/video generation, story workflows, and OSS persistence.
- `ai-pic-frontend/`: Next.js 15 (App Router) application for operators to manage virtual IPs, galleries, stories, episodes, and scripts.

The codebase must remain production-grade, auditable, and reproducible. Every meaningful code change needs traceable documentation, automated validation, and a matching ledger entry.

## Repository Expectations

- **Backend layout**: `app/` (core, api, models, schemas, services), `alembic/`, `tests/`, `scripts/`. Keep service/business logic in `app/services/`; APIs remain thin.
- **Frontend layout**: `src/app/`, `src/components/`, `src/lib/`, `src/utils/`. Keep UI state colocated with features; limit global state.
- **Testing**: Maintain comprehensive pytest coverage (`ai-pic-backend`) and Next.js lint rules. Backend changes must pass `pytest`; frontend changes must pass `npm run lint`.
- **Docs**: Update README / guides when behaviour changes. Architecture decisions belong under `docs/` (create if missing) and should be cross-linked from agent chats.
- **Tasks.md is canonical**: Maintain the live task board in `tasks.md` (use `[ ]` for未完成、`[x]`为已完成). Merge/append所有任务到该文件，禁止再用旧的 `task.md`。

## Agent Collaboration Ledger (`agent_chats/`)

We operate with the same rigor as the reference repositories (`talkReplay`, `orion`, `ai-shifu`, `talkreplay.com`). Follow these rules exactly:

1. Directory structure: `agent_chats/YYYY/MM/DD/`. Create folders as needed; never place files directly under `agent_chats/`.
2. File naming: `YYYY-MM-DDTHH-MM-SSZ-kebab-topic.md` (UTC timestamps). Example: `2025-10-23T07-30-03Z-backend-fastapi-refactor.md`.
3. YAML frontmatter is **required**:
   ```yaml
   ---
   id: 2025-10-23T07-30-03Z-backend-fastapi-refactor
   date: 2025-10-23T07:30:03Z
   participants: [human, codex]
   models: [gpt-4o-mini]
   tags: [backend, api]
   related_paths:
     - ai-pic-backend/app/api/v1/virtual_ip.py
   summary: "Refined virtual IP endpoints and added validation"
   ---
   ```
4. Body sections (all mandatory and in order):
   - `## User Prompt`
   - `## Goals`
   - `## Changes`
   - `## Validation`
   - `## Next Steps`
   - `## Linked Commits`
5. Reference all touched files under `related_paths` using repository-relative paths.
6. Every commit that touches code in `ai-pic-backend/`, `ai-pic-frontend/`, `scripts/`, or modifies this document must include at least **one** staged ledger entry.
7. **Atomic commits are non-negotiable:** after completing each atomic piece of work, stage the matching files and commit immediately. Keep commits minimal, focused, and easily traceable with their corresponding ledger record.
8. Keep `agent_chats/` clean: no unstaged edits, no binary files, redact secrets, prefer ASCII.

The helper `scripts/check_agent_chats.py` (wired into pre-commit) enforces naming, frontmatter, and section requirements. The hook fails when code changes lack a matching ledger entry or when ledger files are malformed.
- 在提交前执行 `./build_prod_images.sh`，确保生产镜像可构建；构建失败需先修复后再提交。

## Pre-Commit Gates & Quality Bar

We adopt a strict workflow similar to the reference projects:

- Install `pre-commit` locally (`pip install pre-commit`) and run `pre-commit install` once.
- Hooks run automatically:
  - `ruff`, `isort`, and `black` for Python under `ai-pic-backend/`.
  - `prettier` for Markdown/JSON/YAML/TypeScript styles.
  - `scripts/check_agent_chats.py` for ledger compliance.
  - `pytest` (backend quick gate) whenever staged files live under `ai-pic-backend/`.
  - `npm run lint` when staging files under `ai-pic-frontend/src/`.
  - `commitlint` enforces Conventional Commit subjects on commit messages.
- Do **not** circumvent hooks. Fix violations or explicitly document why a file is exempt (rare, with user approval).

## Backend Workflow (`ai-pic-backend/`)

1. Use a Python 3.11+ environment.
2. Install dependencies: `pip install -r requirements.txt -r requirements-test.txt`.
3. Run tests before every commit touching backend code:
   ```bash
   cd ai-pic-backend
   pytest
   ```
4. Additional diagnostics available:
   - `python run_tests.py quick` for lightweight checks.
   - `python manage.py migration status` before/after schema work.
   - `pytest tests/test_fastapi_full_flow.py::test_fastapi_full_image_generation_flow -v` for the full AI pipeline.
5. Update docs (`TESTING_GUIDE.md`, `MIGRATION_SYSTEM_GUIDE.md`, etc.) when workflows change.

## Frontend Workflow (`ai-pic-frontend/`)

1. Node.js 20 LTS + npm.
2. Install dependencies: `cd ai-pic-frontend && npm install`.
3. Validate UI work:
   - `npm run lint`
   - `npm run test` (add/maintain tests as the suite grows)
   - `npm run dev` for local verification prior to committing.
4. Keep Tailwind tokens consistent; avoid ad-hoc styling. Update component docs if behaviour changes.

## Commit & Branch Policy

- Conventional Commit messages (lowercase type, ≤72 chars). Examples: `feat(backend): add retry policy`, `fix(frontend): guard auth redirects`.
- **Commit immediately after each atomic change; never postpone commits or leave work-in-progress unstaged.**
- **Atomic commits are mandatory:** once a work item is complete, commit it before starting anything else. Do not batch unrelated tasks into a single commit.
- Always stage the matching `agent_chats` entry with the code changes.
- Prefer focused commits; large changes should be split logically and each accompanied by its own ledger entry.
- Treat `main` as protected: work in topic branches (`feat/*`, `fix/*`, `chore/*`) when collaborating.

### CRITICAL — Minimal Atomic Commits & Clean Workspace

- Minimal atomic commits only: one logical change per commit, paired with its ledger entry. Do not bundle unrelated edits.
- **Keep the repository clean in real time: commit each atomic unit the moment it is complete; never leave stray work sitting unstaged.**
- Minimize diff scope: touch only the files/lines necessary for the task; avoid opportunistic refactors or drive‑by style changes.
- Keep the working tree clean: before each commit ensure there are no stray unstaged edits. Do not leave the repo dirty between steps.

## Delivery Checklist for Agents

Before yielding work back to the user:

**CRITICAL — Chrome self-test (MCP):** After completing each functional change, run a quick end-to-end verification using Chrome via MCP/DevTools; record the scenario in `agent_chats` before marking the task done. Use test account `geyunfei` / `Gyf@845261` to log in. Do not defer runs due to model cost—assume budget is OK.

**CRITICAL — 不要嘴硬:** 当日志、请求结果或用户现场信息与你的推断不一致时，**优先承认不确定性和可能的误判，先复盘/排查，再给结论**；禁止反复坚持“代码没问题”“环境有问题”这类口头判断。遇到冲突信号时，要主动用真实请求（curl、自测脚本、浏览器实际路径）复现问题，并在 `agent_chats` 的 `## Validation` 段明确记录你是如何验证和纠正自己的。

1. Ensure relevant tests (`pytest`, `npm run lint`, targeted suites) pass locally.
2. Verify `pre-commit run --all-files` is clean or document any justified skips.
2.1 Ensure the working tree is clean (no unstaged changes) at commit time.
3. Confirm new/updated `agent_chats` entries satisfy format rules and describe intent, changes, validation, and follow-ups.
4. For任何涉及前后端联动、登录、AI 调用/图像生成等功能改动，**必须在真实浏览器（推荐 Chrome）中完成至少一次端到端路径验证**，可以通过 DevTools 自动化/远程调试完成；在 `agent_chats` 的 `## Validation` 段中明确记录所走用例（例如使用 Seedream 4.5 在虚拟 IP 图像页生成图片的步骤和结果）。
5. Summarise remaining risks or TODOs in the agent response。
6. Never commit secrets or credentials; reference environment variables instead.

Following these conventions keeps the repo aligned with the rigor demonstrated in `talkReplay`, `orion`, `ai-shifu`, and `talkreplay.com`. Deviations require explicit user approval and should be documented in the ledger and commit messages.
