## User Prompt

继续完成 Canon 状态门禁与长篇小说质量闭环；同时由独立 thread 只读 review 整体小说生成代码，由主任务判断并采用必要意见。

## Goals

- 采纳 review 的两项 P1，防止真实 48 章运行接受 provider 截断输出。
- 普通 Resume 遇到已有正文且 ready plan 不可复用时 fail closed，禁止静默 replan 和重写。
- 保持无正文的旧计划迁移、失败规划恢复及显式章节重生成行为兼容。

## Changes

- 小说 AI wrapper 读取 provider `finish_reason`；`length`、token limit 和
  content filter 等截断结果返回 502，不写入 checkpoint。
- `ensure_generation_plan` 在 ready plan hash/门禁异常且修订版已有正文时
  返回 409，不进入 runtime/candidate stale 和 provider 调用。
- 更新旧的“自动重规划并失效正文”测试为 fail-closed 契约，并增加独立
  plan-integrity 与 finish-reason 回归。

## Validation

- focused collect：13 tests collected。
- focused pytest：13 passed。
- `pytest tests/unit/test_story_novel_*.py -q --no-cov`：
  401 passed, 1 skipped。
- 精确路径 isort/black：passed。
- `python scripts/check_repo_docs.py`：ok。
- `python scripts/check_repo_contracts.py --mode diff <changed files>`：ok。
- `git diff --check`：passed。
- `./docker/build_prod_images.sh`：passed；dirty-worktree build 使用 HEAD tag
  `74ac5967`，backend manifest
  `sha256:c2e834a81bc29b061ab099b197c5c1a9ef12086b9711de5e0f4bfac8b3fad46c`，
  frontend manifest
  `sha256:39bab84c5ea4c8bba04c56e41a18066abd3e035061dce4908c635879e5b275d9`。

## Next Steps

- 构建生产镜像、精确提交并重启 backend/worker。
- 仅 Resume 当前 0 章 Revision；已有正文后只允许 hash 完整的普通 Resume。
- 完成正式 cancel/snapshot/Resume、48/48、连续性与 GPT-5.6 验收。

## Linked Commits

- Pending
