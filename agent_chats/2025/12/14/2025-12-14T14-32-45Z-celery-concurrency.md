---
id: 2025-12-14T14-32-45Z-celery-concurrency
date: 2025-12-14T14:32:45Z
participants: [human, codex]
models: [gpt-5.2]
tags: [devops, backend, celery]
related_paths:
  - docker/docker-compose.prod.yml
summary: "Set prod Celery worker concurrency to 8 for better IO-bound throughput"
---

## User Prompt

prod 的  ai-video-celery-worker 设置为 8 个线程吧

## Goals

- 提高生产环境 Celery worker 并发到 8，适配以 IO 为主的任务。

## Changes

- 在 `docker-compose.prod.yml` 的 `ai-video-celery-worker` 启动命令中增加 `-c 8` 并发参数。

## Validation

- 配置改动，无需代码测试；部署后 worker 将以 8 并发启动。

## Next Steps

- 若后续需要按 CPU/限流再调优，可改为环境变量或自动根据资源配置。

## Linked Commits

- chore(devops): set prod celery concurrency to 8
