## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- 消除静态占位图与真实 Skill 节点并存造成的两条平行工作流。
- 让新建 Plan 的真实 Skill 节点拥有可持久化、可解析的类型化边。
- 选择现有 Script 时避免自动重复生成 Script 和 Timeline。

## Changes

- 完整 Plan 到达时移除七个初始占位节点，只保留一套真实 Skill 节点。
- 为真实 Skill 节点创建七条类型化边，包括 `script -> image.candidates` 和人工选用的 `approved_image -> video.candidates.start_frame`。
- 将图片候选输入契约改为 `script` entity reference，与真实执行器的 `script_id` 契约一致。
- 已有 Script 时把 Script、Timeline 和 Image Candidates 设为人工复用/执行检查点，把 Video Candidates 保持为人工选图后的 blocked 状态；Storyboard 仍可自动准备。
- 更新设计文档，明确唯一执行图和复用策略。

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/test_production_canvas_skill_plan.py -q` -> 5 passed。
- `cd ai-pic-frontend && npm run lint` -> 0 errors，3 个既有 warnings。
- `cd ai-pic-frontend && npm run test` -> 327 passed。
- `cd ai-pic-frontend && npm run build` -> 通过，`/canvas` route 成功生成。
- `python scripts/check_repo_contracts.py --mode diff ...` -> 通过。
- `cd ai-pic-backend && python run_tests.py quick` -> 未进入测试；本机 Python 3.13 无法解析仓库固定的 `pydantic==2.5.0` 与 `langchain-core==0.2.43` 依赖。定向 pytest 使用现有环境通过。

2. Browser/runtime validation:

- Entry URL: `http://localhost:8089/canvas`。
- Run ID: `9a4bbfdb95f846e4be216beb1b09ad88`。
- User path: 按名称选择 IP 84、环境 13、Episode 49、Script 30，点击整体创建并保存。
- Console: 内置浏览器 warning/error 为空。
- Network/runtime: 页面只出现一套 Skill 节点；任务仅派发 6317 Virtual IP Image、6318 Environment Image、6319 Storyboard，没有重复 Script/Timeline 任务。
- DB: saved state 为 `graph_version=2`、16 nodes、7 typed edges；`skill-script-generate -> skill-image-candidates` 和 `skill-image-candidates -> skill-video-candidates` 均持久化。
- Screenshot: `artifacts/runs/canvas-executable-graph-20260712T031900Z/single-skill-graph.png`。

3. Conflict signals and corrections:

- Initial assumption: 动态 Skill 节点会复用初始画布的类型化边。
- Contradicting evidence: Run `9dc28f2fc8ee4c508403de83aaf86bf8` 同时保留占位节点和 Skill 节点，DB 边只连接占位节点，真实 `image.candidates` 手动运行被判缺少类型化输入。
- Correction: Plan batch 替换占位图并为真实 Skill identities 生成边；第二个 Run 的 DB 与浏览器均确认唯一执行图。

## Next Steps

- 单独提交候选默认单帧、worker 取消检查和空成功失败门禁。
- 在 provider 恢复后继续同一 Run 的图片候选、视频候选与 Timeline 放置。

## Linked Commits

- Pending
