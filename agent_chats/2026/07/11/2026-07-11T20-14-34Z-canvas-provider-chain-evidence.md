## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交；可以拉起 dev_in_docker 用内置浏览器检验。

## Goals

- 在当前环境集中验证图片候选、人工选图、视频候选、人工选片和 Timeline 回填。
- 核对 Run ID 恢复、浏览器 console、provider task、媒体资产和 stable clip lineage。

## Changes

- 将当前环境 provider-backed 整链标记为完成，并把真实 Run、Task、candidate、Timeline 和 clip 标识写入任务板与设计文档。
- 新增 `canvas-provider-chain.json`，集中记录浏览器、请求、provider、资产和 DB lineage 证据。

## Validation

- In-app Browser：Run `9a4bbfdb95f846e4be216beb1b09ad88` 复用 Timeline `69` v5，图片候选 `442` 保持已选用。
- Provider：Task `6325` 通过 MiniMax `MiniMax-Hailuo-2.3` 生成视频候选 `443`，人工选用成功。
- Timeline：candidate `443` 显式写入 stable clip `video_scene_90_beat_3991_001`，Timeline 从 v5 更新到 v6。
- DB：`timeline_clip_assets.id=1484`、`media_asset_id=443`、`asset_role=generated_video`、`timeline_version=6`。
- 恢复：通过相同 Run ID 恢复后仍显示“已选用”和“已放入 Timeline v6”。
- Console：无 error 级日志。
- `jq empty artifacts/runs/9a4bbfdb95f846e4be216beb1b09ad88/canvas-provider-chain.json` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `pre-commit run --files <changed-docs-and-ledger>` -> passed.

## Next Steps

- 当前 Production Canvas 图片候选到 Timeline 的 P0 退出标准已满足；后续 provider 账户与模型可用性作为运维配置维护。

## Linked Commits

- `90751b20 fix(canvas): reuse mapped timeline support`
- Pending
