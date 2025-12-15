---
id: 2025-12-15T11-39-33Z-voice-binding-agent
date: 2025-12-15T11:39:33Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, audio, agent]
related_paths:
  - ai-pic-backend/app/services/voice_binding_service.py
  - ai-pic-backend/tests/unit/test_voice_binding_service.py
  - tasks.md
summary: "Implemented automatic voice binding for VirtualIP and derived script characters, including scope decisions and persistence in metadata."
---

## User Prompt

实现对白音轨 Feature 的前置能力：角色无音色绑定时用 agent 自动挑选并绑定；衍生角色（路人等）也自动处理，并由 agent 判断 scope（scene/episode/story）；无需人工确认。

## Goals

- 为 VirtualIP 提供缺省 voice_config 自动绑定能力（含审计字段）。
- 为衍生角色提供 voice binding：复用已有绑定并在缺失时通过 agent 判定 scope 后落库（scene/episode/story）。

## Changes

- 新增 `ai-pic-backend/app/services/voice_binding_service.py`：
  - `ensure_virtual_ip_voice_config()`：缺省时通过 agent 从系统音色候选中选 voice_id 并写回 `virtual_ips.voice_config`。
  - `ensure_derived_character_voice_binding()`：衍生角色 scope 判定（agent + fallback）并写入 `derived_character_voice_bindings`（scene/episode/story metadata）。
- 新增单测 `ai-pic-backend/tests/unit/test_voice_binding_service.py`：覆盖无 AI 环境下的 fallback 行为与 scope 落库位置。
- 更新 `tasks.md`：标记“音色绑定/衍生角色音色策略”两项为完成。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `pre-commit run --files ai-pic-backend/app/services/voice_binding_service.py ai-pic-backend/tests/unit/test_voice_binding_service.py tasks.md agent_chats/2025/12/15/2025-12-15T11-39-33Z-voice-binding-agent.md`

## Next Steps

- 实现“按场景生成对白混音音轨”并将 segment beats 写入 `scene_beats`（含留白补足）。

## Linked Commits

- (pending)
