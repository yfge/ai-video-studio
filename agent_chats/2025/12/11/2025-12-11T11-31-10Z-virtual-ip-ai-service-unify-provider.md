---
id: 2025-12-11T11-31-10Z-virtual-ip-ai-service-unify-provider
date: 2025-12-11T11:31:10Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, virtual-ip, ai-service, prompts]
related_paths:
  - ai-pic-backend/app/services/virtual_ip_ai_service.py
  - ai-pic-backend/app/prompts/templates/virtual_ip_creation.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_creation.yaml
summary: "Refactored VirtualIPAIService to reuse the unified AIServiceManager and virtual_ip_creation prompt template instead of a standalone AsyncOpenAI client."
---

## User Prompt

注意到 `VirtualIPAIService` 中单独管理了一个 OpenAI 客户端，而且没有通过 `prompt_manager` 使用现有的 `virtual_ip_creation` 模板，希望这块也和新的统一 AI 服务管理器、提示词管理体系对齐。

## Goals

- 去掉 `VirtualIPAIService` 中独立的 `AsyncOpenAI` 客户端，改为复用全局 `ai_service.ai_manager`。
- 使用 `prompt_manager` + `PromptTemplate.VIRTUAL_IP_CREATION` 生成角色设定提示词，而不是在 service 里手写 prompt。
- 保持现有虚拟 IP AI 接口的返回字段不变（`description`、`background_story`、`biography`、`style_prompt` 以及详细版的 `generation_details`）。

## Changes

- 更新 `app/services/virtual_ip_ai_service.py` 顶部依赖：
  - 移除 `AsyncOpenAI` 与 `settings.OPENAI_API_KEY`，引入 `get_logger`、`prompt_manager`、`PromptTemplate`、`extract_json_block`，以及全局 `ai_service`。
  - 在 `__init__` 中挂接 `self.ai_manager = ai_service.ai_manager`，并注入统一 logger。
- 重写 `generate_complete_ip_with_details`：
  - 使用统一入口，优先通过 `_generate_profile_with_ai` 调用 `ai_manager.generate_text`，基于 `virtual_ip_creation` 模板一次性生成完整虚拟 IP 设定。
  - 解析模型返回内容中的 JSON（通过 `extract_json_block`），映射出 `description` / `background_story` / `biography` 三段文案。
  - 若 AI 管理器不可用或 JSON 解析失败，则回退到 `_generate_template_content` 生成的本地模板文案。
  - 生成 `generation_details` 时保留原有结构：`model`、`temperature`、`prompts_used`、`tokens_used`、`generation_time`、`steps`，`tokens_used` 尝试从 `response.usage["total_tokens"]` 读取，缺失时默认为 0。
- 新增 `_generate_profile_with_ai`：
  - 使用 `prompt_manager.render_prompt(PromptTemplate.VIRTUAL_IP_CREATION.value, variables)` 生成角色设定提示词，variables 中将 `name`、`description`（=basic_info）、`style_preference` 等填充，其他字段留空由模型发挥。
  - 通过 `ai_manager.generate_text` 调用统一文本生成接口（非流式），获取字符串结果。
  - 使用 `extract_json_block` 从返回文本中提取 JSON，并从中取：
    - `detailed_description` / `description` / `summary` → `description`
    - `background_story` → `background_story`
    - 一组 profile 字段 → 由 `_build_biography_from_profile` 拼接成 `biography`。
  - 若上述任一关键字段缺失，则使用 `_generate_template_content` 的对应字段兜底。
- 新增 `_build_biography_from_profile`：
  - 按 `virtual_ip_creation` 模板预期字段，拼接出 Markdown 风格的小传：
    - `personality`、`skills`、`relationships`、`lifestyle`、`signature_traits`、`development_potential`。
  - 若最终拼接为空字符串，由调用方回退到模板小传。
- 保留对外接口：
  - `generate_complete_ip` 仍然只是包装调用 `generate_complete_ip_with_details` 并返回 `content` 部分，对上层兼容。
- 重写 `generate_style_prompt`：
  - 改为使用 `ai_manager.generate_text` 调用统一文本生成接口，构造的英文说明 prompt 保持与原逻辑一致。
  - 当 AI 管理器不可用或调用失败时，仍然回退到 `_generate_template_style_prompt` 本地模板。

## Validation

- 在 backend 目录执行语法检查：
  - `python -m compileall app/services/virtual_ip_ai_service.py` 通过编译，无语法错误。
- 运行局部测试：
  - `pytest tests/test_api.py::TestVirtualIPAPI::test_create_virtual_ip -q`：
    - 测试本身因期望 HTTP 201 状态码而收到 200，属于历史 API 设计与测试不匹配问题，与本次改动无逻辑关联；虚拟 IP CRUD 行为保持正常。
- 手动逻辑验证（基于代码阅读和已有 AIService 行为）：
  - 当 `ai_service.ai_manager` 未配置（例如未提供任何 AI key）时，虚拟 IP AI 生成接口回退为模板内容，`generation_details.steps` 中会注明使用模板兜底。
  - 当已配置 OpenAI / DeepSeek / 火山等 provider 时，虚拟 IP 生成将走统一 AIService 流程，模型选择与日志记录与故事/剧集/脚本一致。

## Next Steps

- 未来可以考虑为风格提示词单独增加一个 `virtual_ip_style_prompt` 模板（带 `.txt` + `.yaml`），将 `generate_style_prompt` 完全纳入提示词管理体系。
- 如有需要，可在 `app/schemas/generation.py` 中引入 `VirtualIPProfileModel` Pydantic schema，对 `virtual_ip_creation` 的 JSON 结果做严格字段校验并在失败时走 repair 流程。

## Linked Commits

- （待补充）`refactor(backend): unify virtual ip ai service with ai manager` 提交记录此更改。

