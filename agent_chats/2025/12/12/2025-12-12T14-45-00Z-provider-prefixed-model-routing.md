---
id: 2025-12-12T14-45-00Z-provider-prefixed-model-routing
date: 2025-12-12T14:45:00Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, ai-service, routing, img2img]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
summary: "当模型 ID 带 provider 前缀时，AIServiceManager 自动锁定对应提供商并剥离前缀，避免跨厂商误用模型导致图生图失败"
---

## User Prompt

生产环境图生图日志出现：

- 参考图已通过 HTTP 下载成功；
- 但任务先走到 `provider=openai`，模型为 `google:gemini-3-pro-image-preview`，返回 `图像变换仅DALL-E 2支持`；
- 随后又请求 Google Gemini 接口。

用户怀疑是路由/兜底选择错误，要求检查并修复类似路径。

## Goals

1. 当调用方传入类似 `google:gemini-...` 的模型 ID 时，确保只在对应 provider 上执行。
2. 避免携带“外部 provider 模型 id”去尝试其他厂商，产生无意义失败日志或错误返回。
3. 统一图生图/文生图/文生文入口的模型前缀处理逻辑。

## Changes

文件：`ai-pic-backend/app/services/ai_service_manager.py`

1. 新增 `_resolve_prefer_provider_and_model(model, prefer_provider)`：

   - 若 `model` 形如 `"provider:model_id"` 且 `provider` 在已初始化 providers 中：
     - 自动将 `prefer_provider` 设为该前缀；
     - 传递给 provider 的模型为剥离前缀后的 `model_id`；
     - 若调用方已显式传入冲突的 `prefer_provider`，记录一次 warning 并以模型前缀为准。

2. 在以下统一入口开头调用该 helper，并在得到 `prefer_provider` 后仅保留该 provider：
   - `generate_text`
   - `generate_image`（文生图）
   - `image_to_image`（图生图）

效果：

- `model=google:gemini-3-pro-image-preview` 会直接锁定 `google` provider，
  不会再先尝试 `openai` 从而触发 `DALL-E 2 only` 失败。

## Validation

1. 静态走查：helper 仅影响 provider 选择和模型字符串，不改变请求参数结构。
2. 本地 `pytest` 当前基线存在大量历史失败/环境依赖问题，未尝试修复；本改动与这些失败无关。

## Next Steps

1. 由人类在本机提交本次原子改动并部署 backend 镜像。
2. 生产再次触发图生图：
   - 日志应直接显示 `provider=google model=gemini-...`；
   - 不再出现 `provider=openai model=google:...` 的失败记录。
3. 如后续视频/语音也出现带前缀模型，可再将 helper 应用到相应入口。

## Linked Commits

- 待提交：`fix(backend): respect provider-prefixed model ids in manager`
