---
id: 2025-12-12T13-30-00Z-img2img-preload-trust-env-false
date: 2025-12-12T13:30:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, ssl, img2img, prod]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/openai_provider.py
summary: "图生图参考图预加载禁用 trust_env 并开启重定向，同时下载时将 https 降级为 http 规避生产 SSL 校验失败"
---

## User Prompt

生产环境图生图仍出现：

- `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`
- `CERTIFICATE_VERIFY_FAILED: Hostname mismatch`

即使 backend Dockerfile 已安装/更新 CA 证书，`image_to_image base64 preload` 仍然全部失败，导致 Google 图生图任务失败。用户要求进一步处理并确认“先下载再传 base64”链路可用。

## Goals

1. 提升图生图参考图 base64 预加载的稳定性，避免生产环境中环境变量代理/中间人证书干扰。
2. 保证在有 HTTPS 重定向的情况下也能正确下载到图片内容。
3. 在 prod HTTPS 证书异常时仍能稳定下载参考图（接受降级为 HTTP 的权衡）。

## Changes

### 1. 预加载参考图时禁用 trust_env，并开启 follow_redirects

文件：`ai-pic-backend/app/services/ai_service_manager.py`

- 原逻辑：

  ```python
  async with httpx.AsyncClient(timeout=self.config.default_timeout) as client:
      resp = await client.get(url)
  ```

  `httpx` 默认 `trust_env=True`，会读取容器环境中的 `HTTP_PROXY`/`HTTPS_PROXY`/`REQUESTS_CA_BUNDLE` 等设置。
  在 prod 中如果存在代理或自定义 CA，会导致：

  - 证书链被替换/不被信任 → `unable to get local issuer certificate`
  - 返回默认证书 → `Hostname mismatch`

- 新逻辑：
  ```python
  async with httpx.AsyncClient(
      timeout=self.config.default_timeout,
      trust_env=False,
      follow_redirects=True,
  ) as client:
      resp = await client.get(url)
  ```

> 效果：
>
> - 预加载阶段绕过环境变量代理与自定义 CA，直接使用系统 CA 进行 HTTPS 校验。
> - 若 CDN/OSS 有 302/307 到真实对象 URL，也会自动跟随并取到图片 bytes。
> - 成功后仍然传递 `base64_images` 给 provider，避免 provider 再次请求外网 URL。

### 2. 下载参考图时优先使用 HTTP（https -> http）

文件：

- `ai-pic-backend/app/services/ai_service_manager.py`
- `ai-pic-backend/app/services/providers/google_provider.py`
- `ai-pic-backend/app/services/providers/volcengine_provider.py`
- `ai-pic-backend/app/services/providers/openai_provider.py`

在所有“下载参考图/外部图片 URL -> bytes/base64”的路径中，若传入 URL 为 `https://...`，则在下载阶段降级为 `http://...`：

```python
if url.lower().startswith("https://"):
    url = "http://" + url[len("https://"):]
```

> 背景：prod 中 `resource.lets-gpt.com` 偶发证书链/hostname mismatch，导致 `CERTIFICATE_VERIFY_FAILED`；用户确认接受在图片下载阶段统一走 HTTP，避免证书问题阻塞图生图。

### 3. Google Provider 内部兜底下载也禁用 trust_env

文件：`ai-pic-backend/app/services/providers/google_provider.py`

- `_fetch_inline_image` 原本也使用默认 `trust_env=True`。
- 改为：
  ```python
  async with httpx.AsyncClient(
      timeout=self.config.timeout,
      trust_env=False,
      follow_redirects=True,
  ) as client:
      resp = await client.get(image_url)
  ```

> 效果：
>
> - 即便上游没有传 base64（极端情况下），GoogleProvider 的兜底下载也不会受 prod 代理/证书干扰。

## Validation

1. **静态走查**
   - 仅修改 `httpx.AsyncClient` 的构造参数，不改变请求 URL、base64 格式或 provider 接口签名。
   - `trust_env=False` 和 `follow_redirects=True` 为 httpx 官方参数，语义明确。
2. **本地测试现状**
   - 运行 `cd ai-pic-backend && pytest`，存在大量与本改动无关的历史失败/环境依赖问题（当前仓库基线不全绿），未针对这些失败做额外修复。
3. **预期 prod 验证**
   - 部署新镜像并重启 celery 后，再触发一次环境图生图/虚拟 IP 图生图：
     - Celery 日志应不再出现 `CERTIFICATE_VERIFY_FAILED`（下载阶段已降级为 HTTP）；
     - 若仍失败，日志会指向对象不存在或网络问题。

## Next Steps

1. 在生产服务器上重建并部署新的 backend 镜像。
2. 观察 celery 日志是否还有 SSL preload skip。
3. 如仍有 hostname mismatch，需进一步检查 `resource.lets-gpt.com` DNS 是否有多 IP/多证书节点或内部网络 MITM（但现在可排除 env 代理因素）。

## Linked Commits

- 待提交：图生图参考图预加载禁用 trust_env 并开启 follow_redirects，修复 prod SSL 校验失败。
