---
id: 2026-06-10T09-40-00Z-dev-hmr-proxy-browser-validation
date: "2026-06-10T09:40:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - docker
  - dev-environment
  - browser-validation
related_paths:
  - docker/nginx.dev.conf
  - artifacts/runs/clip-storyboard-ui-20260610T051400Z/browser_validation.json
summary: 真实 Chrome 浏览器验证分镜生产链路（环境图默认绑定、故事板生成、资产 lineage、Panel 引用），并修复 dev nginx 缺 websocket 代理导致 Next HMR 失联整页重载、打断任务轮询的问题。
---

# Dev HMR Proxy Fix And Clip Storyboard Browser Validation

## User Prompt

完成整体分镜生成链路并优化 UI；用户指定使用 dev_in_docker 栈做真实浏览器验证。

## Goals

- 在 dev Docker 栈（nginx :8089）用真实 Chrome 验证本系列前端改动。
- 验证：环境图自动默认勾选、全选/清空、绑定上下文摘要、内联任务状态、故事板生成与回填、Panel 引用进入视频参考来源。
- 修复验证过程中发现的 dev 环境缺陷。

## Changes

- `docker/nginx.dev.conf`：`location /` 增加 `proxy_http_version 1.1`、`Upgrade`/`Connection "upgrade"` 头和 `proxy_read_timeout 600s`。原配置不支持 websocket，`/_next/webpack-hmr` 退化为 GET 404 循环，Next dev 客户端失联后强制整页重载，会卸载片段生产面板中的任务轮询。修复并重启 nginx 后 `webpack-hmr` 404 消失。

## Validation

- Chrome DevTools 真实浏览器（非 fallback），账号 geyunfei，剧集「第1集 末日安全屋」，clip `video_scene_577_beat_3888_003`：
  - 选环境「老拐工作室」→ 4 张环境图加载，第 1 张自动勾选，「已选 1/4」计数与全选/清空按钮渲染正确。
  - 视频绑定上下文摘要变为「已携带绑定 / 环境图：1 张 已绑定」。
  - 点「生成故事板参考图」→ 内联状态行「故事板参考图生成中（任务 #6035），完成后自动刷新…」。
  - 后端 `grid_storyboard_sheet_generate` 29.1s 成功，sheet 上传 `ai-generated/clip-storyboard/image/20260610/051423/4063b0cc.png`。
  - 重新选中 clip：资产审计出现「故事板参考图 #599」，预览图带「点击查看大图」，视频参考来源新增「故事板 Panel 1」。
- 证据：`artifacts/runs/clip-storyboard-ui-20260610T051400Z/`（browser_validation.json + 2 张截图）。
- `BUILD_PUSH=false ./docker/build_prod_images.sh` 本地构建成功（exit 0，未推送 registry）。

## Next Steps

- 角色 IP 图默认勾选路径需在绑定了 IP 的剧集上复验（本剧集无 episode characters）。
- 视频生成（rework）链路的真实 provider 验证依赖 Volcengine/Keling 账户余额（Keling 已报 balance not enough）。

## Linked Commits

- This commit.
