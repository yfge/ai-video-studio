# TESTING_GUIDE — 虚拟 IP 图像生成与图生图验证

本指南主要记录如何在 Docker + Nginx 开发环境下，用真实浏览器（推荐 Chrome）验证虚拟 IP 图像文生图 / 图生图流程，尤其是 Seedream 4.5 / DALL·E 等模型下的分辨率与图生图变体保存行为。

> 所有前后端联动、登录、AI 调用/图像生成等功能改动，**必须在真实浏览器中完成至少一次端到端路径验证**。本文件中的用例应在 `agent_chats` 的 `## Validation` 段中引用。

## 环境准备

- 启动 Docker 开发环境（只暴露 Nginx 端口）：
  - 后端：`ai-video-backend`（FastAPI，内部 `8000`）
  - 前端：`ai-video-frontend`（Next.js，经 `ai-video-nginx` 转发到 `http://localhost:8089`）
- 确保 MySQL / Redis 持久化目录已在 `.gitignore` 中忽略：
  - `docker/mysql_data/`
  - `docker/redis_data/`

## 登录与基础数据

1. 在 Chrome 打开 `http://localhost:8089/login`。
2. 使用已有账号登录（例如：`geyunfei` / `Gyf@845261`）。
3. 打开虚拟 IP 图像页：`http://localhost:8089/virtual-ip/1/images`。
   - 页面标题应为「`老拐 - 图像管理`」，列表中已有至少一张 `portrait` 图像。

## 文生图（Seedream 4.5 / DALL·E）分辨率验证

1. 在 `虚拟 IP 图像管理` 页点击「🤖 AI生成图像」，展开文生图表单。
2. 在「使用模型」下拉中分别选择：
   - `Seedream 4.5 — volcengine`：
     - 「分辨率」下拉只展示 `2K（Seedream 推荐）`。
     - 选择 `2K`，填写/保留提示词后点击「立即生成」。
     - 期望结果：
       - 请求命中 `/api/v1/virtual-ips/{id}/images/generate`，并由 Volcengine Ark `/images/generations` 完成生成。
       - 新图片保存为 `VirtualIPImage` 记录，标签包含 `ai_generated`，在网格顶部展示。
   - `DALL-E 3 — openai`：
     - 「分辨率」下拉显示 `1024x1024` / `1024x1792` / `1792x1024` 三个选项。
     - 分别选择不同长宽比进行生成，确认后端按 OpenAI 图像 API 官方 `size` 规格调用。
   - `DALL-E 2 — openai`：
     - 「分辨率」下拉显示 `256x256` / `512x512` / `1024x1024`。
     - 选择 1–2 个尺寸验证调用与返回。

> 注：如上游服务因配额/网络等原因返回错误，应在前端看到清晰的错误提示（非空白/无反馈），并在日志中记录实际 `size` 参数。

## 图生图（基于虚拟 IP 资产的变体）验证

### 1. 单张图生图变体（Seedream 4.5）

1. 在 `虚拟 IP 图像管理` 页，确保当前模型为 `Seedream 4.5`，分辨率可选 `2K`。
2. 在图像网格中选中一张 `portrait` 图像，点击该卡片上的「图生图」按钮。
3. 在弹出的「基于当前图像生成变体」对话框中：
   - 「使用模型」默认应为 `Seedream 4.5 — volcengine`（或该图的 `ai_model`）。
   - 「生成数量」保持为 `1 张`。
   - 「变体提示词」可保留默认文案（背面照/全身照）或进行适当修改。
4. 点击「生成变体」。
5. 期望结果：
   - Toast / 弹窗提示「图生图生成成功」。
   - 列表顶部新增 1 张新图片：
     - 标签包含 `ai_generated` 与 `variant`。
     - `category` 继承自原图（例如 `portrait`）。
   - 不再打开新标签页，也不会触发浏览器自动下载。

### 2. 多张图生图变体 + 分辨率透传

1. 同样在某张 Seedream 生成的图像上点击「图生图」。
2. 将「生成数量」设置为 `2 张` 或 `3 张`。
3. 保持模型选择为 `Seedream 4.5 — volcengine`。
4. 点击「生成变体」。
5. 期望结果：
   - 一次性新增多张 `variant` 图像，每张都作为新的 `VirtualIPImage` 出现在网格顶部。
   - 后端调用 `/api/v1/virtual-ips/{id}/images/{image_id}/variants` 时，
     - 请求体中带上 `count` 和（如有）`size` 字段。
     - `size` 目前复用文生图表单中已选择的 `size`，例如 Seedream 的 `2K`，并透传到统一的 `image_to_image` 调用。

> 当前阶段，图生图弹窗暂不单独展示分辨率下拉，而是**复用文生图已选的 `size`**。后续可以在任务看板中补充「按模型白名单提供独立图生图分辨率选项」的子任务。

## 日志与排错

- 后端日志关键点：
  - `ai-video-backend` 容器中搜索：
    - 文生图：`VirtualIP image gen | ip=`、`openai_dalle`、`ai_volcengine` 等关键字。
    - 图生图：`image_to_image fallback`、`图生图生成失败`、`variant` 等关键字。
- 典型问题：
  - Ark 报错 `image size must be at least 3686400 pixels`：
    - 说明 `size` 未设置为 `2K` 或其它合规规格，需要在模型白名单中校正。
  - DALL·E 报 400/500：
    - 优先检查 `size` 是否在官方允许列表中，再检查密钥/配额。

## 在 agent_chats 中记录验证

每次对虚拟 IP 图像生成 / 图生图流程进行改动时，`agent_chats/YYYY/MM/DD/*.md` 的 `## Validation` 段应至少包含：

- 所用浏览器与环境（例如「Chrome + docker-compose.dev + Nginx，仅暴露 8089」）。
- 实际执行的端到端用例：
  - 哪个虚拟 IP（例如「ID=1，角色：老拐」）。
  - 使用了哪些模型 / 分辨率（例如「Seedream 4.5 2K，图生图生成数量=2」）。
  - 前端 UI 行为（新图是否出现在网格、是否仍有自动下载/新窗口等）。
- 遇到的错误与解决方式（如 Ark 尺寸错误、DALL·E 接口报错等）。 

