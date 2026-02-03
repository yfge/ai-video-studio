---
id: 2026-02-03T22-00-00Z-dialogue-audio-agent
date: 2026-02-03T22:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, agent, audio, tts, emotion]
related_paths:
  - ai-pic-backend/app/services/agents/__init__.py
  - ai-pic-backend/app/services/agents/dialogue_audio_agent.py
  - ai-pic-backend/tests/unit/services/agents/__init__.py
  - ai-pic-backend/tests/unit/services/agents/test_dialogue_audio_agent.py
  - tasks-agent-fix.md
summary: "创建Dialogue Audio Agent，实现角色音色注册表/情绪对白对齐/语速韵律检测/多角色对话协调"
---

## User Prompt

继续 P1.11 Dialogue Audio Agent 重构

## Goals

1. 创建 `DialogueAudioAgent` 核心类
2. 实现角色音色注册表（voice_id + 特征 per character）
3. 实现情绪-对白对齐校验（开心台词配开心语气）
4. 实现语速/韵律自然度检测
5. 实现多角色对话渲染协调（自然交替/重叠检测）
6. 补充单元测试

## Changes

### 新增文件

1. **`app/services/agents/__init__.py`**
   - 模块初始化，导出 Agent 相关类

2. **`app/services/agents/dialogue_audio_agent.py`** (~550 行)
   - `DialogueAudioAgent`: 核心 Agent 类
     - `register_voice()`: 注册角色音色配置
     - `register_voices_from_config()`: 批量注册音色
     - `get_voice_profile()`: 获取角色音色配置
     - `detect_dialogue_emotion()`: 从对白内容检测情绪
     - `validate_emotion_alignment()`: 验证情绪-对白对齐
     - `_check_emotion_transitions()`: 检测突变情绪转换
     - `validate_speech_rhythm()`: 验证语速/韵律自然度
     - `validate_turn_taking()`: 验证多角色对话协调
     - `create_render_plan()`: 创建完整渲染计划
   - 辅助类:
     - `EmotionCategory`: 情绪类别枚举
     - `DialogueQualityIssueType`: 问题类型枚举
     - `DialogueQualitySeverity`: 严重程度枚举
     - `DialogueQualityIssue`: 问题描述
     - `CharacterVoiceProfile`: 角色音色配置
     - `DialogueRenderPlan`: 对白渲染计划
     - `DialogueAudioResult`: 处理结果

3. **`tests/unit/services/agents/__init__.py`**
   - 测试模块初始化

4. **`tests/unit/services/agents/test_dialogue_audio_agent.py`** (~380 行)
   - 30 个单元测试用例
   - 覆盖: 音色注册、情绪检测、对齐验证、语速检测、轮流协调、渲染计划

### 关键实现细节

- **情绪关键词映射**:
  ```python
  EMOTION_KEYWORDS = {
      HAPPY: ["开心", "高兴", "兴奋", "喜悦", ...],
      SAD: ["悲伤", "难过", "伤心", "沮丧", ...],
      ANGRY: ["愤怒", "生气", "恼怒", "暴怒", ...],
      ...
  }
  ```

- **情绪兼容性映射**:
  - happy → {HAPPY, SURPRISED, FLUENT}
  - sad → {SAD, CALM, WHISPER}
  - angry → {ANGRY, DISGUSTED}

- **语速阈值** (字符/秒):
  - 中文: slow=2.5, normal=3.5-5.5, fast=7.0
  - 英文: slow=2.0, normal=2.8-4.0, fast=5.0

- **轮流对话阈值**:
  - 最小换人间隔: 200ms
  - 最大重叠: 50ms

- **突变情绪检测**:
  - happy → angry (突变)
  - angry → happy (突变)
  - happy → sad (突变)
  - fearful → angry (突变)

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/agents/test_dialogue_audio_agent.py -v
# 30 passed in 0.09s
```

## Next Steps

1. P1.6.5: 连续性账本压缩优化（优先级排序替代 FIFO 截断）
2. 完成 P0 剩余验证任务 (1.7-1.8, 2.7, 3.7, 4.7)
3. 集成 DialogueAudioAgent 到现有 dialogue_audio_service.py
4. 开始 P2 任务（提示词模板重构、通用 Agent 框架等）

## Linked Commits

- feat(backend): add dialogue audio agent with voice registry and emotion validation
