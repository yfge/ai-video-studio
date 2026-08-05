## User Prompt

用户接受将成长拆为认知、能力、资源、活动/时间尺度四条可选全书曲线；这些曲线不作为逐章数值 KPI。继续解决真实长篇任务在第 20 章因不可截断 Canon 超过 32K 上下文预算而失败的问题，并完成真实 48 章生成与质量验收。

## Goals

- 保留 MySQL 中完整 Canon、状态和修订版动态实体目录。
- 章前规划与正文上下文只投影当前章节实际引用的实体、状态和知识。
- 不放宽 32K 硬约束门禁，不丢失当前章节所需的关系、位置和知识边界。
- 用真实失败调用的上下文包验证修复效果，并为后续正式 Resume 做准备。

## Changes

- 章前硬上下文不再复制完整 `revision_local_entities` 目录，只保留当前章引用的 `subjects` 状态。
- 章节规划包同样移除仅用于持久化查找的动态实体目录。
- 角色关注名的模糊匹配只适用于人物实体，避免旧概念名称因包含主角名而被误选。
- 人物 `knowledge` 只保留当前可见 Canon 引用，关系和所有权继续按现有可见性规则过滤。
- 增加大规模历史实体、目录性动态实体和历史知识的回归测试。

## Validation

- 真实 Task `#6878`、Revision `37a9fc7a35e048f8b95a42edaf59001b`、调用 `#3204` 的第 20 章上下文离线只读复算：硬上下文由 33,862 字符降到 13,800 字符；完整数据仍在数据库，Prompt 中保留 13 个当前相关实体。
- 受影响回归：29 passed。
- 完整 Story Novel 单测原始容器结果：790 passed、48 failed、1 skipped；48 项与既有 FastAPI `HTTPException.__str__` 环境兼容基线相同。
- 同一 839 项在测试进程内仅适配异常字符串后：838 passed、1 skipped。
- isort passed；black 首次机械整理 3 个文件，复跑 passed。

## Next Steps

- 完成仓库契约和差异检查后精确提交本切片。
- 重启 backend 与 Celery worker，通过正式 UI 从第 20 章 Resume，继续到 48/48。
- 完成连续性检查、GPT-5.6 分批与全书审读、读者吸引力结论、DOCX 和审批证据。

## Linked Commits

- Pending
