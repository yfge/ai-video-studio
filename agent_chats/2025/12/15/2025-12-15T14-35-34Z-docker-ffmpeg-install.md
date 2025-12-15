---
id: 2025-12-15T14-35-34Z-docker-ffmpeg-install
date: 2025-12-15T14:35:34Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docker, backend, audio]
related_paths:
  - docker/Dockerfile.backend.dev
  - docker/Dockerfile.backend.prod
  - tasks.md
summary: "Install ffmpeg in backend/celery images to unblock audio concat and beats timeline generation"
---

## User Prompt

整体完成“对白音轨与声音驱动时间轴”功能；每完成一个工作项更新 `tasks.md`、及时自测并原子提交；所有音频都要上传 OSS。

## Goals

- 修复 celery 任务在音频拼接阶段因缺少 `ffmpeg` 导致失败的问题
- 保证 dev/prod 后端镜像都具备音频拼接运行依赖，便于后续 E2E 验证与发布

## Changes

- `docker/Dockerfile.backend.dev` / `docker/Dockerfile.backend.prod`：
  - 安装 `ffmpeg`
  - 将 Debian 源从 `http://` 切换为 `https://`，避免拉包过程中出现 `unexpected EOF`
  - 增加安装重试（最多 5 次）以提升构建稳定性，并在构建期校验 `ffmpeg` 可用
- `tasks.md`：补记并勾选“镜像安装 ffmpeg”完成项

## Validation

- `docker compose -f docker/docker-compose.dev.yml build ai-video-backend ai-video-celery-worker`
- `docker compose -f docker/docker-compose.dev.yml up -d --no-deps --force-recreate ai-video-backend ai-video-celery-worker`
- `docker exec ai-video-celery-worker ffmpeg -version`
- `docker exec ai-video-celery-worker ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 ... /tmp/ffmpeg_silence.mp3`

## Next Steps

- 用 Chrome 跑通 Episode 内“生成对白音轨 → 生成时间轴 → 生成分镜帧”完整链路并记录到 `agent_chats`

## Linked Commits

- (pending)
