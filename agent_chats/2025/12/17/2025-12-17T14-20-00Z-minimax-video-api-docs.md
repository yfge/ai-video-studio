---
id: 2025-12-17T14-20-00Z-minimax-video-api-docs
date: 2025-12-17T14:20:00Z
participants: [human, claude]
models: [claude-sonnet-4-5]
tags: [documentation, api, minimax, video-generation]
related_paths:
  - docs/api/minimax/video-generation-fl2v.md
  - docs/api/minimax/video-generation-i2v.md
  - docs/api/minimax/video-generation-query.md
  - docs/api/minimax/video-generation-download.md
summary: "Added MiniMax video generation API documentation including first-last frame to video, image to video, query task status, and video download endpoints"
---

## User Prompt

用户更新了 MiniMax API 视频生成相关的文档，需要提交到 git 仓库。

## Goals

- 提交新增的 MiniMax 视频生成 API 文档
- 创建相应的 agent_chats 记录
- 遵循项目的提交规范（Conventional Commits）

## Changes

### 新增文件

1. **docs/api/minimax/video-generation-fl2v.md** (8.6K)
   - 首尾帧生成视频接口文档
   - 接口：`POST /v1/video_generation`
   - 使用首尾帧图片及文本内容创建视频生成任务
   - 包含完整的 OpenAPI 规范

2. **docs/api/minimax/video-generation-i2v.md** (8.9K)
   - 图生视频任务接口文档
   - 接口：`POST /v1/video_generation`
   - 输入图片及文本内容创建视频生成任务
   - 包含完整的 OpenAPI 规范

3. **docs/api/minimax/video-generation-query.md** (3.5K)
   - 查询视频生成任务状态接口文档
   - 接口：`GET /v1/query/video_generation`
   - 通过 task_id 查询视频生成任务的状态
   - 包含完整的 OpenAPI 规范

4. **docs/api/minimax/video-generation-download.md** (3.4K)
   - 视频文件下载接口文档
   - 接口：`GET /v1/files/retrieve`
   - 通过 file_id 下载生成的视频文件
   - 包含完整的 OpenAPI 规范

### 文档特点

- 所有文档使用统一的 OpenAPI 3.1.0 规范格式
- API 域名：`https://api.minimaxi.com`
- 所有接口需要 Bearer Token 认证
- 文档包含详细的参数说明和响应示例

## Validation

### 文件列表检查

```bash
ls -lh docs/api/minimax/
```

确认新增了4个视频生成相关的文档文件。

### Git 状态

```bash
git status
```

确认4个文件为新增的未跟踪文件：
- video-generation-fl2v.md
- video-generation-i2v.md
- video-generation-query.md
- video-generation-download.md

## Next Steps

- 提交这些文档到 git 仓库
- 如需要，可以考虑创建一个 README.md 索引文档整合所有 MiniMax API 文档
- 可以添加更多示例代码和使用指南

## Linked Commits

将在当前 commit 中提交。
