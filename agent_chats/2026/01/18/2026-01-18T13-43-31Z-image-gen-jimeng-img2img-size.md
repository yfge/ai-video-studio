---
id: 2026-01-18T13-43-31Z-image-gen-jimeng-img2img-size
date: "2026-01-18T13:43:31Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, providers]
related_paths:
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/providers/jimeng_provider.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
  - docs/image-gen-provider-matrix.md
  - tasks.md
summary: "让 Jimeng 图生图透传 size，并在 provider 侧映射为 width/height，避免 UI 选项被静默丢弃。"
---

## User Prompt

- 全局检查文生图/图生图提示词规范与 provider 参数一致性，并按 provider 进一步优化（原子化分布提交）。

## Goals

- 修复 provider 参数不一致：UI 侧有 `size_options`，但后端 Jimeng img2img 静默丢弃 `size`。
- 保持 provider-aware 归一化层行为可验证（unit tests + Chrome 自测 + Docker prod build）。

## Changes

- 允许 Jimeng `image_to_image` 透传 `size`：`supported_ai_manager_keys()` 白名单加入 `size`。
- Jimeng provider `image_to_image()` 支持 `size`：对 `size` 做 normalize 校验并映射为 `width/height`，写入请求与响应 metadata。
- 单测补齐：验证 `build_ai_manager_call()` 对 Jimeng img2img 保留 `size` 且过滤 `aspect_ratio`。
- 文档/任务看板同步：更新 provider matrix 备注与 `tasks.md` 进度项。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome（localhost:8089）：
  - 登录后进入 `http://localhost:8089/virtual-ip/233525e9045146d580a1d18ef4a28161`，点击任一“图生图”打开「图生图变体」弹窗，确认模型列表与尺寸输入正常加载。
  - 通过 DevTools Console 请求 `/api/v1/ai/models/available?model_type=image_to_image`，确认当前环境未启用 Jimeng（列表仅含 google/keling/openai/volcengine），因此未能在 UI 里实际提交 Jimeng img2img 任务；Jimeng 的 `size` 透传由单测覆盖。

## Next Steps

- 若需端到端验证 Jimeng：补齐本地 Jimeng provider 配置（不在仓库提交任何密钥），并在图生图弹窗选择 Jimeng 提交 1 次任务，抓包确认 payload/metadata 的 `size→width/height` 生效。
- 继续梳理其它 provider 的 img2img 参数差异（如 Seedream 多图生图、尺寸/比例校验落盘）。

## Linked Commits

- TBD

