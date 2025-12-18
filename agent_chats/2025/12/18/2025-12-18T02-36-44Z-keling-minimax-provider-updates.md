---
id: 2025-12-18T02-36-44Z-keling-minimax-provider-updates
date: 2025-12-18T02:36:44Z
participants: [human, claude]
models: [claude-sonnet-4-5]
tags: [backend, providers, keling, minimax, video-generation, jwt-auth, api-integration]
related_paths:
  - ai-pic-backend/app/services/keling_auth.py
  - ai-pic-backend/app/services/providers/keling_provider.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-backend/app/services/minimax_client.py
  - ai-pic-backend/app/services/providers/polling_utils.py
  - ai-pic-backend/app/services/providers/retry_utils.py
summary: "Implemented Phase 1 & 2 of Keling and MiniMax provider updates: JWT authentication for Keling, unified task polling utilities, and video generation for both providers"
---

## User Prompt

继续实现Keling和MiniMax的API集成，基于之前创建的文档。

## Goals

1. **Phase 1: Core Infrastructure**
   - Create JWT authentication manager for Keling AI
   - Add GET method support to MiniMax client
   - Implement unified task polling utilities
   - Create retry decorators with auth refresh

2. **Phase 2: Keling Provider Updates**
   - Update authentication to use JWT (HS256)
   - Change base URL to official endpoint
   - Add V2 series models (kling-v2-6, v2-5-turbo, v2-1-master, v2-1)
   - Implement new image generation endpoint
   - Implement new video generation endpoint with multiple modes
   - Add multi-image video generation support

3. **Phase 3: MiniMax Provider Updates**
   - Add video generation models (Hailuo series, I2V series)
   - Implement video generation endpoint
   - Implement task polling and file retrieval

## Changes

### New Files Created

1. **ai-pic-backend/app/services/keling_auth.py** (214 lines)
   - `KelingAuthManager` class for JWT token management
   - HS256 algorithm signing using AccessKey/SecretKey
   - Token caching with 5-minute refresh buffer (30min TTL)
   - Thread-safe implementation with lock
   - Methods: `generate_token()`, `get_valid_token()`, `invalidate_cache()`, `get_auth_header()`, `is_token_valid()`, `get_token_info()`

2. **ai-pic-backend/app/services/providers/polling_utils.py** (230 lines)
   - `TaskPoller` class for unified async task polling
   - `TaskStatus` enum for standardized status mapping
   - Exponential backoff support (configurable)
   - Provider-specific status mappers: `keling_status_mapper()`, `minimax_status_mapper()`
   - Configurable max_attempts, delays, and result extraction

3. **ai-pic-backend/app/services/providers/retry_utils.py** (220 lines)
   - `async_retry()` decorator with exponential backoff
   - Retryable HTTP status codes (429, 500, 502, 503, 504)
   - Retryable provider error codes (1002, 1039, 5000, 5001, 5002)
   - `async_retry_with_auth_refresh()` specialized decorator for JWT auth refresh
   - Automatic token invalidation on 401/403/1004 errors

### Modified Files

4. **ai-pic-backend/app/services/minimax_client.py**
   - Added `get_json()` method for GET requests (lines 114-141)
   - Supports query parameters
   - Reuses existing auth and error handling
   - Used for video task status queries and file retrieval

5. **ai-pic-backend/app/services/providers/keling_provider.py** (Complete overhaul, 644 lines)
   - **Authentication**: Replaced simple Bearer token with JWT authentication
     - Initialize `KelingAuthManager` in `__init__()`
     - New `_get_auth_headers()` method for dynamic token injection
     - Validate both api_key (AccessKey) and api_secret (SecretKey)

   - **Base URL**: Updated to `https://api-beijing.klingai.com`

   - **Model List**: Added V2 series models
     - V2 models: kling-v2-6, kling-v2-5-turbo, kling-v2-1-master, kling-v2-1
     - V1 models: kling-v1-6, kling-v1-5, kling-v1 (kept for compatibility)
     - Image models: kling-image-v2, kling-image-v1

   - **Image Generation** (`generate_image()`): New endpoint POST /v1/images/generations
     - Parameters: model_name, prompt, negative_prompt, image, image_reference, image_fidelity, human_fidelity, resolution (1k/2k), n, aspect_ratio
     - Task creation + polling flow
     - Polling: `_poll_image_task()` → GET /v1/images/generations/{task_id}

   - **Video Generation** (`generate_video()`): New endpoint POST /v1/videos/image2video
     - Parameters: model_name, image (required), image_tail (optional), prompt, negative_prompt, mode (std/pro), duration (5/10), cfg_scale (V1 only), camera_control
     - Support for first-frame and first-last-frame modes
     - Polling: `_poll_video_task()` → GET /v1/videos/image2video/{task_id}

   - **Multi-Image Video** (`generate_video_from_multiple_images()`): New endpoint POST /v1/videos/multi-image2video
     - kling-v1-6 only
     - 2-4 images support
     - Reuses video task polling

   - **Updated Methods**:
     - `_initialize_client()`: Uses JWT headers
     - `get_task_status()`: Updated to support both image and video task types
     - Removed old `_poll_task_status()` (replaced by specialized pollers)

