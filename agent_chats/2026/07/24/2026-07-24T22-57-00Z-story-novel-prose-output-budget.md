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

## Validation

- Task 6645 / Invocation 1399：DeepSeek V4 Pro 在 9500 output tokens
  返回 `finish_reason=length`；截断门禁正确拒绝且 0 章写入。
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

## Next Steps

- 完成 focused、完整小说单测、格式、contracts 与生产镜像验证。
- 通过正式页面 Resume 当前 Revision，验证请求预算为 16000 且第 1 章
  不再因输出截断失败。

## Linked Commits

- Pending.
