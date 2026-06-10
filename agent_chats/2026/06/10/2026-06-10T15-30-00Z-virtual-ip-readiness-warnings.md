---
id: 2026-06-10T15-30-00Z-virtual-ip-readiness-warnings
date: "2026-06-10T15:30:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - backend
  - frontend
  - virtual-ip
related_paths:
  - ai-pic-backend/app/services/virtual_ip_readiness.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip/crud.py
  - ai-pic-backend/app/schemas/virtual_ip.py
  - ai-pic-backend/tests/test_virtual_ip_readiness.py
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VirtualIPReadinessWarnings.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
summary: IP 详情响应新增非阻塞 readiness 块（默认头像/voice 静态校验+中文告警），前端详情页顶部琥珀告警清单——把"渲染期才爆"的缺头像/坏 voice 绑定提前到 IP 配置阶段可见。
---

# Virtual IP Readiness Warnings

## User Prompt

生产链路优化 Phase B5：IP 默认头像和 voice_config 无任何校验，缺失时到角色匹配/配音生成才失败，操作者难定位根因。

## Goals

- 后端 IP 详情响应加 `readiness: {has_default_avatar, voice_config_valid, warnings[]}`；仅静态校验（provider/voice_id 非空字符串、default_avatar_url 或 is_default 图片存在），不打 provider API、不硬阻断。
- 前端 IP 详情页顶部琥珀告警清单（role=alert），就绪时不渲染。

## Changes

- 新增 `app/services/virtual_ip_readiness.py`（compute_virtual_ip_readiness，中文修复指引文案）。
- `app/schemas/virtual_ip.py`：`VirtualIPReadiness` + `VirtualIPResponse.readiness`。
- `crud.py`：两个详情端点（id/business_id）经 `_detail_response` 附加 readiness；列表端点不变（避免 N 次 images 加载）。
- 前端：`VirtualIPReadiness` 类型、`VirtualIPReadinessWarnings` 组件、详情页接入。
- 新测试 `tests/test_virtual_ip_readiness.py`：4 个用例（双缺告警、URL/默认图两种头像来源、partial voice config 拒绝）。

## Validation

- 后端：`pytest tests/test_virtual_ip_readiness.py`（4 passed）+ `pytest -k virtual_ip`（58 passed，排除预存坏模块）。
- 前端：`npm run test` 71 passed；lint 0 errors；build 通过。

## Next Steps

- B6：任务取消（前后端）。

## Linked Commits

- This commit.
