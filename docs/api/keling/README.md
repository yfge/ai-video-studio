# Kling AI API 文档

可灵（Kling AI）图像和视频生成 API 完整文档集。

## 文档目录

### 1. [公共信息](./common-info.md)

包含所有 API 接口的通用信息：

- **调用域名**：`https://api-beijing.klingai.com`
- **接口鉴权**：JWT Token 生成方法（Python 示例）
- **错误码对照表**：完整的 HTTP 状态码和业务码说明

### 2. [图生视频 API](./imagetovideo.md)

单图参考生成视频的完整接口文档：

- **创建任务** - `POST /v1/videos/image2video`
  - 支持图片 URL 或 Base64 编码
  - 支持首尾帧控制
  - 支持运动笔刷（静态/动态）
  - 支持摄像机运镜控制
  - 支持音色控制

- **查询单个任务** - `GET /v1/videos/image2video/{id}`
- **查询任务列表** - `GET /v1/videos/image2video`

### 3. [多图参考生视频 API](./multi-imagetovideo.md)

多图（最多4张）参考生成视频的接口文档：

- **创建任务** - `POST /v1/videos/multi-image2video`
  - 支持最多 4 张参考图片
  - 支持自定义画面纵横比（16:9, 9:16, 1:1）

- **查询单个任务** - `GET /v1/videos/multi-image2video/{id}`
- **查询任务列表** - `GET /v1/videos/multi-image2video`

### 4. [图像生成 API](./image-generation.md)

文生图和图生图的完整接口文档：

- **创建任务** - `POST /v1/images/generations`
  - 支持文生图和图生图两种模式
  - 支持多种画面比例（16:9, 9:16, 1:1, 4:3, 3:4, 3:2, 2:3, 21:9）
  - 支持 1K/2K 清晰度
  - 支持批量生成（最多9张）
  - 支持角色特征参考和人物长相参考（kling-v1-5）

- **查询单个任务** - `GET /v1/images/generations/{id}`
- **查询任务列表** - `GET /v1/images/generations`

### 5. [能力地图](./capability-map.md)

详细的模型版本能力对照表：

#### 视频生成能力
- kling-v1 系列（v1, v1-5, v1-6）
- kling-v2 系列（v2-master, v2-1, v2-1-master, v2-5-turbo, v2-6）
- kling-video-o1
- 分辨率和帧率对比
- 各模型支持的功能（首尾帧、运动笔刷、运镜控制、声音控制等）

#### 图像生成能力
- kling-image-o1
- kling-v1 系列
- kling-v2 系列
- 支持的画面比例
- 清晰度对比（1K/2K）

## 快速开始

### 1. 获取认证信息

首先从可灵开发者平台获取 AccessKey 和 SecretKey。

### 2. 生成 API Token

参考 [公共信息文档](./common-info.md) 中的 JWT Token 生成方法。

### 3. 调用 API

选择合适的接口：

- 单图生视频 → [图生视频 API](./imagetovideo.md)
- 多图生视频 → [多图参考生视频 API](./multi-imagetovideo.md)
- 文生图/图生图 → [图像生成 API](./image-generation.md)

### 4. 查询能力支持

在调用前，建议先查阅 [能力地图](./capability-map.md) 确认目标模型版本支持所需功能。

## 重要提示

- 生成的图片/视频会在 **30天后被清理**，请及时转存
- Base64 编码时不要添加 `data:image/png;base64,` 前缀
- 图片格式支持：`.jpg` / `.jpeg` / `.png`
- 图片文件大小限制：≤ 10MB
- 图片尺寸要求：≥ 300px
- 图像生成最多支持一次生成 9 张图片

## 技术支持

如有问题，请联系可灵 AI 客服。
