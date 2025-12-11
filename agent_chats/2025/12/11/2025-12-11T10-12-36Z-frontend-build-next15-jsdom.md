---
id: 2025-12-11T10-12-36Z-frontend-build-next15-jsdom
date: 2025-12-11T10:12:36Z
participants: [human, codex]
models: [gpt-5.1]
tags: [frontend, build, docker]
related_paths:
  - ai-pic-frontend/package.json
  - ai-pic-frontend/package-lock.json
  - ai-pic-frontend/src/app/admin/users/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/components/RoleManagementModal.tsx
  - ai-pic-frontend/src/components/UserApprovalModal.tsx
  - ai-pic-frontend/src/components/UserDetailsModal.tsx
  - ai-pic-frontend/src/components/StoryboardFrameCard.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/tests/storyboardStructure.e2e.ts
  - ai-pic-frontend/tests/storyboardStructure.e2e.tsx
  - docker/docker-compose.prod.yml
summary: "Fixed Next.js build for prod images: jsdom typings, shared FrameCard component, Suspense wrapper for admin users, and aligned frontend types for production Docker builds."
---

## User Prompt

前端生产构建在 Docker 多架构镜像构建时失败：先是 jsdom 类型缺失和 FrameCard 页面导出问题，修完后 Next.js 15 又报 /admin/users 页面 useSearchParams 需要 Suspense 包裹，导致 `npm run build` 和 Dockerfile.frontend.prod 构建都卡在这里。

## Goals

- 让 `ai-pic-frontend` 在本地执行 `npm run build` 完全通过，支持生产 Docker 镜像构建。
- 消除 jsdom 相关类型错误，并保持现有基于 node:test 的前端测试正常编译。
- 解决 `/admin/users` 使用 `useSearchParams` 触发的 Next.js 15 Suspense 要求。
- 保持既有用户管理/脚本/虚拟 IP 页面类型安全，尽量不引入 `any`。

## Changes

- 安装 `@types/jsdom` 作为 devDependency，并更新 `package-lock.json`，修复 jsdom 的 TypeScript 类型缺失问题。
- 新增 `src/components/StoryboardFrameCard.tsx`，抽出分镜卡片 `FrameCard`、`SceneTag` 和 `formatText`：
  - 定义专用的 `StoryboardFrame` 类型用于分镜帧属性。
  - 导出 `FrameCard` 供脚本详情页和测试复用，避免在 page 组件里导出额外值导致 Next.js Page 类型错误。
- 更新 `src/app/scripts/[id]/page.tsx`：
  - 从新组件模块引入 `FrameCard`、`SceneTag` 和 `formatText`，删除本地重复定义。
  - 继续使用 `StoryboardFrame` 类型进行结构化分镜解析、分组和渲染，保持原有逻辑不变。
- 调整分镜 e2e 测试：
  - 将 `tests/storyboardStructure.e2e.ts` 重命名为 `.tsx`，显式导入 `afterEach`，并改为从 `src/components/StoryboardFrameCard` 导入 `FrameCard`，以匹配新的组件结构。
- 修正用户详情组件时间格式函数：
  - `src/components/UserDetailsModal.tsx` 中的 `formatDateTime` 改为接受可选字符串，避免 `updated_at` 为 `undefined` 时的类型错误。
- 修正认证 API 类型：
  - 在 `src/utils/api.ts` 中为 `login` 调用显式声明 `request<{ access_token: string; token_type: string }>`，消除 `response.data.access_token` 的类型报错。
- 解决 Next.js 15 对 `/admin/users` 的 Suspense 要求：
  - 在 `src/app/admin/users/page.tsx` 中引入 `Suspense`，将原来的 `AdminUsersPage` 重命名为 `AdminUsersPageContent`。
  - 新增默认导出组件 `AdminUsersPage`，在内部用 `<Suspense>` 包裹 `AdminUsersPageContent`，提供简洁的加载中骨架，从而满足 `useSearchParams` 必须在 Suspense 边界内的约束。
- 保持此前对 Episodes、Stories、Virtual IP Images 以及用户审批/角色管理 Modal 的类型调整（这些文件已在本次 diff 中，但变更核心仍围绕修复构建和类型）。
- 保留生产 Docker Compose 文件 `docker-compose.prod.yml` 中使用预构建镜像和统一 uploads 卷的配置（与此前 Docker 相关改动保持一致，仅随本次提交一起纳入）。

## Validation

- 在 `ai-pic-frontend` 目录执行：
  - `npm run build`：Next.js 15 构建通过，静态页面导出和类型检查全部完成。
  - `npm run lint`：无 ESLint 错误或警告。
- 手动检查：
  - `/src/app/scripts/[id]/page.tsx` 中不再有非法的 Page 命名导出，`FrameCard` 仅从 `src/components/StoryboardFrameCard.tsx` 引入。
  - `tests/sceneStructurePanel.test.tsx` 和 `tests/storyboardStructure.e2e.tsx` 均能通过 TypeScript 编译，使用 jsdom + node:test 的测试模式保持不变。
- 尚未在本地重新运行 Docker 多架构构建脚本，但该脚本依赖的 `npm run build` 已验证通过，预期可恢复生产镜像构建流程。

## Next Steps

- 在有 Docker 环境的机器上执行 `docker/build_prod_images.sh`，实际验证 linux/amd64 + linux/arm64 的生产镜像构建。
- 在本地或测试环境通过 `docker-compose.prod.yml` 启动完整栈，做一遍基于浏览器的回归（登录、用户管理、剧本分镜工作流）。
- 后续如有更多分镜 UI 组件复用需求，可考虑把相关类型和 UI 进一步集中到一个 `storyboard` 组件模块，减少散落定义。

## Linked Commits

- （待填写）在完成 `git commit` 后，将对应的提交哈希补充到这里，例如：`- feat(frontend): fix next build for prod images (abcd1234)`

