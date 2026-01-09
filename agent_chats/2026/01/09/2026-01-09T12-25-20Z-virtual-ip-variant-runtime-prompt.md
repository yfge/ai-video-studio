---
id: 2026-01-09T12-25-20Z-virtual-ip-variant-runtime-prompt
date: "2026-01-09T12:25:20Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, prompts, virtual-ip]
related_paths:
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/services/virtual_ip/virtual_ip_image_prompts.py
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.yaml
  - ai-pic-backend/tests/unit/services/virtual_ip/test_virtual_ip_image_prompts.py
summary: "Use PromptManager runtime template for Virtual IP img2img variant prompts (unify prompt management and improve quality consistency)"
---

## User Prompt

用户追问「为什么没有用统一的提示词管理？」并希望提升图像生成质量一致性（虚拟 IP / 环境 / 分镜），继续推进统一化落地。

## Goals

- 为虚拟 IP 图生图变体引入“运行时 prompt 模板”（直接喂给图像模型），避免继续依赖散落的默认字符串。
- 保持 API 入参 `prompt`（用户变体指令）语义不变；渲染失败时自动 fallback 到原 prompt，降低行为风险。

## Changes

- 新增 PromptManager 运行时模板 `virtual_ip_image_variant`：
  - `ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.txt`
  - `ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.yaml`
- 新增渲染封装函数 `render_virtual_ip_image_variant_prompt`，统一在服务层渲染并提供 fallback：
  - `ai-pic-backend/app/services/virtual_ip/virtual_ip_image_prompts.py`
- 虚拟 IP 图生图变体生成改为使用模板渲染后的最终 prompt 构建 `ImageGenRequest`（归一化层仍负责 provider-safe 参数过滤）：
  - `ai-pic-backend/app/services/virtual_ip/image_variant_service.py`
- 新增单元测试覆盖模板渲染与缺失模板 fallback 行为：
  - `ai-pic-backend/tests/unit/services/virtual_ip/test_virtual_ip_image_prompts.py`

## Validation

- Unit tests:
  - `pytest -q tests/unit/services/virtual_ip/test_virtual_ip_image_prompts.py`
- Chrome E2E（Docker dev + Nginx，`http://localhost:8089`）：
  1. 登录：`geyunfei` / `Gyf@845261`
  2. 打开虚拟 IP「老拐」图片管理：`/virtual-ip/233525e9045146d580a1d18ef4a28161#ip-images`
  3. 在任意一张图片卡片点击「图生图」打开「图生图变体」弹窗
  4. 选择提供商/模型：`火山引擎` → `Seedream 4.5`，生成张数 `1`，点击「提交图生图任务」
  5. 跳转到 `/tasks`，确认创建任务成功并完成：`虚拟IP图生图 - 图像6`（Task ID: 545），参数中可见 `model=volcengine:doubao-seedream-4-5-251128`、`size=2K`、`count=1`

## Next Steps

- 将 `prompt_template` / `template_version` / `prompt_variables_hash` 等信息写入 Task.parameters 或 VirtualIPImage.metadata，提升可追溯性与可回放能力。

## Linked Commits

- TBD
