---
id: 2026-01-29T22-42-49Z-story-character-registry-policy
date: 2026-01-29T22:42:49Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, generation, characters]
related_paths:
  - ai-pic-backend/app/core/validators/character_registry.py
  - ai-pic-backend/app/prompts/templates/episode_generation.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_film.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_generation_tv_series.txt
  - ai-pic-backend/app/prompts/templates/script_generation.txt
  - ai-pic-backend/app/prompts/templates/script_generation_short_drama.txt
  - ai-pic-backend/app/prompts/templates/story_outline.txt
  - ai-pic-backend/app/prompts/templates/story_outline_film.txt
  - ai-pic-backend/app/prompts/templates/story_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/story_outline_tv_series.txt
  - ai-pic-backend/app/services/episode/episode_generation_service.py
  - ai-pic-backend/app/services/script/script_character_policy.py
  - ai-pic-backend/app/services/script/script_generator.py
  - ai-pic-backend/app/services/script/script_utils.py
  - ai-pic-backend/app/services/storyboard/storyboard_character_anchors.py
  - ai-pic-backend/tests/unit/core/validators/test_character_registry.py
  - ai-pic-backend/tests/unit/services/script/test_script_character_policy.py
summary: "Enforced Story角色注册表为生成链路单一来源，允许泛化小角色并阻断未知角色。"
---

## User Prompt
只允许 Story 注册角色 + 少量“泛化小角色”(路人/店员/旁白)，允许自动归一；并要求在 docker 容器中验证。

## Goals
- 生成链路角色单一来源：StoryCharacter 注册表优先，避免 main_characters 漂移引入新角色。
- 允许有限泛化小角色：`路人/店员/旁白`（含后缀如 路人甲/店员A），其余“新命名角色”必须阻断。
- 提升 prompt 约束强度，降低 LLM 自行扩写新角色概率。
- 补齐单测，确保规则可回归。

## Changes
- 新增角色注册表工具：`ai-pic-backend/app/core/validators/character_registry.py`
  - 泛化小角色归一（路人/店员/旁白），别名提取与 display name 推断，昵称/别名到 canonical 的最小启发式归一。
- 剧本生成增加角色策略 enforcement：`ai-pic-backend/app/services/script/script_character_policy.py`
  - 将 scenes/dialogues 中的角色名归一到 Story 注册表；发现未知命名角色则返回 unknown 列表。
- 剧本生成阻断未知角色：`ai-pic-backend/app/services/script/script_generator.py`
  - enforcement 后若存在 unknown 角色，抛 `GenerationFailedError`，并给出可读错误信息。
- 角色资料构建以 StoryCharacter 为准：`ai-pic-backend/app/services/script/script_utils.py`
  - Story 存在注册表时忽略 `story.main_characters`（避免“主角/反派”被旧字段注入 prompt）。
- Episode prompt 统一注入 character_profiles：`ai-pic-backend/app/services/episode/episode_generation_service.py`
- Storyboard 名称别名提取复用核心逻辑：`ai-pic-backend/app/services/storyboard/storyboard_character_anchors.py`
- 强化模板角色约束（故事/剧集/剧本）：`ai-pic-backend/app/prompts/templates/*`
  - 明确“不得新增命名角色”，仅允许泛化小角色；同时修正 prompt 输出排版（避免 trim_blocks 导致的换行丢失）。
- 新增单测覆盖：`ai-pic-backend/tests/unit/core/validators/test_character_registry.py`、`ai-pic-backend/tests/unit/services/script/test_script_character_policy.py`

## Validation
- 单测：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（902 passed）
- 生产镜像构建：`./docker/build_prod_images.sh`（backend/frontend multi-arch build & push succeeded）
- Docker 环境实际 prompt 预览验证（绕过 MCP Chrome 失败）：
  - `POST /api/v1/episodes/prompt/preview`（story_id=3）确认出现“角色约束”段落，且主角列表来自 Story 注册表（老拐/文闻）
  - `POST /api/v1/scripts/prompt/preview`（episode_id=7）确认“角色约束”段落存在，角色设定排版正常
- Chrome MCP：调用 `chrome-devtools/new_page` 遇到 `Transport closed`，无法执行浏览器自动化；已用 API 预览作为替代验证路径。

## Next Steps
- 将“未知角色阻断/修复”扩展到 timeline/storyboard 生成链路（当前主要覆盖 episode/script）。
- 为生成失败提供 repair 策略（自动把昵称归一或提示用户先注册角色/补齐角色卡）。
- 按你定义的全流程（deepseek 文生文 + banana pro 生图 + geo veo3 生视频）跑 1 个 Story/1 个 Episode/时间轴+音轨+视频，并抽检逻辑一致性。

## Linked Commits
- (pending) feat(backend): enforce story character registry in generation

