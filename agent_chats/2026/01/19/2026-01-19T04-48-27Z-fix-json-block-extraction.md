---
id: 2026-01-19T04-48-27Z-fix-json-block-extraction
date: 2026-01-19T04:48:27Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, parsing, storyboard]
related_paths:
  - ai-pic-backend/app/utils/json_utils.py
  - ai-pic-backend/tests/unit/test_story_parser.py
summary: "Improve extract_json_block to take the first balanced JSON block, avoiding LLM echo text breaking parsing."
---

## User Prompt

全流程测试短剧；发现分镜生成卡住/输出不稳定，需要修复并继续。

## Goals

- 让 `extract_json_block()` 能可靠解析 LLM 返回的 JSON，即使 code fence 内附带了额外提示文本/示例 JSON。
- 为分镜（Storyboard）等依赖 JSON schema 的链路提升稳定性。

## Changes

- 在 `extract_json_block()` 中改为提取第一个“括号配平”的 JSON 块，避免被末尾示例 JSON 污染（`ai-pic-backend/app/utils/json_utils.py`）。
- 增加单测覆盖 “code fence 内追加示例 JSON” 场景（`ai-pic-backend/tests/unit/test_story_parser.py`）。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- `./docker/build_prod_images.sh`

## Next Steps

- 重启 `ai-video-celery-worker` 使解析逻辑生效，重新生成 storyboard 后继续图像/视频 E2E。

## Linked Commits

- (pending)
