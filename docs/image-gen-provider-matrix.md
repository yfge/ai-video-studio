# Image Gen Provider Matrix（provider-aware）

本文件用于说明当前“统一图像生成归一化层”（`ai-pic-backend/app/services/image_gen/`）的 **提示词语义** 与 **provider×mode 参数能力矩阵**，并给前端动态表单提供一份可核对的参考。

关联设计文档：`docs/design/image-generation-unification.md`

## 提示词语义（统一约定）

### `prompt`

- 正向描述：包含“画面内容 + 风格/镜头/材质/光照 + 约束（如无字无水印）”。
- Domain（Virtual IP / Environment / Storyboard）会在后端通过模板/策略注入上下文；最终下发到 provider 的为归一化后的 `prompt`。

### `negative_prompt`

- 语义：负向约束（Avoid/Constraints），用于抑制不希望出现的元素。
- 兼容策略：当 provider+mode 不支持 `negative_prompt` 时，后端会把其 **合并进 `prompt`**（以 `Avoid: ...` 形式追加），并记录：
  - `audit.dropped_fields += ["negative_prompt"]`
  - `audit.warnings += ["negative_prompt not supported ... merged into prompt"]`

### `reference_images` / `extra_images`

- API 层字段统一叫 `reference_images`（list）。
- 归一化后统一进入 `ImageGenNormalized.extra_images`，再按 provider+mode 映射到 AIServiceManager：
  - TEXT_TO_IMAGE：映射为 `reference_images`
  - IMAGE_TO_IMAGE：第 1 张作为 `image_url`（base），其余映射为 `extra_images`（仅当 provider 支持）
- 兼容策略：当 provider+mode 不支持多参考图时：
  - 前端应限制只选 1 张（避免“选了但被忽略”）
  - 后端会丢弃 `reference_images` 并记录 `audit.dropped_fields += ["reference_images"]`
- 已知约束：
  - Google/Gemini（text_to_image）：为降低 413 风险，后端会将 `reference_images` **截断为最多 4 张**（并在 provider 内联上传前自动压缩）。
  - 可灵（text_to_image）：仅使用第 1 张参考图（映射到 provider 的 `image` 字段）。

## provider×mode 参数能力矩阵

说明：

- “✅/❌”以当前 `supported_ai_manager_keys()` 白名单为准（`ai-pic-backend/app/services/image_gen/provider_params.py`）。
- `cfg_scale` 对火山引擎会映射为 `guidance_scale`，且仅部分模型支持（见 UI notes）。

| provider | mode | `reference_images`（list） | `extra_images`（img2img） | `negative_prompt` | `seed` | `steps` | `cfg_scale` | `strength` | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI | text_to_image | ❌ | n/a | ❌ | ❌ | ❌ | ❌ | n/a | DALL·E 2/3 主要用 `size`/`style` |
| OpenAI | image_to_image | n/a | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 仅支持单 base image（variations/inpainting） |
| Google | text_to_image | ✅ | n/a | ❌ | ❌ | ❌ | ❌ | n/a | 支持 `reference_images`（建议≤4张；过大将自动压缩）；`aspect_ratio` 可用 |
| Google | image_to_image | n/a | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | 支持多参考图（base + extra） |
| Volcengine | text_to_image | ✅ | n/a | ❌ | ❌ | ❌ | ⚠️ | n/a | `cfg_scale→guidance_scale`（部分模型） |
| Volcengine | image_to_image | n/a | ✅ | ❌ | ❌ | ❌ | ⚠️ | ❌ | 支持多参考图（base + extra） |
| 可灵（Keling） | text_to_image | ✅（仅 1 张） | n/a | ⚠️ | ❌ | ❌ | ❌ | n/a | `reference_images[0]→image`；有参考图时 `negative_prompt` 会合并进 prompt；支持 `image_reference/image_fidelity/human_fidelity` |
| 可灵（Keling） | image_to_image | n/a | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | img2img 不支持 `negative_prompt`（需写入 prompt） |
| 即梦（Jimeng） | text_to_image | ❌ | n/a | ✅ | ✅ | ✅ | ✅ | n/a | 支持 `width/height`（由 `size` 归一化） |
| 即梦（Jimeng） | image_to_image | n/a | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 支持 `strength`（显式走 img2img） |

## Domain 行为差异（与矩阵的关系）

### Virtual IP

- 目标：稳定生成“同一角色的不同变体”。
- `negative_prompt`：当使用 profile 默认 negative_prompt 且 domain=Virtual IP 时，会自动追加 `VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA`（保持角色一致性/避免劣化）。

### Environment

- 目标：环境资产，不被角色/镜头风格污染。
- policy 会禁用 `style_spec/style_preset`（只保留必要的 `style`）。

### Storyboard（分镜）

- 目标：利用参考图作为“锚点”，生成首尾关键帧。
- 当前策略：
  - refs 存在，且 provider 支持 txt2img `reference_images`，并且未显式设置 `strength`：优先 `TEXT_TO_IMAGE + reference_images`（把 refs 当 conditioning）
  - 否则：`IMAGE_TO_IMAGE`（base=第 1 张 ref，extra=其余 refs；若 provider 不支持 extra，前端应限制只选 1 张）

## E2E Quick Checks（Chrome）

- Environment：进入任一环境详情页，选择 Google/Gemini 模型，确认「模型提示」中出现“参考图内联上传/413 风险/建议≤4张”等提示。
- Storyboard：进入分镜页，打开「选择参考图生成关键帧」弹窗，确认可选择「火山引擎」等 txt2img 模型，且 helperText 为“仅展示支持参考图文生图的模型”。
