---
id: 2025-12-17T14-10-00Z-keling-api-documentation
date: 2025-12-17T14:10:00Z
participants: [human, claude]
models: [claude-sonnet-4-5]
tags: [documentation, api, keling]
related_paths:
  - docs/api/keling/README.md
  - docs/api/keling/common-info.md
  - docs/api/keling/imagetovideo.md
  - docs/api/keling/multi-imagetovideo.md
  - docs/api/keling/image-generation.md
  - docs/api/keling/capability-map.md
summary: "Created comprehensive Kling AI API documentation including authentication, image/video generation endpoints, and capability mapping"
---

## User Prompt

用户要求将 Kling AI（可灵）的 API 文档从网页内容整理成 markdown 格式保存到项目中，包括：

1. 公共信息（调用域名、接口鉴权、错误码）
2. 图生视频接口文档
3. 多图参考生视频接口文档
4. 图像生成接口文档
5. 能力地图（各模型版本支持的功能对照表）

## Goals

- 从用户提供的网页内容中提取 Kling AI API 文档信息
- 将所有 API 文档整理成规范的 markdown 格式
- 创建完整的文档集，包括索引、接口文档和能力地图
- 确保文档结构清晰、格式统一、易于查阅

## Changes

### 新增文件

1. **docs/api/keling/README.md** - 文档索引和快速开始指南

   - 包含所有文档的导航链接
   - 快速开始流程说明
   - 重要提示和技术支持信息

2. **docs/api/keling/common-info.md** - 公共信息

   - 调用域名：`https://api-beijing.klingai.com`
   - JWT Token 鉴权方法（包含 Python 示例代码）
   - 完整的错误码对照表（HTTP 状态码和业务码）

3. **docs/api/keling/imagetovideo.md** - 图生视频接口

   - 创建任务接口：`POST /v1/videos/image2video`
   - 查询单个任务接口：`GET /v1/videos/image2video/{id}`
   - 查询任务列表接口：`GET /v1/videos/image2video`
   - 支持功能：首尾帧控制、运动笔刷、摄像机运镜控制、音色控制

4. **docs/api/keling/multi-imagetovideo.md** - 多图参考生视频接口

   - 创建任务接口：`POST /v1/videos/multi-image2video`（支持最多4张图片）
   - 查询单个任务接口：`GET /v1/videos/multi-image2video/{id}`
   - 查询任务列表接口：`GET /v1/videos/multi-image2video`
   - 支持自定义画面纵横比

5. **docs/api/keling/image-generation.md** - 图像生成接口

   - 创建任务接口：`POST /v1/images/generations`
   - 查询单个任务接口：`GET /v1/images/generations/{id}`
   - 查询任务列表接口：`GET /v1/images/generations`
   - 支持文生图和图生图两种模式
   - 支持多种画面比例、1K/2K 清晰度、批量生成（最多9张）

6. **docs/api/keling/capability-map.md** - 能力地图
   - 视频生成能力对照表（kling-v1 系列、kling-v2 系列、kling-video-o1）
   - 图像生成能力对照表（kling-image-o1、kling-v1 系列、kling-v2 系列）
   - 分辨率、帧率和清晰度对比
   - 各模型版本支持的功能详情

### 文档特点

- 使用统一的 markdown 表格格式展示接口信息和参数
- 所有代码示例使用语法高亮的代码块
- 参数说明详细，包含类型、必填性、默认值和描述
- 重要提示使用 blockquote 突出显示
- 接口之间使用分隔线清晰划分

## Validation

### 文档完整性检查

```bash
ls -lh docs/api/keling/
```

确认创建了6个文档文件：

- README.md (3.1K) - 索引
- common-info.md (3.8K) - 公共信息
- imagetovideo.md (15K) - 图生视频
- multi-imagetovideo.md (7.7K) - 多图生视频
- image-generation.md (7.7K) - 图像生成
- capability-map.md (7.1K) - 能力地图

### 内容验证

- ✅ 所有文档使用规范的 markdown 格式
- ✅ 表格格式统一，对齐清晰
- ✅ 代码示例包含语法高亮
- ✅ 参数说明完整详细
- ✅ 能力地图涵盖所有模型版本
- ✅ README 提供清晰的导航和快速开始指南

### Git 状态

```bash
git status
```

确认 `docs/api/keling/` 目录为新增的未跟踪文件。

## Next Steps

- 提交这些文档到 git 仓库
- 如需要，可以添加更多接口文档（如文生视频、视频续写等）
- 可以考虑添加接口调用的完整示例代码
- 可以在主 README 中添加对这些 API 文档的引用

## Linked Commits

将在下一个 commit 中提交。
