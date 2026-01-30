---
id: 2025-10-20T10-10-00Z-backend-bcrypt-pin-and-docs
date: 2025-10-20T10:10:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, deps, docs]
related_paths:
  - ai-pic-backend/requirements.txt
  - ai-pic-backend/DIAGNOSTIC_GUIDE.md
summary: "Pin bcrypt to 3.2.2 for passlib compatibility and add troubleshooting doc for login bcrypt error."
---

## User Prompt

处理登录报错 `(trapped) error reading bcrypt version`，并在文档中给出排障指引。

## Goals

- 修复 passlib 与 bcrypt 不兼容导致的登录失败；
- 在诊断指南中提供明确的解决步骤。

## Changes

- `requirements.txt` 新增 `bcrypt==3.2.2` 固定，避免安装到 4.x；
- `DIAGNOSTIC_GUIDE.md` 增补“登录时报错：AttributeError: module 'bcrypt' has no attribute '**about**'”章节及解决方案。

## Validation

- 重新安装依赖后，登录流程可正常进行（本机/虚拟环境验证）。

## Next Steps

- 将来可考虑升级 passlib 或兼容层以支持 bcrypt 4.x。

## Linked Commits

- pending（本地增量补丁将与此台账条目一并提交）
