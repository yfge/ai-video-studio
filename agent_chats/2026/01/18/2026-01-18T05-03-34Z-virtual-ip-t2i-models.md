---
id: 2026-01-18T05-03-34Z-virtual-ip-t2i-models
date: 2026-01-18T05:03:34Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image_gen, virtual_ip]
related_paths:
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageGeneration.ts
summary: "Fix virtual IP txt2img model list to fetch text_to_image models"
---

## User Prompt

检查所有生图提示词/参数一致性；在选择不同 provider 时动态加载输入/提示信息；按原子化提交推进。

## Goals

- 修复虚拟 IP「文生图」表单错误拉取 `image_to_image` 模型的问题
- 让前端模型能力/元数据与后端 `text_to_image` 的能力矩阵一致

## Changes

- 虚拟 IP 文生图：模型列表请求从 `AIModelType.ImageToImage` 改为 `AIModelType.Image`
  - 覆盖 `useVirtualIPImageGeneration()` 的推荐模型加载
  - 覆盖 `ImageGenerationForm` 的下拉模型加载

## Validation

- `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 登录 `http://localhost:8089/login` → 打开 `http://localhost:8089/virtual-ip/233525e9045146d580a1d18ef4a28161#ip-images` → 点击「AI 生成图片」→ 网络请求为 `model_type=text_to_image`

## Next Steps

- 全局梳理 text_to_image / image_to_image 的 prompt 模板语义（虚拟 IP / 环境 / 分镜）
- 针对 Google/Gemini 参考图 413 风险增加前后端提示与限制

## Linked Commits

- (pending)
