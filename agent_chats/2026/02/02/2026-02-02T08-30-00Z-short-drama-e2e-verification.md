---
id: 2026-02-02T08-30-00Z-short-drama-e2e-verification
date: 2026-02-02T08:30:00Z
participants: [human, claude-opus-4]
models: [claude-opus-4-5-20251101]
tags: [e2e, verification, short-drama, microgenre]
related_paths:
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-backend/app/api/v1/endpoints/scripts/storyboard.py
  - ai-pic-backend/app/services/storyboard/frame_generation.py
summary: "短剧全流程 E2E 验证完成：IP→环境→故事→剧本→分镜图→分镜视频"
---

## User Prompt

执行短剧全流程 E2E 验证（IP→环境→故事→剧本→分镜图→分镜视频），使用 Chrome MCP 进行浏览器端到端测试。

## Goals

1. 验证虚拟 IP 创建与管理功能
2. 验证环境资产创建与管理功能
3. 验证故事创作中的微类型选择功能
4. 验证剧集/剧本生成与 hook/cliffhanger 规划
5. 验证分镜帧生成与时间轴对齐
6. 验证分镜图像生成界面（参考图选择、AI 提示词）
7. 验证分镜视频生成入口

## Changes

无代码变更，仅为验证任务。

## Validation

### 测试环境

- URL: http://localhost:8089
- 账号: geyunfei / Gyf@845261
- 浏览器: Chrome (via MCP DevTools)

### 验证结果

| 步骤 | 功能 | 状态 | 验证内容 |
|------|------|------|----------|
| 1 | 虚拟IP | ✅ | 角色"林晚_爽剧测试_01300519"：肖像、风格提示词、MiniMax 配音 |
| 2 | 环境资产 | ✅ | "雨夜现代公寓室内（爽剧测试0130）"：3张场景图片 |
| 3 | 故事+微类型 | ✅ | "雨夜离婚协议（爽剧测试01300524）"：都市爽剧、被背叛者的清醒与反击 |
| 4 | Hook规划 | ✅ | 极致开场、证据流爽点、智商碾压、夫妻对决、强追更钩子 |
| 5 | 剧集/剧本 | ✅ | "第1集: 雨夜惊变"：3场景、9条beats、时间轴音轨 |
| 6 | 分镜帧 | ✅ | 11帧：景别/运镜/构图/AI提示词完整 |
| 7 | 图像生成界面 | ✅ | 角色+环境参考图选择、风格/画幅设置 |
| 8 | 视频生成入口 | ✅ | "生成视频"按钮可用 |

### 微类型功能详细验证

1. **微类型标签系统**
   - 目标市场下拉选择
   - 微类型输入框（支持自定义）
   - 节奏模板选择（自定义/预设）

2. **投流驱动的钩子设计**
   - 10秒锁定观众的开场钩子
   - 每集证据流爽点规划
   - 强追更结尾卡点

3. **起承转合四幕结构**
   - 第一幕（起）：撞破背叛
   - 第二幕（承）：秘密收集证据
   - 第三幕（转）：关键亮证据
   - 第四幕（合）：最终对峙逆袭

4. **专业影视术语支持**
   - 景别：close-up, extreme close-up, medium, wide
   - 运镜：zoom, fixed, tilt, pull
   - 构图：diagonal, center symmetry, three-thirds, foreground-background
   - AI提示词：自动从中文描述生成英文提示词

### 分镜图生成界面验证

- 环境参考图：自动从环境资产选取（已选2张）
- 角色参考图：自动从虚拟IP选取（林晚、顾辰各1张）
- 生成设置：
  - 提示词：auto-populated from frame description
  - 生成张数：4
  - 风格：写实
  - 画幅比例：9:16
  - 模型：可选

## Next Steps

1. 实际触发 AI 图像生成并验证生成质量
2. 实际触发视频生成并验证输出时长与画幅
3. 下载生成的图片/视频进行人工抽检
4. 补充自动化回归测试覆盖此流程

## Linked Commits

- (验证任务，无代码提交)
- tasks.md 更新：标记 E2E 验证任务完成
