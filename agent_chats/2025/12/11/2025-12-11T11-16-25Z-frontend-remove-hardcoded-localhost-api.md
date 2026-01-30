---
id: 2025-12-11T11-16-25Z-frontend-remove-hardcoded-localhost-api
date: 2025-12-11T11:16:25Z
participants: [human, codex]
models: [gpt-5.1]
tags: [frontend, api, cleanup]
related_paths:
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/test-auth/page.tsx
summary: "Removed remaining hardcoded http://localhost:8000 API bases in client pages so production uses same-origin /api paths everywhere."
---

## User Prompt

部署后前端部分功能（如注册、环境页、分镜等）仍然尝试请求 `http://localhost:8000/...`，怀疑是 Docker 构建没生效，要求把这些地方也改成和主 API 客户端一样的相对路径方案。

## Goals

- 清理前端中残留的 `http://localhost:8000` 硬编码，统一用相对 `/api/...` 或基于 `NEXT_PUBLIC_API_URL` 的前缀。
- 确保在生产域名（例如 `https://video.lets-gpt.com`）下，所有页面都通过同域 `/api` 访问后端。
- 保持 Next.js 15 构建和类型检查通过。

## Changes

- `src/app/environments/page.tsx`：
  - 将 `apiBase` 从 `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'` 改为 `(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')`。
  - 图片 URL 拼接继续复用 `apiBase`，默认走当前域名的 `/uploads/...`。
- `src/app/virtual-ip/[id]/images/page.tsx`：
  - 将 `API_BASE` 从 `(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '')` 改为 `(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')`。
  - `resolveImageUrl` 仍优先使用 `oss_url`，无 OSS 时再用 `API_BASE + file_path`。
- `src/app/episodes/[id]/storyboard/page.tsx`：
  - 将 `apiBase` 从 `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"` 改为 `(process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "")`。
  - `imageSrc` 使用该前缀拼接后端静态图片路径，默认同域 `/uploads/...`。
- `src/app/test-auth/page.tsx`（调试页面）：
  - 把两处直接 `fetch('http://localhost:8000/...')` 改为 `fetch('/api/v1/auth/login')` 和 `fetch('/api/v1/virtual-ips/')`，方便在生产域名下直接用来排查认证链路。

## Validation

- 在 `ai-pic-frontend` 中执行 `npm run build`：
  - Next.js 15 构建通过，所有页面（包括 `/environments`、`/episodes/[id]/storyboard`、`/virtual-ip/[id]/images` 和 `/test-auth`）都能顺利生成。
- 搜索确认：
  - `rg "http://localhost:8000"` 只剩测试 HTML 和 README 示例，不再出现在实际运行的 React 页面代码中。

## Next Steps

- 重新执行 `./docker/build_prod_images.sh` 并用最新 `IMAGE_TAG` 更新生产栈，前端所有 API 调用将统一走 `https://video.lets-gpt.com/api/...`。
- 如果需要在本地开发时继续直连后端，可在 `.env.local` 设置 `NEXT_PUBLIC_API_URL=http://localhost:8000`，不会影响生产镜像。

## Linked Commits

- （待补充）`fix(frontend): remove localhost api bases` 提交包含这次清理。
