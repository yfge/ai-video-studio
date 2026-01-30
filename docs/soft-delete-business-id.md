# 全局软删除 + business_id 方案（设计稿）

## 1. 目标与约束

- 所有业务实体统一支持软删除，默认查询排除软删数据，删除后允许同 key 重建。
- 为所有实体引入稳定的 `business_id`（`replace(uuid(), '-', '')`，长度 32），作为业务级关联主键并建立唯一索引。
- 删除语义：写入 `is_deleted=true`、`deleted_at`、`deleted_by`（`users.id`）、`deleted_reason`，保留审计；支持按需恢复。
- 再生成逻辑（episode/script 等）：创建全新记录（新的 `id`/`business_id`），旧记录软删；前端接受新 ID/business_id。
- 关联逐步切换为按 `business_id` 关联，保持过渡期的 `id` 兼容能力。
- 默认行为不降低查询性能：为 `business_id`、`is_deleted`、复合唯一键加索引。

## 2. 范围（实体清单）

- 核心内容链路：`stories`、`episodes`、`scripts`、`story_characters`、`story_treatments`、`story_step_outlines`、`scenes`、`scene_beats`、`shots`、`script_templates`。
- 资产与环境：`images`、`virtual_ips`、`virtual_ip_images`、`environments`。
- 任务与用户：`tasks`、`users`、`user_audit_logs`。
- 其他/后续：后续新增表默认包含该 mixin；若存在未列出的表，按同样规则处理。

## 3. 模型设计

- 基础字段（写入 `BaseMixin`/`SoftDeleteBusinessMixin`）：
  - `business_id`: `String(32)`, not null, server_default `replace(uuid(), '-', '')`, 唯一索引。
  - `is_deleted`: `Boolean`, default `false`, 索引。
  - `deleted_at`: `DateTime(timezone=True)`, nullable。
  - `deleted_by`: `Integer`（FK `users.id`，nullable）。
  - `deleted_reason`: `Text`, nullable。
- 唯一性调整：原唯一索引改为包含 `is_deleted` 的复合唯一（MySQL: `UNIQUE (key..., is_deleted)`）以允许软删后重建同 key。
- 软删操作：提供 `soft_delete(user_id, reason=None)` 工具方法，设置字段并提交；恢复可清空上述字段并置 `is_deleted=false`。
- 默认查询：服务层/DAO 引入通用过滤器，除非显式 `include_deleted=True`。

## 4. 关联切换到 business_id

- 新增 `*_business_id` 列（`String(32)` + 索引）并回填，过渡期同时保留 `*_id`。
- 关联映射建议：
  - Episode → Story：`story_business_id`
  - Script → Episode：`episode_business_id`
  - StoryCharacter → Story/VirtualIP：`story_business_id`、`virtual_ip_business_id`
  - StoryStepOutline → Story/Episode/Treatment：`story_business_id`、`episode_business_id`、`story_treatment_business_id`
  - Scene → Script/StoryStepOutline/Environment：`script_business_id`、`story_step_outline_business_id`、`environment_business_id`
  - SceneBeat → Scene：`scene_business_id`
  - Shot → Scene/SceneBeat：`scene_business_id`、`scene_beat_business_id`
  - VirtualIPImage → VirtualIP：`virtual_ip_business_id`
  - Task → User/target entity（按需要补充 `target_business_id` 字段）
  - UserAuditLog → User/Admin：对应 `*_business_id`
- 代码使用顺序：优先写/读 `*_business_id`，回退到 `*_id` 仅用于兼容；响应体中始终返回 `business_id`。

## 5. 行为与兼容

- 删除接口：从硬删改为软删；需要 `deleted_by`（当前用户），`deleted_reason` 可选；默认列表/详情不返回软删数据。
- 恢复能力：如需，可暴露 admin 级恢复接口（清空软删字段并写入审计）。
- 再生成（regenerate）：
  - Episode/Script regenerate 创建新记录（含新的 `business_id`/`id`），复制必要字段；旧记录软删并附加 `deleted_reason='regenerate superseded'`。
  - 下游派生数据（scenes/scene_beats/shots 等）跟随新记录重建；旧派生数据软删或与旧记录共存但默认不可见。
  - 前端在 regenerate 后切换到新记录（以 `business_id` 为主）。
- 唯一键：在软删后允许重建，例如 Episode `(story_id, episode_number, is_deleted)`，VirtualIP `name` 同理；对需要全局唯一的 `business_id` 维持独立唯一索引。

## 6. 迁移方案（分阶段）

- Phase 0：准备
  - 落地 `SoftDeleteBusinessMixin`，梳理所有模型/外键/唯一约束清单。
  - 评估数据库版本（MySQL 8+ 假设）；确认部分索引/表达式兼容性。
- Phase 1：字段落地与回填
  - Alembic：为所有表添加 `business_id`、软删字段、唯一/普通索引；回填现有行 `business_id`。
  - 移除 `business_id` server_default，避免后续写入遗漏校验。
  - 默认查询层统一增加 `is_deleted=false` 过滤（服务/DAO）。
- Phase 2：关联 backfill 与双写
  - 为各子表添加 `*_business_id`，通过 `JOIN` 旧 `id` 回填。
  - API/Service 写入时同时写 `id` 与 `business_id` 关联；响应增加 `business_id`。
  - 调整唯一约束为含 `is_deleted` 的复合唯一。
- Phase 3：业务语义切换
  - 删除接口改为软删；新增可选恢复接口（如需要）。
  - regenerate 改为“新建记录 + 旧记录软删”；派生数据重建/软删策略落地。
  - 前端改为使用 `business_id` 作为路由/请求参数优先键，兼容旧 `id` 只读。
- Phase 4：收口与清理
  - 代码默认只用 `business_id`（`id` 仅保留内部 FK）；下线兼容分支。
  - 数据自检：`business_id` 唯一性、软删过滤覆盖度、外键回填完整性。
  - 文档/测试收口。

## 7. 测试与验证

- 后端：`pytest` 覆盖新增软删行为、唯一约束（软删后重建）、regenerate 新 ID 流程、关联回填正确性。
- 前端：`npm run lint`，关键页面（故事/剧集/剧本/虚拟 IP/环境/任务）切换到 `business_id` 后的端到端验证；regenerate 返回新 ID 路由跳转。
- 数据校验脚本：迁移后校验 `business_id` 唯一、`*_business_id` 非空、软删过滤是否生效（抽样查询）。

## 8. 风险与回滚

- 风险：索引/约束迁移时间长；部分唯一约束改造错误导致写入失败；代码漏加 `is_deleted` 过滤导致脏数据暴露；前端未及时切换导致 404。
- 回滚：逐阶段可回退 Alembic；保留旧 `id` 关联使快速回退可用；在切流前保持双写，问题时可切回 `id` 读写。
