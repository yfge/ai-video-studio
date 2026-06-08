# 图像生成统一化设计（Virtual IP / Environment / Storyboard）

## TL;DR

当前后端存在多条图像生成链路（虚拟 IP 文生图/图生图、环境文生图/图生图、分镜图像生成），它们在 **model/provider 解析、参数校验与透传、参考图归一化、持久化与元数据记录** 等方面存在明显不一致，导致质量与行为难以稳定复现、难以做统一优化。

本设计提出引入一个“**统一归一化层**”（Normalizer + Domain Policy + Provider Param Mapping），将各入口/worker 的分散逻辑收敛为一致的请求规范与可追溯元数据，再由各域适配器完成各自落库（VirtualIPImage / Environment.reference_images / Storyboard JSON）与 UI 兼容。

当前落地进度（截至 2026-01-10）：

- ✅ Phase 1：归一化层（`app/services/image_gen/`）
- ✅ Phase 2：虚拟 IP 文生图/图生图（variants）接入归一化层，并统一 Runtime Prompt（`virtual_ip_image` / `virtual_ip_image_variant`）
- ✅ Phase 3：环境文生图/图生图（sync+async+worker）接入归一化层，并接入 PromptManager（`environment_image`）
- ✅ Phase 4：分镜图生图接入归一化层（保留现有锚点合并策略，抽出参数构建到 service）
- ✅ Phase 5：统一“质量一致性/可复现”参数（`seed/steps/cfg_scale/negative_prompt/strength`）贯通 VirtualIP / Environment / Storyboard（含 Task.parameters 记录）
- ✅ Phase 6：引入“生成参数 profile/preset”（按 `provider+model+mode` 提供默认 `steps/cfg_scale/negative_prompt`），并提供 profiles 查询 API（`GET /api/v1/image-gen/profiles`）

---

## 背景

平台目前至少包含以下图像生成场景：

- 虚拟 IP：文生图（生成角色头像/立绘等）
- 虚拟 IP：图生图（基于已有角色图生成变体：视角/姿态/服装等）
- 环境：文生图（生成场景环境参考图）
- 环境：图生图（基于环境参考图生成变体）
- 分镜：图像生成（按分镜帧生成；当存在参考图时倾向走图生图，包含角色锚点与环境锚点）

这些链路使用了统一的 `AIServiceManager`（`generate_image` / `image_to_image`），但入口与 worker 的“请求构建”和“落库/持久化/元数据记录”分散实现，导致统一优化困难。

---

## 目标 / 非目标

### 目标

1. **统一请求语义**：同一组输入参数在不同 domain（virtual_ip/environment/storyboard）下具有清晰、可预测的行为（尤其是 model/provider、size、aspect_ratio、style/style_spec、reference_images）。
2. **统一归一化与校验**：
   - 统一解析 `provider:model` / `model_id`
   - 统一 size/aspect_ratio 归一化（并按 provider 支持能力过滤）
   - 统一 reference_images 归一化（URL/相对路径/data URL）
   - 统一安全透传：按 provider 白名单过滤 kwargs，避免“未知字段进入请求体导致不确定行为”
3. **统一元数据记录**：可复现（replay）一次生成：输入、归一化结果、provider/model、参数、参考图计数/摘要。
4. **统一持久化策略**：对外部图像 URL 统一走下载/上传（OSS/CDN）流程，保证最终可用 URL 稳定，并为后续质量门禁留入口。
5. **渐进迁移**：保持现有 API/worker 基本不变，内部逐步接入统一层，避免一次性大改。

### 非目标（本阶段不做）

- 不重构现有 provider 实现细节（OpenAI/Keling/Volcengine/Jimeng/Google 等）
- 不重写现有分镜生成端到端链路；统一化先以“抽公共能力、减少重复”为主
- 不立即引入复杂的“自动质量评分/门禁/多轮重试”（可作为后续增强，设计中预留接口）

---

## 现状梳理（按 domain）

下面列出主要入口与 worker 位置，方便后续迁移对照。