6. **ai-pic-backend/app/services/providers/minimax_provider.py** (Updated, 576 lines)
   - **Imports**: Added `polling_utils` import

   - **Supported Types**: Added `IMAGE_TO_VIDEO` and `TEXT_TO_VIDEO`

   - **Video Models**: Added 6 video generation models
     - Hailuo series: MiniMax-Hailuo-2.3, MiniMax-Hailuo-2.3-Fast, MiniMax-Hailuo-02
     - I2V series: I2V-01-Director, I2V-01-live, I2V-01

   - **Video Generation** (`generate_video()`): New endpoint POST /v1/video_generation
     - Parameters: model, first_frame_image (required), last_frame_image (optional), prompt, duration (6/10), resolution (512P/720P/768P/1080P), prompt_optimizer, fast_pretreatment, aigc_watermark
     - Task creation + polling + file retrieval flow

   - **Task Polling** (`_poll_video_task()`): GET /v1/query/video_generation
     - Polls task status (Preparing/Queueing/Processing/Success/Fail)
     - Automatically retrieves file info when task succeeds
     - Max 120 attempts × 10s = 20 minutes timeout

   - **File Retrieval** (`_retrieve_video_file()`): GET /v1/files/retrieve
     - Gets download URL for generated video
     - Returns file metadata (file_id, filename, bytes, created_at)

## Validation

### Syntax Validation

```bash
cd /Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-backend

# Validate new files
python3 -m py_compile app/services/keling_auth.py
python3 -m py_compile app/services/providers/polling_utils.py
python3 -m py_compile app/services/providers/retry_utils.py

# Validate updated files
python3 -m py_compile app/services/providers/keling_provider.py
python3 -m py_compile app/services/providers/minimax_provider.py
python3 -m py_compile app/services/minimax_client.py
```

All files passed syntax validation with no errors.

### Code Structure Verification

✅ **Keling Provider**:
- JWT authentication initialized properly
- All 3 endpoints implemented (image, video, multi-image-video)
- Task polling uses unified TaskPoller
- Model list includes all V1 and V2 models

✅ **MiniMax Provider**:
- GET method added to client
- All 6 video models registered
- Video generation workflow complete (create → poll → retrieve)
- Uses unified TaskPoller with MiniMax status mapper

✅ **Infrastructure**:
- JWT token manager with caching
- Unified polling utilities
- Retry decorators with auth refresh support

## Key Implementation Details

### JWT Authentication Flow (Keling)
1. User provides `KELING_ACCESS_KEY` and `KELING_SECRET_KEY` in environment
2. `KelingAuthManager` generates JWT on first request:
   - Headers: `{"alg": "HS256", "typ": "JWT"}`
   - Payload: `{"iss": access_key, "exp": now+1800, "nbf": now-5}`
   - Signed with secret_key using HS256
3. Token cached for 30 minutes, refreshed 5 minutes before expiry
4. On 1004 error (auth failed), cache invalidated and new token generated

### Task Polling Strategy
- **Images**: 60 attempts × 5s = 5 minutes timeout
- **Videos**: 120 attempts × 10s = 20 minutes timeout
- Exponential backoff disabled by default (constant delay for predictability)
- Status mapping: provider-specific → standardized `TaskStatus` enum

### Error Handling
- **Keling codes**: 1000-1004 (auth), 1100-1103 (account), 1200-1203 (params), 1301-1304 (policy), 5000-5002 (server)
- **MiniMax codes**: 1000-1039 (various), 2013 (input format)
- Retry on transient errors: 429 (rate limit), 500-504 (server errors)
- Auth refresh on 401, 403, 1004

## Breaking Changes

### Keling Provider
⚠️ **Breaking**: Authentication mechanism changed from simple Bearer token to JWT
- **Before**: Only `api_key` required (used as Bearer token)
- **After**: Both `api_key` (AccessKey) and `api_secret` (SecretKey) required for JWT signing
- **Migration**: Users must update environment variables:
  ```bash
  # Old (no longer works)
  KELING_API_KEY=your_token

  # New (required)
  KELING_ACCESS_KEY=your_access_key
  KELING_SECRET_KEY=your_secret_key
  ```

⚠️ **Breaking**: Base URL changed
- **Before**: `https://klingai.com/api/v1`
- **After**: `https://api-beijing.klingai.com`

⚠️ **Breaking**: API endpoints changed
- Image generation: `/images/generate` → `/v1/images/generations`
- Video generation: `/videos/generations` or `/videos/image2video` → `/v1/videos/image2video`
- Task polling: `/tasks/{id}` → `/v1/images/generations/{id}` or `/v1/videos/image2video/{id}`

⚠️ **Breaking**: Method signatures changed
- `generate_image()`: New parameters (image_reference, image_fidelity, human_fidelity, aspect_ratio)
- `generate_video()`: Different parameters (image instead of image_url, new mode, camera_control)

### MiniMax Provider
✅ **No Breaking Changes**: All changes are additive
- New video generation capability added
- Existing text generation and TTS features unchanged

## Next Steps

1. **Unit Tests** (Phase 4, pending)
   - `test_keling_auth.py`: JWT generation, caching, refresh
   - `test_polling_utils.py`: Task polling, status mapping, timeouts
   - `test_retry_utils.py`: Retry logic, backoff, auth refresh
   - `test_keling_provider.py`: Image/video generation, JWT auth
   - `test_minimax_provider.py`: Video generation, task polling

2. **Integration Tests** (Phase 4, pending)
   - End-to-end Keling workflow in dev_in_docker
   - End-to-end MiniMax workflow in dev_in_docker
   - JWT token refresh scenarios
   - Long-running video generation (20min timeout)

3. **Documentation** (Phase 4, pending)
   - Update README with new environment variables
   - Migration guide for Keling users
   - API usage examples for video generation

4. **Environment Configuration**
   - User needs to configure in dev_in_docker:
     ```bash
     KELING_ACCESS_KEY=...
     KELING_SECRET_KEY=...
     MINIMAX_API_KEY=...
     MINIMAX_GROUP_ID=...
     ```

## Linked Commits

Commit will include all Phase 1 & 2 changes:
- New files: keling_auth.py, polling_utils.py, retry_utils.py
- Updated files: keling_provider.py, minimax_provider.py, minimax_client.py
- This agent_chats entry
