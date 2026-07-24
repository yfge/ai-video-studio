## User Prompt

去掉 8192 上限；章节正文使用可支持 3000–5000 字完整输出的预算。

## Goals

- 防止标准 5000 字章节在 9500 tokens 处被 provider 截断。
- 保留超长自定义章节的动态预算，不恢复应用级 16000 上限。
- 已知输出能力不足的模型在启动前继续返回 422。

## Changes

- 标准小说章节输出预算下限改为 16000 tokens。
- 超长自定义章节继续使用按最大字符数动态计算的更高预算。
- 模型能力预检使用与实际章节调用一致的预算。
- typed state 的 evidence-only 返修也使用 16000 tokens；返回结构仍只允许
  两个证据 map，不能借预算提升修改冻结状态。

## Validation

- Task 6645 / Invocation 1399：DeepSeek V4 Pro 在 9500 output tokens
  返回 `finish_reason=length`；截断门禁正确拒绝且 0 章写入。
- Task 6646 / Invocation 1403：evidence-only 返回仅 180 字符，但
  reasoning 消耗满固定 3000 completion tokens 后截断；门禁仍拒绝且 0 章写入。
- focused：19 passed。
- 完整 `tests/unit/test_story_novel_*.py -q --no-cov`：
  409 passed，1 skipped。
- 精确 `isort`、`black`、repo docs、repo contracts diff 与
  `git diff --check` 均通过；源码 118 行，测试 247 行。
- `./docker/build_prod_images.sh` 通过：
  - backend manifest
    `sha256:711f9f7a80c22883fa2919d05f466e8f1e1c5e07097e9b1832f92ecf4d32a043`
  - frontend manifest
    `sha256:97db13ec9009e28786da5ca6da19c08a245bb898cdd558bd94d6d27fb2c92a4f`
- evidence-only 预算回归：11 passed；完整小说单测仍为
  409 passed，1 skipped。
- evidence-only 变更的精确格式、docs、contracts、diff check 通过；
  源码 132 行，测试 207 行。
- evidence-only 生产镜像构建通过：
  - backend manifest
    `sha256:3232370e919ec866a7d1902e0e372c35610776a95b8a6f10ff63bae4b9e8e99a`
  - frontend manifest
    `sha256:dae5bb8316b55601500296363574dcfbb7ac80127e582f3bc9d9b2cc8e20e7df`

## Next Steps

- 完成 focused、完整小说单测、格式、contracts 与生产镜像验证。
- 通过正式页面 Resume 当前 Revision，验证请求预算为 16000 且第 1 章
  不再因输出截断失败。

## Linked Commits

- Pending.