### 虚拟 IP 文生图（text-to-image）

- API：`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation.py`
  - 同步：`POST /{virtual_ip_id}/images/generate`
  - 异步：`POST /{virtual_ip_id}/images/generate-async`（创建 Task 后 Celery）
- Worker：`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py::process_virtual_ip_image_task`
- 调用：`ai_service.generate_virtual_ip_image(...)`（当前实现位于 `ai-pic-backend/app/services/ai/images_generation.py`）
- 落库：写 `VirtualIPImage`（含 prompt、ai_model、generation_params、metadata 等）

### 虚拟 IP 图生图（image-to-image variants）

- API：`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py`
  - 同步：`POST /{virtual_ip_id}/images/{image_id}/variants`
  - 异步：`POST /{virtual_ip_id}/images/{image_id}/variants-async`
- Worker：`ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py::process_virtual_ip_image_variant_task`
- 调用：`ai_service.ai_manager.image_to_image(...)`
- 落库：对每张结果调用 `ai_service._persist_generated_image(...)`，然后写 `VirtualIPImage`（变体）

### 环境 文生图（text-to-image）

- API：`ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py`
  - 同步：`POST /environments/{env_id}/images/generate`
  - 异步：`POST /environments/{env_id}/images/generate-async`
- Worker：`ai-pic-backend/app/api/v1/endpoints/story_structure/async_tasks.py::process_environment_image_task`
- 调用：`ai_service.ai_manager.generate_image(...)`
- 落库：`download_and_attach(...)` 追加到 `Environment.reference_images`，并在 `env.extra_metadata` 记录最近一次生成信息
- 特殊策略：环境链路会强制禁用 `style_spec/style_preset`（避免角色/镜头风格干扰环境）

### 环境 图生图（image-to-image variants）

- API：`ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py`
  - 同步：`POST /environments/{env_id}/images/variants`
  - 异步：`POST /environments/{env_id}/images/variants-async`
- Worker：`ai-pic-backend/app/api/v1/endpoints/story_structure/async_tasks.py::process_environment_image_variant_task`
- 调用：`ai_service.ai_manager.image_to_image(...)`
- 落库：同样通过 `download_and_attach(...)` 追加到 `Environment.reference_images`

### 分镜 图像生成（按帧生成，可能走 img2img）

- API：`ai-pic-backend/app/api/v1/endpoints/storyboard/media.py::generate_storyboard_images`
- Worker：`ai-pic-backend/app/services/task_worker_storyboard_media.py::storyboard_image_generate_task`
- Processor：`ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py::_process_storyboard_image_task`
- 策略：
  - 合并参考图来源：帧已有 refs、用户传入 refs、角色锚点（VirtualIPImage）、环境锚点（Environment.reference_images）
  - 有参考图时走 `ai_manager.image_to_image`，否则走 `ai_manager.generate_image`
  - prompt 使用 `PromptTemplate.STORYBOARD_IMAGE_PROMPT`（`docs` 对应模板 `ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt`）
- 落库：持久化每张图片后写回 `script.extra_metadata.storyboard.frames[*]`

---

## 主要问题（统一化动机）

1. **model/provider 解析不一致**

   - 环境使用 `parse_model_and_provider`
   - 虚拟 IP 图生图使用 `infer_provider_from_model`
   - 分镜内部手动 `split(':', 1)`
     → 同样的 model 字符串在不同入口可能得到不同 provider 选择/不同 fallback 行为。

2. **size/aspect_ratio 行为不一致**

   - 环境入口会按 provider 能力过滤不支持的 aspect_ratio（避免无效字段）
   - 虚拟 IP / 分镜更多是透传到 provider
     → 可能导致某些 provider 因未知字段报错，或 silently ignore，质量/结果不可预测。

3. **reference_images 归一化重复实现**

   - 虚拟 IP 与环境各自实现 `normalize_reference_images`
   - 分镜又有独立实现与额外语义（labeled references）
     → 规则漂移导致“同样的 ref 输入”在不同链路表现不同。

