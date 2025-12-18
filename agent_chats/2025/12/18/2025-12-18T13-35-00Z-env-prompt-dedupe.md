---
id: 2025-12-18T13-35-00Z-env-prompt-dedupe
date: 2025-12-18T13:35:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Deduplicate environment generation prompt to avoid repeating description when extra prompt matches."
---

## User Prompt

- 环境管理中的提示词预览重复描述，需检查模板。

## Goals

- 在环境文生图/图生图的提示词生成中，避免将与环境描述相同的额外提示重复拼接。

## Changes

- `_compose_environment_prompt` 现在在追加 `extra` 前进行去重：若与 `env.description` 一致则跳过，只保留一次描述。

## Validation

- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/story_structure.py`（通过）。
- `bash docker/build_prod_images.sh`（通过，镜像 tag ce2f2af）。
- 未重跑全量 `pytest`（基线仍有既有失败），依赖 pre-commit backend quick gate。

## Next Steps

- 部署后端/worker 至镜像 `ce2f2af`；重新观察任务详情中的 LLM Prompt Preview，应不再重复描述。

## Linked Commits

- (pending)
