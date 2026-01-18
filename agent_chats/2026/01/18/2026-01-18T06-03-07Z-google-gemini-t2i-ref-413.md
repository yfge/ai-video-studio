---
id: 2026-01-18T06-03-07Z-google-gemini-t2i-ref-413
date: 2026-01-18T06:03:07Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, provider, google]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/ui_metadata.py
  - ai-pic-backend/app/services/providers/google_provider/helpers.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
  - ai-pic-backend/tests/unit/test_google_provider_helpers.py
summary: "Mitigated Google/Gemini txt2img reference image 413 risk by limiting ref count, compressing inline images, and surfacing UI notes."
---

## User Prompt

全局检查文生图/图生图提示词规范，并针对不同 provider 优化参数与 UI；优先处理 Google/Gemini 参考图可能触发 413 的问题；原子化提交并更新 tasks.md。

## Goals

- 降低 Google/Gemini 文生图携带参考图时的 413 风险（限制张数/压缩/提示）。
- 保持 provider-aware normalize/audit 语义一致，避免“输入展示但被丢弃”。
- 补齐单元测试覆盖并完成浏览器端到端核验。

## Changes

- `normalize_image_gen_request`：Google/Gemini 文生图 `reference_images` 超过 4 张时截断并写入 warnings/dropped_fields。
- `google_provider/helpers.py`：下载参考图后在内联前进行 downscale + JPEG 重新编码压缩（默认目标约 220KB、最大边 512）。
- `build_image_gen_ui_metadata`：对 Google/Gemini 增加“参考图内联上传可能 413”的模型提示。
- 新增/更新单测覆盖：Google 文生图参考图截断、内联图片压缩逻辑。

## Validation

- Backend tests: `cd ai-pic-backend && pytest -q tests/unit tests/services tests/scripts`
- Prod build: `./docker/build_prod_images.sh`
- Chrome (MCP) E2E:
  - 使用 `geyunfei / Gyf@845261` 登录
  - 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`
  - 在「模型提示」中确认出现 “Google/Gemini 参考图会以内联方式上传…避免 413…” 提示

## Next Steps

- 前端：将 reference_images 动态输入/限制扩展到分镜文生图等入口（按 image_gen 能力隐藏/限制）。
- Docs：补齐 provider×domain 参数兼容矩阵（含 reference_images 张数/尺寸建议与降级策略）。

## Linked Commits

- fix(backend): mitigate google t2i refs 413