4. **prompt 构造策略分裂**

   - 分镜有专用模板强约束（避免拼图、字幕、UI 等）
   - 环境使用结构化拼接
   - 虚拟 IP 文生图历史上存在“模板渲染/实际入参不一致”的问题（现已统一到 Runtime 模板，并避免 style_spec suffix 重复叠加）
   - 各模板内部仍有大量“通用约束/负面词/质量片段”重复，容易在迭代时产生漂移（现已引入 `app/prompts/templates/fragments/` 统一管理）
     → 质量不稳定且难以统一调参/迭代。

5. **可追溯性不足**
   - 有的链路记录 style_spec resolution，有的只记录 style hint
   - reference images 通常只在 metadata 中散落记录（甚至不记录）
   - Task.parameters 与域对象记录结构不统一
     → 很难回答“这张图是怎么生成的、用了哪些参数/参考图、为什么这次质量差”。

---

## 统一化设计

### 统一概念模型

引入三个核心结构（建议放在 `app/services/image_gen/`）：

1. `ImageGenRequest`（入口层结构）

   - `domain`: `virtual_ip` | `environment` | `storyboard`
   - `mode`: `text_to_image` | `image_to_image`
   - `prompt`: str（未归一化）
   - `model`: str | None（可含 `provider:` 前缀）
   - `prefer_provider`: str | None（可选）
   - `style`: str
   - `style_preset_id`: str | None
   - `style_spec`: dict | None
   - `size`: str | None
   - `aspect_ratio`: str | None
   - `width/height`: int | None（兼容旧字段）
   - `count`: int
   - `seed`: int | None（可选：固定随机种子）
   - `steps`: int | None（可选：采样步数）
   - `cfg_scale`: float | None（可选：CFG scale）
   - `negative_prompt`: str | None（可选：反向提示词，仅部分 provider 支持）
   - `strength`: float | None（可选：图生图强度，仅 img2img 场景）
   - `base_image`: str | None（img2img 基准）
   - `reference_images`: list[str]（额外参考图）
   - `labeled_references`: list[dict] | None（仅 storyboard）
   - 扩展字段（后续）：`quality/denoise/image_fidelity/...`（按 provider 逐步收敛）

2. `ImageGenNormalized`（归一化后的结构）

   - `provider`: str（最终使用/强制）
   - `model_id`: str（去掉 provider 前缀后的 model）
   - `normalized_size`: str | None
   - `normalized_aspect_ratio`: str | None（按能力过滤后的结果）
   - `prompt`: str（最终 prompt，模板化/追加 style prompt 等）
   - `seed/steps/cfg_scale/negative_prompt/strength`（完成类型转换与范围约束后的值）
   - `base_image_url`: str | None（已转为绝对可访问 URL）
   - `extra_images`: list[str]（已归一化）
   - provider-safe 调用参数：由 `build_ai_manager_call(normalized)` 生成（按 provider 白名单过滤 kwargs）
   - `audit`: dict（归一化过程信息：丢弃的字段、默认值来源、policy 选择等）

3. `ImagePersistResult`（持久化结果）
   - `final_url`（优先 OSS/CDN）
   - `oss_url/local_file_path/relative_path/file_size/filename`
   - `persist_meta`（下载/上传信息、错误等）

### Domain Policy（差异显式化）

用 policy 统一“域差异”，避免散落的 if/else：

- `VirtualIPPolicy`

  - 允许 `style_preset_id/style_spec`
  - 文生图 prompt：角色描述 + 风格/类别 +（可选）结构化模板
  - 图生图：基准图来自 VirtualIPImage；reference_images 作为 extra_images

- `EnvironmentPolicy`

  - 强制 `style_preset_id/style_spec=None`（保留现有设计意图）
  - prompt：`compose_environment_prompt(...)` 结构化拼接
  - base_image：参数或 `env.reference_images[0]`

- `StoryboardPolicy`
  - prompt：使用 storyboard 模板（避免拼图/字幕/UI），并支持 labeled reference context
  - reference_images 合并策略：用户 > 帧 refs > 角色锚点 > 环境锚点（保持现有逻辑）

