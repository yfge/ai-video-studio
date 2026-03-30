---
id: 2026-03-30T15-41-58Z-repo-testing-skills
date: 2026-03-30T15:41:58Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [engineering, skills, testing, docs]
related_paths:
  - .codex/skills/ai-video-studio-backend-test/SKILL.md
  - .codex/skills/ai-video-studio-backend-test/agents/openai.yaml
  - .codex/skills/ai-video-studio-frontend-test/SKILL.md
  - .codex/skills/ai-video-studio-frontend-test/agents/openai.yaml
  - .codex/skills/ai-video-studio-mcp-e2e/SKILL.md
  - .codex/skills/ai-video-studio-mcp-e2e/agents/openai.yaml
  - docs/testing/agent-validation-workflow.md
  - docs/README.md
  - tasks.md
summary: "Add repo-versioned backend/frontend/MCP testing skills and a shared validation workflow reference"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN:

# 仓库内测试 Skill 体系重规划

## Goals

1. 在仓库内版本化 3 个 testing skills，分别覆盖 backend、frontend、MCP E2E。
2. 不新增重复测试 wrapper，继续复用仓库现有测试命令和文档真源。
3. 增加一个共享验证文档，统一验证矩阵、MCP 最小检查项和 `agent_chats` 的 `## Validation` 模板。
4. 更新 `docs/README.md` 与 `tasks.md`，让协作者能发现并使用这些 skills。

## Changes

1. 新增 repo-local skills：

- `.codex/skills/ai-video-studio-backend-test`
- `.codex/skills/ai-video-studio-frontend-test`
- `.codex/skills/ai-video-studio-mcp-e2e`

2. 为 3 个 skills 补齐正式 `SKILL.md` 内容：

- backend skill 固定 backend quick/full/targeted/diagnostic 的命令矩阵，并明确 `run_pytest.py` 只是辅助入口。
- frontend skill 固定 `npm run lint` 为最低门槛，并把 `npm run test` / `npm run build` 设计为风险驱动加跑项。
- MCP skill 固定 DevTools SOP、fallback 规则和 `agent_chats` 输出契约，并要求每次先读取 `AGENTS.md`，不在 skill 内重复硬编码测试账号。

3. 新增共享验证文档：

- `docs/testing/agent-validation-workflow.md` 统一显式调用方式、验证矩阵、MCP 最小检查项、`## Validation` 模板和“不要嘴硬”记录规则。

4. 更新索引和任务板：

- `docs/README.md` 增加 testing skills 与共享验证文档入口。
- `tasks.md` 新增“测试 / MCP 验证流程 Skill 化”工程化条目，并记录已完成项与后续自动发现待办。

## Validation

1. Skill 结构校验：

- `python /Users/geyunfei/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-backend-test` -> `Skill is valid!`
- `python /Users/geyunfei/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-frontend-test` -> `Skill is valid!`
- `python /Users/geyunfei/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-mcp-e2e` -> `Skill is valid!`

2. 针对改动文件的格式/钩子校验：

- `pre-commit run --files .codex/skills/... docs/README.md docs/testing/agent-validation-workflow.md tasks.md` -> passed

3. Browser / MCP validation:

- Not applicable for application behavior. This change only adds repo-local skills and documentation; no frontend/backend runtime path changed.

4. Additional repo gate:

- `./docker/build_prod_images.sh` -> passed
- Backend image pushed: `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:f4f3074`
- Frontend image pushed: `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-frontend:f4f3074`

## Next Steps

1. If future work needs automatic skill discovery, add a dedicated sync/install mechanism instead of changing the v1 repo-local contract.
2. If explicit forward-testing with fresh agents is required later, request delegation explicitly before using sub-agents.

## Linked Commits

- pending (this commit)
