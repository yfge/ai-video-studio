## User Prompt

继续通过真实系统 API + MySQL 完成 48 章长篇；任何质量门禁失败时停止付费，
修复正确链路而不绕过 Canon、状态或 future gate。

## Goals

- 修复 Task 6639 逐事件语义复审忽略已有 typed effects、改绑 fact source
  并要求重复移动的非收敛问题。
- 保持复审必须归零的 fail-closed 门禁。

## Changes

- 复审 prompt 明示 verification mode，并逐事件提供已有 knowledge grants。
- 明确相同角色/事件知识、相同移动和已到达地点不得作为 missing effect 重报。
- 语义审计 parser 强制非 Canon fact ID 使用
  `fact-{source_event_id}-{正整数}`；Canon milestone fact 仍须逐字使用 outcome。
- 第二轮仍报告任何合法遗漏时继续失败，不放宽门禁。

## Validation

- Task 6639 fail closed，0 章。
- #1371 首审与 #1372 复审均完整覆盖第 17–24 章的 18 个 event ID。
- #1372 错把 `ev-ch19-3` 的 fact 写成 `fact-ev-ch19-1-1`，并重报现有/
  不连续移动；已确认无 active Task 或 invocation。
- focused：10 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  406 passed，1 skipped。
- 精确 isort/black、repo docs/contracts diff、`git diff --check`：passed。
- `./docker/build_prod_images.sh`：passed（dirty build tag `0cd03f76`）；
  backend manifest `df9c23cc8009321a25d24adfa053b895f0c2d45fb8ecfdd4e01236915324015f`，
  frontend manifest `c4406eae0d4d92e15870b73c6bbfea1b30fe678505843237eb7f8f34504e3fdb`。

## Next Steps

- 运行 focused/full Story Novel tests、格式、contracts 与生产镜像。
- 精确提交、重启后，只 Resume 当前 Revision 一次。

## Linked Commits

- Pending