### 统一提示词管理（PromptManager）

**现状**：仓库已有 PromptManager（`app/prompts/`），图像生成链路已逐步统一到“Runtime Prompt Templates”：

- 分镜已使用 `PromptTemplate.STORYBOARD_IMAGE_PROMPT` 进行 prompt 组装（并可注入 labeled reference context）
- 环境已使用 `PromptTemplate.ENVIRONMENT_IMAGE` 渲染最终给图像模型的 prompt
- 虚拟 IP 文生图/图生图已接入 `virtual_ip_image` / `virtual_ip_image_variant`（直接喂给图像模型）

**统一策略**：把图像相关模板分成两类，并明确每条链路的模板边界。

1. **Runtime Prompt Templates（直接喂给图像模型）**

   - 输出是单段 prompt 文本（必要时可附带 `negative_prompt` 字段供支持的 provider 使用）
   - 目标：可预测、可复现、可版本化地迭代“图像质量与一致性”
   - 典型模板：`environment_image`、`storyboard_image_prompt`、（建议新增）`virtual_ip_image` / `virtual_ip_image_variant`

2. **Prompt-Generator Templates（给 LLM 用来生成 prompt）**

   - 输出是结构化 JSON（`positive_prompt/negative_prompt/...`），用于“提示词改写/扩写”场景
   - 目标：在需要更强表达力时，用 LLM 生成更细的 prompt，但必须可控（temperature=0、严格 JSON、可回放）
   - 典型模板：现有 `image_generation` 更适合归到这一类（并应明确只在开启 prompt-rewrite pipeline 时使用）

**元数据记录（建议）**：所有 domain 在 Task.parameters 与域对象落库时统一记录：

- `prompt_template` / `prompt_template_version`
- `prompt_variables`（可选：只存 hash/摘要，避免泄露敏感文本）
- `final_prompt`（必要时可截断）
- （可选）`negative_prompt` / `seed` / `steps` / `cfg_scale` 等

### Provider Param Mapping（安全透传）

在统一层做 **provider 白名单**，将 domain 参数映射为 provider 接口可接受的字段：

- OpenAI（DALL·E）：`size/style` 等
- Volcengine Seedream：`size/n/watermark` + `reference_images`（若支持）等
- Keling：`resolution`（由 size 映射）、`aspect_ratio`、`image_reference`、`image_fidelity` 等
- Jimeng：`width/height/steps/cfg_scale/seed/negative_prompt`（拒绝未知字段直接进入 `**kwargs`）
- Google：`imageSize/aspectRatio` 等

该层负责：

- 丢弃不支持字段（记录在 `audit.dropped_fields`）
- 必要转换（`size -> resolution`、`size -> width/height`）
- 统一 `count` clamp（1..4）

### 生成参数 profile/preset（质量一致性）

**问题**：同一个 provider/model 在不同入口（VirtualIP/Environment/Storyboard）下，经常因为“默认 steps/cfg/negative_prompt 不一致或缺失”导致质量与风格难以稳定。

**策略**：后端引入 `generation_profile`（profile/preset），作为“按 `provider+model+mode` 的默认生成参数档位”。入口只需要传：

- `generation_profile`（如：`balanced` / `quality` / `fast`）
- 可选覆盖：`steps/cfg_scale/negative_prompt/strength`

后端在统一归一化层中按 profile **填充缺省值**（不覆盖显式传入的字段），并在元数据中记录最终使用的参数。

**后端真源**：

- Registry：`ai-pic-backend/app/services/image_gen/profiles.py`
- Profiles API：`GET /api/v1/image-gen/profiles?model=<provider:model_id>&mode=text_to_image|image_to_image`

> 注意：并非所有 provider 都支持 `steps/cfg_scale/negative_prompt`，profiles API 可能返回空列表；前端应按返回内容决定是否展示 profile 选择。

### reference_images 归一化（统一实现）

统一归一化规则（供所有 domain 使用）：

