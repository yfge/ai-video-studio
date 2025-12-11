---
id: 2025-12-11T21-58-55Z-volcengine-img2img-ref-fix
date: 2025-12-11T21:58:55Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, ai, volcengine, storyboard]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - docs/api/volcengine-image-stream.md
summary: "Relax Volcengine img2img reference handling and align with Seedream streaming docs"
---

## User Prompt

分镜和虚拟 IP 图生图参考图没有真正参与生成，特别是 Seedream 4.5 / Volcengine 在有坏参考图 URL（例如 symmetrical_architecture_shot.jpg）时会直接失败并 fallback 成文生图。希望修复后端逻辑，保证多参考图图生图正确使用用户上传的图片，并按照 volcengine-image-stream 文档检查实现；提交变更并保证 build 没问题。

## Goals

- 让分镜页和虚拟 IP 图生图在 Seedream 4.5 场景下真正使用用户选择的多张参考图。
- 在存在 404/坏参考图 URL 时容错，而不是整体失败并退化为文生图。
- 对齐 docs/api/volcengine-image-stream.md 对 doubao-seedream-4.5 的参数约束（参考图数量 + 生成图片数量 ≤15、sequential_image_generation 等）。
- 保证改动不会破坏后端构建和运行（至少语法与核心路径正常）。

## Changes

- Updated `ai-pic-backend/app/services/ai_service_manager.py`:
  - Reworked `image_to_image` base64 预加载逻辑为“按 URL 逐个下载、局部容错”的模式：
    - 对 `[image_url] + extra_images` 去重后逐个 GET。
    - 单个 URL 404 或网络错误只记录 `image_to_image base64 preload skip url=...` warning，跳过该图而不再让整个预加载失败。
    - 只要有至少一张图片成功，组装 `data:image/...;base64,...` 列表传入 `kwargs["base64_images"]`，支持最多 14 张参考图。
    - 若所有参考图都失败则记录 warning，但不阻断 Provider 内部的兜底逻辑。
- Updated `ai-pic-backend/app/services/providers/volcengine_provider.py`:
  - Aligned `image_to_image` implementation with Seedream 4.5 文档（包括 streaming 文档约束）：
    - 优先使用上游传入的 `base64_images`（最多 14 张），避免在 Provider 内重复下载参考图。
    - 当没有 `base64_images` 时，支持直接传 URL 的路径，对 `[image_url] + extra_images` 去重后逐个 GET，针对 404/网络错误记录 `Volcengine image_to_image skip bad ref url=...` 并跳过，容忍部分参考图不可用。
    - 如果最终没有任何可用参考图，则返回 `AIResponse(success=False, error="没有可用的参考图用于图生图")`，交由上游决定是否走 text-to-image fallback。
    - 按 `volcengine-image-stream.md` 约束计算 `max_images`：在 `n>0` 的基础上结合参考图数量做 `total_refs + max_images <= 15` 的裁剪。当参考图已经占满上限时强制只生成一张。
    - 显式设置 `"stream": False`，走非流式输出路径，和现有业务处理逻辑对齐。
  - 保持 Ark 接口为 `POST /api/v3/images/generations`，`response_format: "url"`，`watermark` 透传布尔开关，与文档一致。
- Confirmed `docs/api/volcengine-image-stream.md` already documents：
  - Seedream 4.5 多图/单图/文生图的能力说明。
  - `sequential_image_generation`、`sequential_image_generation_options.max_images` 以及“参考图数量 + 最终生成的图片数量 ≤ 15”的约束。
  - 当前 Provider 实现与文档在参数和约束上保持一致，无需额外文案修改。

## Validation

- Backend runtime validation（Docker dev stack）：
  - 重启 `ai-video-backend` 与 `ai-video-celery-worker` 容器，确认服务启动正常。
  - 使用用户提供的 Token 和请求体，直接通过 curl 调用：
    - `POST http://localhost:8000/api/v1/scripts/19/storyboard/generate-images`
    - `model: "volcengine:seedream-4.5"`、`frames: [6]`、`count: 1`，`reference_images` 中包含多张 `/uploads/*.png` 与一张虚拟 IP OSS 图。
  - 观察 Celery 日志：
    - `[SBIMG] task start | script_id=19 ... model=volcengine:seedream-4.5 count=1`
    - `[SBIMG] frame refs | idx=6 total_refs=9 frame_refs=9 payload_refs=4 char_anchor=3 env_refs=4`
    - `image_to_image base64 preload skip url=http://ai-video-backend:8000/symmetrical_architecture_shot.jpg error=Client error '404 Not Found' ...`
    - `image_to_image base64 preload skip url=http://ai-video-backend:8000/neon_light_projection_on_concrete.jpg error=Client error '404 Not Found' ...`
    - `HTTP Request: POST https://ark.cn-beijing.volces.com/api/v3/images/generations "HTTP/1.1 200 OK"`
    - `LLM Response | task=image_to_image provider=volcengine model=seedream-4.5 status=success ...`
    - 随后下载 Ark 返回图片并持久化到 `./uploads/46a00eaa...png`，最终将分镜第 6 帧的 `image_url` 更新为新的 storyboard OSS 地址。
  - 验证重点：
    - Seedream 图生图调用没有再出现 `image_to_image fallback: using text-to-image without reference`。
    - 404 的历史占位图（`symmetrical_architecture_shot.jpg`、`neon_light_projection_on_concrete.jpg`）只被记录并跳过，不再影响整次图生图。
    - 有效的 `/uploads/*.png` 参考图和虚拟 IP 图成功参与图生图请求。
- Build / syntax check：
  - 运行 `python -m compileall ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/providers/volcengine_provider.py`，确认改动文件无语法错误。
  - 之前全量 `pytest -q` 在当前分支上存在大量既有失败（主要集中在用户管理和迁移相关测试），这些在本次改动前已存在，且与本次 Volcengine/Storyboard 改动无直接关联，因此没有在本次工作中尝试全部修复。

## Next Steps

- 建议你在浏览器中登录 `http://localhost:8089/episodes/12/storyboard`（用户 `geyunfei`），在分镜第 6 帧重新勾选多张参考图并选择 Seedream 4.5 进行图生图，主观确认生成结果是否更贴近参考图风格和构图。
- 如需进一步提高控制力，可以考虑在 UI 里区分“硬参考图”（必须使用）和“软参考图”（可跳过），并在 Storyboard 管道中分别传递，以便后续在 Provider 层做更细粒度的权重或优先级控制。
- 若希望 IP 图文生图在 Google/Gemini 路径下也做同样的容错和多图控制，可以补充一条专门针对 Google Provider 的验证用例并视需要做文档补充。

## Linked Commits

- `fix(backend): relax volcengine img2img refs`

