---
id: 2026-06-10T21-50-00Z-list-newest-first-and-null-tags-crash
date: "2026-06-10T21:50:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - backend
  - frontend
  - bugfix
  - stories
  - virtual-ip
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories/crud.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip/crud.py
  - ai-pic-backend/app/schemas/virtual_ip.py
  - ai-pic-backend/tests/test_list_ordering_newest_first.py
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPListSection.tsx
  - ai-pic-frontend/src/hooks/useVirtualIPList.ts
summary: 修复"最近生成的故事和 IP 看不到"：故事/IP 列表无排序导致最新记录被 limit 截掉；IP 列表中 tags 为 NULL 的自动创建 IP 触发前端 .length 崩溃使整页空白。
---

# List Newest-First Ordering And Null-Tags Crash Fix

## User Prompt

用户报告：最近的生成故事和 IP 看不到。

## Goals

- 定位并修复故事/IP 列表不显示最新记录的问题。

## Changes

排查（数据均在 DB 且归属正确，接口 200）发现两个独立根因：

1. **列表无排序**：`GET /stories`（limit=50）和 `GET /virtual-ips/`（默认 limit=20）的查询没有 `order_by`，MySQL 按主键升序返回——用户有 60 个故事/80+ IP，最新记录（story 60「我的生活被狗血包围」、IP 83「斌哥」）被截掉。修复：两个列表 `order_by(id.desc())`。
2. **null tags 整页崩溃**：自动创建的 IP（「临时角色默认形象」「验证快递员-20260609」）DB 中 `tags=NULL`，前端 `TagList` 读 `tags.length` 抛 `Cannot read properties of null` 导致 /virtual-ip 整页白屏。修复：后端 `VirtualIPBase` 加 `field_validator` 把 None tags/style_reference_images 序列化为 `[]`（治本）；前端 `ip.tags ?? []` 双重防御（TagList 与 allTags flatMap）。

- 新测试 `tests/test_list_ordering_newest_first.py`（两个列表最新优先）。

## Validation

- 后端：排序+readiness+unique_name 相关 9 passed。
- 前端：lint 0 errors，71 测试全过。
- 真实浏览器（dev 栈 :8089）：/stories 显示「我的生活被狗血包围」；/virtual-ip 不再白屏，「斌哥」排首位，null-tags IP 正常渲染。证据：`artifacts/runs/list-ordering-fix-20260610T214500Z/virtual_ip_list_fixed.png`。

## Next Steps

- 继续 B6b：任务列表取消按钮。

## Linked Commits

- This commit.