- 允许：`http(s)://`、`data:image/...`、相对路径（必须带图片扩展名）
- 相对路径转绝对：`{backend_base}/{path}`
- 过滤掉“描述性字符串”（避免当成路径导致 404）
- 日志与审计：只记录计数与 hash，不记录完整 URL（避免泄露与日志爆炸）

### 统一持久化（download/upload）

统一使用现有 `persist_generated_image` / `ai_service._persist_generated_image` 的能力：

- 下载远端 URL / 解码 data URL
- 写入本地 uploads
- OSS/CDN 上传（按 `require_upload=bool(oss_service)` ）
- 返回 `final_url = oss_url or relative_path`

同时统一写入元数据（见下节）。

---

## 元数据与可追溯性规范（建议）

建议所有链路在 Task.parameters 与域落库时遵循同一结构（示意）：

```json
{
  "domain": "virtual_ip",
  "mode": "image_to_image",
  "input": {
    "prompt": "...",
    "model": "keling:kling-image-v2",
    "style": "realistic",
    "size": "2k",
    "aspect_ratio": "1:1",
    "count": 2,
    "reference_images_count": 3
  },
  "normalized": {
    "provider": "keling",
    "model_id": "kling-image-v2",
    "size": "2k",
    "aspect_ratio": "1:1",
    "dropped_fields": ["aspect_ratio(not supported)"]
  },
  "result": {
    "provider": "keling",
    "model": "kling-image-v2",
    "images_count": 2
  }
}
```

域对象侧（VirtualIPImage/Environment/Storyboard frame）至少记录：

- `provider/model`
- `style/style_spec/style_spec_resolution`（若适用）
- `size/aspect_ratio/count`
- `prompt_template`（模板名/版本/源码哈希，用于审计与回放）
- `prompt_sha256`（实际入参 prompt 的哈希，用于去重/对比）
- `reference_images_count` + `reference_images_hash`（不存全量 URL 也可）

---

## 迁移计划（渐进）

1. Phase 1：引入统一结构与归一化函数（不接入业务）

   - 新增 `app/services/image_gen/`（types、normalize、providers_mapping、refs、audit）
   - 单测覆盖：model/provider、size/aspect_ratio、refs normalize、policy 行为

2. Phase 2：接入虚拟 IP 图生图（风险较小，结果落库清晰）

   - 将 `virtual_ip_images/variants.py` 与 `virtual_ip_images/async_tasks.py` 改为调用统一层构建请求与安全透传
   - 将 `ai_service.generate_virtual_ip_image(...)`（`app/services/ai/images_generation.py`）接入统一层，对 size/aspect_ratio 做统一归一化，并避免 style_spec prompt suffix 重复叠加

3. Phase 3：接入环境文生图/图生图（保持禁用 style_spec 的 policy）

   - 替换 `environment_generation.py` / `environment_variants.py` / `story_structure/async_tasks.py` 的重复逻辑

4. Phase 4：接入分镜（保持现有合并锚点逻辑，抽出 normalize 与 provider mapping）
   - 将 `_gen_images` 参数构建迁移到统一层（`app/services/storyboard/storyboard_image_generation.py`），减少脚手架代码重复

---

## 测试与验收（建议）

- 单元测试：归一化与 provider mapping（不需要真实调用外部 API）
- 集成测试：mock `AIServiceManager` 响应，验证各 domain 落库结构一致、Task.parameters 结构一致
- 手工验证（Chrome E2E）：同一组输入参数在 VirtualIP/Environment/Storyboard 走同样的 provider/model 选择与 size/aspect_ratio 行为（并在 UI 中可追溯）

---

## 后续增强（质量一致性）

统一化完成后，可在“持久化前后”插入可选的质量门禁：

- 基础门禁：图片可解码、分辨率符合预期、文件大小阈值
- 肖像门禁：人脸数量检测、清晰度检测
- 自动重试：换 seed / 调整负面词 / 限定构图（以 policy 控制）

这些增强应通过统一层的 hook/strategy 实现，避免再次在各 domain 分散实现。
