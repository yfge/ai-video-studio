## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 支持按场景和剧集组织大型生产画布。
- 将分区作为经过后端校验的持久化图定义。

## Changes

- 新增 episode/scene 分区 schema、成员、边界和折叠状态。
- 多选节点可创建场景或剧集分区，折叠隐藏成员节点和关联边，展开恢复。
- 本地与服务器 Run 保存/恢复分区定义。
- 后端拒绝重复分区 ID、重复成员和未知节点引用。

## Validation

- 后端 production canvas graph 单元与集成测试：17 passed。
- 前端完整测试：308 passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run build`：Next.js production build 通过。
- 后端完整测试：2433 passed、88 skipped；4 failed、13 errors 均位于既有 episode outline、agent audit、model/character/task cancel/video rework 测试，主要错误为共享 SQLite 数据库只读/表约束问题，production canvas graph 测试全部通过。
- `python scripts/check_repo_docs.py` 与 diff contracts 检查通过。
- 内置浏览器临时无 Run 画布：场景分区折叠从 7 节点/7 边变为 5 节点/4 边，展开恢复；剧集分区可同时创建；重置后分区为 0，console error/warn 为 0。
- 浏览器证据：`artifacts/runs/canvas-sections-20260711T152500Z/`。

## Next Steps

- 实现撤销重做与剩余执行恢复操作。

## Linked Commits

- This commit
