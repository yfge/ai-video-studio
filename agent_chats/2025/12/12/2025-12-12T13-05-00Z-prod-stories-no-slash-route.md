---
id: 2025-12-12T13-05-00Z-prod-stories-no-slash-route
date: 2025-12-12T13:05:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, api, prod, stories]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip.py
summary: "为 /api/v1/stories 增加无尾斜杠路由，消除 307 重定向导致的故事列表访问问题"
---

## User Prompt

生产环境访问 `https://video.lets-gpt.com/api/v1/stories?limit=50` 返回 `307 Temporary Redirect`，怀疑故事列表接口有问题，导致异步生成的故事虽然任务完成但列表中看不到。

## Goals

1. 排查 `GET /api/v1/stories` 在 prod 环境返回 307 的原因。
2. 让前端使用的 `/api/v1/stories?limit=50` 调用直接返回 200，而不是 307 重定向。
3. 确保异步生成的故事在任务完成后可以通过故事列表接口正常查询到。

## Changes

### 1. 原因分析

- 后端 `stories` 路由定义在 `ai-pic-backend/app/api/v1/endpoints/stories.py` 中：
  ```python
  @router.get("/")
  async def get_stories(...):
      ...
  ```
  在 `api_router.include_router(stories.router, prefix="/stories")` 的前提下：
  - 实际路径是：`/api/v1/stories/`
  - 当客户端请求 `/api/v1/stories?limit=50`（不带尾斜杠）时，FastAPI/Starlette 会返回 307 到 `/api/v1/stories/?limit=50`。
- 在本地 dev 环境，浏览器/Next.js 通常会自动跟随 307，因此影响不明显；
- 在 prod 通过 nginx + 反向代理 + 跨域访问时，这个 307 会直接暴露出来，并有可能跟其他代理规则叠加产生意料之外的行为（例如额外的跨协议重定向），用户自然怀疑“列表接口有问题”。

### 2. 新增无尾斜杠路由以消除 307（stories / episodes / scripts / virtual-ips）

- 修改文件：`ai-pic-backend/app/api/v1/endpoints/stories.py`
- 在已有的：
  ```python
  @router.get("/")
  async def get_stories(...):
      ...
  ```
  下方新增一个别名路由：
  ```python
  @router.get("", include_in_schema=False)
  async def get_stories_no_slash(
      skip: int = Query(0, ge=0),
      limit: int = Query(100, ge=1, le=100),
      genre: Optional[str] = Query(None),
      status: Optional[str] = Query(None),
      current_user: User = Depends(get_current_active_user),
      db: Session = Depends(get_db),
  ):
      """
      兼容无尾斜杠的 /api/v1/stories 请求，避免 307 重定向。

      内部直接复用 get_stories 的过滤与分页逻辑。
      """
      return await get_stories(
          skip=skip,
          limit=limit,
          genre=genre,
          status=status,
          current_user=current_user,
          db=db,
      )
  ```

> 效果：  
> - `GET /api/v1/stories?limit=50` 和 `GET /api/v1/stories/?limit=50` 都直接返回 200 列表，无需 307。  
> - OpenAPI 文档只展示 `/stories/` 这一条路由，避免重复。

- 修改文件：`ai-pic-backend/app/api/v1/endpoints/episodes.py`
  - 原有路由：
    ```python
    @router.get("/", response_model=List[EpisodeResponse])
    async def get_episodes(...):
        ...
    ```
  - 新增别名路由：
    ```python
    @router.get("", response_model=List[EpisodeResponse], include_in_schema=False)
    async def get_episodes_no_slash(...):
        return await get_episodes(...)
    ```
  - 影响路径：`/api/v1/episodes` 与 `/api/v1/episodes/`。

- 修改文件：`ai-pic-backend/app/api/v1/endpoints/scripts.py`
  - 原有路由：
    ```python
    @router.get("/", response_model=List[ScriptResponse])
    async def get_scripts(...):
        ...
    ```
  - 新增别名路由：
    ```python
    @router.get("", response_model=List[ScriptResponse], include_in_schema=False)
    async def get_scripts_no_slash(...):
        return await get_scripts(...)
    ```
  - 影响路径：`/api/v1/scripts` 与 `/api/v1/scripts/`。

- 修改文件：`ai-pic-backend/app/api/v1/endpoints/virtual_ip.py`
  - 原有路由：
    ```python
    @router.get("/")
    def list_virtual_ips(...):
        ...
    ```
  - 新增别名路由：
    ```python
    @router.get("", include_in_schema=False)
    def list_virtual_ips_no_slash(...):
        return list_virtual_ips(...)
    ```
  - 影响路径：`/api/v1/virtual-ips` 与 `/api/v1/virtual-ips/`。

### 3. 与任务/故事生成链路的关系

- 异步生成故事 `/api/v1/stories/generate-async` 链路不变：
  - 创建 `Task`（status=pending）；
  - Celery 任务 `tasks.story_generate` 调用 `_process_story_generation_task`；
  - 插入 `Story` 记录（`status="draft"`）；
  - 更新 Task 为 `completed`，并写 `result_file_path="story:<id>"`。
- 列表接口 `GET /api/v1/stories` 负责按 `user_id`、`genre`、`status` 过滤 Story：
  - 普通用户：只看自己的故事；
  - 管理员/超管：可查看所有用户的故事；
  - 支持 `?status=draft` 等状态筛选。
- 前端 `storyAPI.getStories` 调用的正是 `/api/v1/stories?limit=50`，在本次修复后会直接命中 `get_stories_no_slash`，从而不再出现 307，列表能稳定拿到数据。

## Validation

1. **本地静态检查**
   - 确认 `stories.py` 中新加的路由签名与 `get_stories` 一致，调用方式是 `await get_stories(...)`（因为原函数是 async）。
   - 确认添加了 `include_in_schema=False`，避免在 OpenAPI 中重复暴露两条等价路由。
2. **预期 prod 行为**
   - 部署更新后，在生产环境访问：
     - `GET https://video.lets-gpt.com/api/v1/stories?limit=50`
     - `GET https://video.lets-gpt.com/api/v1/episodes?story_id=...`
     - `GET https://video.lets-gpt.com/api/v1/scripts?episode_id=...`
     - `GET https://video.lets-gpt.com/api/v1/virtual-ips?limit=...`
       - 这些请求都应直接返回 200，而非 307 重定向。
   - 「故事管理」页调用 `storyAPI.getStories` 不再遇到 307，可以正常显示包括新生成的草稿在内的故事列表。

## Next Steps

1. 在生产服务器上拉取最新代码并重启 backend 服务（或重新部署容器镜像），使新路由生效。
2. 用浏览器 DevTools 在「故事管理」页查看：
   - `GET /api/v1/stories?limit=50` 的状态码和返回体；
   - 确认不再有 307，且 `data` 数组中包含最近异步生成的故事（状态为 `draft`）。
3. 如后续发现其他模块也有 `/xxx` 与 `/xxx/` 之间 307 的情况（例如 episodes、scripts），可以按同样模式补充无斜杠路由别名。

## Linked Commits

- 待提交：为 stories 路由增加无尾斜杠 `GET ""` 别名，消除 `/api/v1/stories` 访问时的 307 重定向，保证故事列表在 prod 环境下正常返回。
