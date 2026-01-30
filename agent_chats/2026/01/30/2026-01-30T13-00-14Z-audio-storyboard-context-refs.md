---
id: 2026-01-30T13-00-14Z-audio-storyboard-context-refs
date: 2026-01-30T13:00:14Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, storyboard, prompts, video]
related_paths:
  - tasks.md
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_context.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_context.yaml
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/storyboard/storyboard_audio_context_enricher.py
  - ai-pic-backend/app/services/storyboard/storyboard_audio_character_visuals.py
  - ai-pic-backend/app/services/storyboard/storyboard_audio_context_utils.py
  - ai-pic-backend/app/services/storyboard/storyboard_audio_scene_env_hints.py
  - ai-pic-backend/tests/fixtures/markers.py
  - ai-pic-backend/tests/test_full_image_generation.py
  - ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py
summary: "Inject Story character visual card briefs + auto reference_images into audio_timeline->storyboard frames"
---

## User Prompt

在 audio_timeline→storyboard 阶段注入 Story 角色卡简述（外观/服饰锚点），并自动选取 reference_images（<=3：人物锚点+环境），做到“不依赖先跑分镜图”也能稳住身份。

## Goals

- 在从 episode audio timeline 生成 storyboard 占位时，把“角色是谁”明确写入视觉提示词上下文（但不泄露对白文本）。
- 自动从 Story 角色注册表与 Environment 资产中选取 reference_images（<=3），贯通后续 Veo 视频生成提交。
- 保持提示词模板统一管理，避免散落字符串拼接。

## Changes

- 新增模板 `storyboard_audio_visual_context`：把 base visual prompt + 角色卡简述 + 环境锚点组合成 `prompt_description`（用于后续生成 ai_prompt）。
  - `ai-pic-backend/app/prompts/templates/storyboard_audio_visual_context.txt`
  - `ai-pic-backend/app/prompts/templates/storyboard_audio_visual_context.yaml`
  - `ai-pic-backend/app/prompts/templates.py`
- 新增 audio_timeline→storyboard enrich 层：
  - `ai-pic-backend/app/services/storyboard/storyboard_audio_context_enricher.py`
  - `ai-pic-backend/app/services/storyboard/storyboard_audio_character_visuals.py`
  - `ai-pic-backend/app/services/storyboard/storyboard_audio_scene_env_hints.py`
  - `ai-pic-backend/app/services/storyboard/storyboard_audio_context_utils.py`
  - 行为：
    - 从 StoryCharacter registry 读取 VirtualIP.description/style_prompt，生成角色卡简述（外观/服饰锚点）。
    - 选择角色锚点图（优先 VirtualIPImage.oss_url 默认头像，其次 default_avatar_url/style_reference_images）。
    - 选择环境锚点图（Scene.environment.reference_images）。
    - 写入 `frame.reference_images`（<=3；有环境时为 “最多2角色 + 环境”）。
    - 把角色卡/环境锚点注入 `frame.prompt_description`，后续 `apply_storyboard_prompt_optimizations()` 生成的 `ai_prompt` 将包含这些上下文。
- audio_timeline→storyboard 帧结构补充 `scene_id`，便于环境资产关联：
  - `ai-pic-backend/app/services/dialogue_audio_service.py`
- 测试与模板覆盖：
  - `ai-pic-backend/tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py`
  - `ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py`
- 测试稳定性：默认跳过 external(OpenAI/OSS) 测试（需显式 `RUN_EXTERNAL_TESTS=1` 才执行），避免本地/CI 在“有 key 但无外网”时误跑：
  - `ai-pic-backend/tests/fixtures/markers.py`
  - `ai-pic-backend/tests/test_full_image_generation.py` 标记为 `openai/external`
- 更新任务看板：标记该项完成。
  - `tasks.md`

## Validation

- `cd ai-pic-backend && pytest`（1036 passed, 91 skipped）
- Chrome (MCP) E2E：
  - 登录 `http://localhost:8089`（geyunfei / Gyf@845261）
  - 打开 Story `雨夜离婚协议（爽剧测试01300524）` → Episode 工作台 → 分镜页
  - 点击“从时间轴同步分镜占位”（勾选“覆盖已有分镜”）
  - 抽检同步后的帧：
    - Dialogue 帧 `AI 提示词` 包含“开口说话/无字幕/无可读文字”，且包含 `角色卡:` 与 `环境锚点:`
    - “已绑定参考图”数量符合 <=3（示例帧显示 2 张：角色+环境）

## Next Steps

- 抽检至少 2 个 dialogue beat 生成的视频：嘴型/说话动作明显，且无字幕/无可读文字（延续 tasks.md P0 验证项）。
- 对“三人同框”帧进一步策略化 ref 选择（必要时按 importance/speaker 优先级动态替换/轮换锚点）。

## Linked Commits

- (pending)

