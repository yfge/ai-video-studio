---
id: 2026-01-23T05-15-00Z-short-drama-scoring-traffic-sheet
date: 2026-01-23T05:15:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, short_drama, scoring, traffic_sheet]
related_paths:
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/prompts/templates/script_score.txt
  - ai-pic-backend/app/prompts/templates/script_score.yaml
  - ai-pic-backend/app/prompts/templates/traffic_sheet_generation.txt
  - ai-pic-backend/app/prompts/templates/traffic_sheet_generation.yaml
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/services/scoring/__init__.py
  - ai-pic-backend/app/services/scoring/script_score_service.py
  - ai-pic-backend/app/services/scoring/traffic_sheet_service.py
  - ai-pic-backend/app/api/v1/endpoints/scoring.py
  - ai-pic-backend/app/api/v1/api.py
  - ai-pic-backend/app/prompts/templates/system_prompt_story_short_drama.txt
  - ai-pic-backend/app/prompts/templates/system_prompt_script_short_drama.txt
  - ai-pic-backend/tests/unit/services/scoring/__init__.py
  - ai-pic-backend/tests/unit/services/scoring/test_script_score_service.py
  - ai-pic-backend/tests/unit/services/scoring/test_traffic_sheet_service.py
summary: "实现 HookScore/ScriptScore 评分系统和投流表生成服务，优化 DeepSeek 短剧模板指令"
---

## User Prompt

检查 tasks.md 并推进「短剧微类型闭环」的剩余工作：

1. 短剧故事模板与剧本模板（每集强爽点/反转/收获点/结尾钩子）
2. 投流素材生成模板（15/30/60 秒素材、标题、字幕钩子）
3. HookScore/ScriptScore agent 与"投流表生成"service
4. 前端分镜/时间线 hook 节点标注 UI

## Goals

1. 实现 HookScore/ScriptScore agent 评分系统
2. 新增投流素材生成模板（Traffic Sheet）
3. 优化 DeepSeek 短剧模板指令
4. 创建 API 端点供前端调用

## Changes

### Schema 扩展 (generation.py)

- 新增 `ScriptScoreDimensions`: 评分维度（冲突强度、角色辨识度、文化适配、素材可剪性、逻辑一致性）
- 新增 `ScriptScoreResult`: 评分结果（overall_score, verdict, strengths, risks, rewrite_guidance, suggested_ad_hooks）
- 新增 `TrafficSheetAsset`: 投流表单条素材（asset_id, duration_seconds, hook_type, key_line, visual_hook, shot_list, cliff_or_cta）
- 新增 `TrafficSheet`: 投流表（assets 列表）

### Prompt 模板

- 新增 `script_score.txt/yaml`: 剧本评分模板，按 5 维度评分，输出 JSON
- 新增 `traffic_sheet_generation.txt/yaml`: 投流表生成模板，从剧本提炼 15/30/60 秒素材
- 注册到 `PromptTemplate` 枚举

### 服务层 (app/services/scoring/)

- 新增 `ScriptScoreService`: 评分服务，支持阈值判定（Pass >= 4.0 且无维度 < 3.5；Review 3.5-3.9；Rewrite < 3.5）
- 新增 `TrafficSheetService`: 投流表生成服务，从剧本提炼素材
- 新增 `score_script_from_db` / `generate_traffic_sheet_from_db` 便捷函数

### API 端点 (endpoints/scoring.py)

- `POST /scoring/score`: 评估剧本质量
- `POST /scoring/traffic-sheet`: 生成投流表
- `GET /scoring/score/{script_id}`: 根据 ID 获取评分
- `GET /scoring/traffic-sheet/{script_id}`: 根据 ID 生成投流表

### DeepSeek 优化

- 增强 `system_prompt_story_short_drama.txt`: 添加 JSON 输出规范（双引号、嵌套对象完整填充、ad_snippets 至少 3 条）
- 增强 `system_prompt_script_short_drama.txt`: 同上

### 单元测试

- `test_script_score_service.py`: 12 个测试（verdict 判定、响应解析、默认值）
- `test_traffic_sheet_service.py`: 9 个测试（响应解析、素材模型）

## Validation

```bash
# 评分服务测试 (21 tests passing)
cd ai-pic-backend
python -m pytest tests/unit/services/scoring/ -v --tb=short
# 结果：21 passed

# 模板解析测试 (12 tests passing)
python -m pytest tests/unit/test_prompt_template_resolver_story_format_variants.py tests/unit/test_story_format_prompt_templates.py -v --tb=short
# 结果：12 passed
```

## Next Steps

1. **前端分镜/时间线 hook 节点标注 UI** (Task #4)

   - 在 StoryboardPage 展示 hook_beat 标记
   - 关联 ad_snippets 到对应帧
   - 支持导出素材清单

2. **集成测试**

   - 端到端测试：从剧本生成到评分到投流表
   - Chrome E2E 验证 API 端点

3. **HookScore/ScriptScore 接入生成链路**
   - 在剧本生成后自动触发评分
   - 低分自动触发修订建议或重新生成

## Linked Commits

- 2012763 feat(backend): add script scoring and traffic sheet services
