# 分镜管理任务拆解（/episodes/[id]/storyboard）

> 场景： http://localhost:8089/episodes/8/storyboard，目标是让分镜生成/编辑对齐规范化场景/镜头，并能携带角色与环境参考图完成闭环。

## 里程碑 0：现状梳理与阻断收集
- [ ] 功能/需求：梳理当前分镜生成入口、规范化场景/镜头数据与环境/角色资产的绑定现状，列出阻断清单。
- [ ] 后端：盘点 `/scripts/{id}/storyboard` / `generate_storyboard*` 返回体与 story_structure 模型的缺口（环境/角色/镜头 id），确认是否存在版本或 JSON 兼容分支。
- [ ] 前端：在 storyboard 页面确认哪些 UI 依赖未打通（镜头角色选择、环境选择、参考图载入、生成按钮状态），记录具体交互缺口。
- [ ] 验证：用 episode 8 复现“生成分镜→生成图像/视频→保存”路径，截图/日志记录当前失败点。

## 里程碑 1：数据与上下文对齐
- [ ] 功能/需求：确定生成/更新分镜的上下文字段清单（场景摘要、beat/shot 描述、角色、环境、提示词模板版本），并对外暴露；**剧本生成时即抽象出场景列表写入 `story_structure.scenes`，必要时生成 beats/shots 占位，保证新剧本可直接用于分镜。**
- [ ] 后端：`ai_service.generate_storyboard` / plan / update 路径统一携带 normalized scene/shot id、environment_id、character_ids，并将 `scene_scope`、`shot_scope`、context_text 反写 meta；剧本生成落地时同步 scenes→story_structure.scenes（含 beats/shots 占位）；确保 partial regenerate merge 策略。
- [ ] 前端：storyboard 页面请求参数与展示层对齐新字段（场景/镜头 id、上下文提示词预览、scope 提示），阻断未选择规范化场景/镜头的生成操作；确认加载的场景列表来自 story_structure 而非文本解析。
- [ ] 验证：补充/更新 storyboard prompt 单测覆盖上下文注入；本地调用 `/scripts/{id}/storyboard/preview` 确认字段生效；生成新剧本后直接打开分镜页，确认场景列表、beats/shots 占位已自动可用。

## 里程碑 2：参考图锚点与生成闭环
- [ ] 功能/需求：规定“角色图片 + 环境图片 + 分镜提示词”作为生成锚点，首尾帧/单帧/整场景皆可调用。
- [ ] 后端：`generate_storyboard_images` 支持 environment + character 参考图的自动聚合，写回帧级 metadata（reference_images、environment_id、character_ids、asset_id）；视频生成入口复用同一锚点。
- [ ] 前端：在分镜列表提供参考图选择/默认选中逻辑、首尾帧快速生成按钮，将选中的 env/role 透传给生成接口并在 UI 标记锚点；保存/刷新后保持选择状态。
- [ ] 验证：在 http://localhost:8089/episodes/8/storyboard 走一遍“选环境+镜头角色→生成首尾帧图像→查看回填 meta→触发视频生成”流程并记录结果。

## 里程碑 3：版本化与可见性
- [ ] 功能/需求：明确分镜版本号、来源（生成/手工）、模型/模板标签的展示与回滚需求。
- [ ] 后端：在 storyboard meta 中记录 version、updated_at、generation_method/source/model、scene_scope、template_version；提供回滚或只读快照接口（若可行）。
- [ ] 前端：在顶部信息区突出版本/来源/模板信息，支持选择特定版本查看，保存/生成后显示版本号递增。
- [ ] 验证：手工/自动生成后检查 meta 落盘与 UI 展示一致，补充 README/TESTING_GUIDE 对应字段说明。
