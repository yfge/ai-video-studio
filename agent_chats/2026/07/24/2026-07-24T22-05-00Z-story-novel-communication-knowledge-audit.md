## User Prompt

继续通过真实系统 API + MySQL 完成 48 章长篇；任何质量门禁失败时停止付费，
修复正确链路而不绕过 Canon、状态或 future gate。

## Goals

- 修复 Task 6641 把不包含具体事实的“联系并请求支持”误判为长期知识授予。
- 保持逐事件语义复审必须归零的 fail-closed 门禁。

## Changes

- 语义审计 prompt 明确：联系、请求、询问、呼叫或发送若未逐字写出具体新事实，
  不得推断任一方获得 knowledge grant。
- 增加 prompt 合同回归，避免重新引入通信动作即知识授予的错误推断。

## Validation

- Task 6641 fail closed，0 章。
- Invocation 1378 将 `ev-ch18-2` 猜为港务监理获知虚构 fact，
  Invocation 1379 又改猜为老拐获知同一 fact，证明事件本身没有稳定的知识命题。
- `pytest tests/unit/test_story_novel_plan_semantic_audit.py -q --no-cov`：
  10 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  406 passed，1 skipped。
- 精确 isort/black、repo docs/contracts diff、`git diff --check`：passed。
- `pre-commit run --all-files`：未通过既有全仓格式/ruff 基线，并自动改写
  233 个非本任务 tracked 文件；已按运行前 clean 基线全部精确恢复。未保留任何
  非本任务改动，精确文件 hooks 仍为 passed。
- `./docker/build_prod_images.sh`：passed（dirty build tag `d9457298`）；
  backend manifest `b61ccf5437eaf1f22c75ce85f4a4b26cae1153ae7dab003f43e2571b12242d5b`，
  frontend manifest `3b8f910bd5cddd441731e1b1b0caa5de1559e873cd9209e1cc86bf273812f406`。

## Next Steps

- 精确提交、重启后，只 Resume 当前 Revision 一次。

## Linked Commits

- Pending
