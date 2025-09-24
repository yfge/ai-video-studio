# 阿里云OSS集成指南

本项目已集成阿里云OSS云存储服务，实现AI生成的图像、视频和音频文件的自动上传和管理。

## 功能特性

### 🚀 自动上传
- **图像生成**: AI生成的图像会自动上传到OSS，并返回OSS链接
- **视频生成**: AI生成的视频和缩略图会自动上传到OSS
- **音频生成**: AI生成的音频文件会自动上传到OSS
- **智能分类**: 根据文件类型自动分类存储

### 📁 存储结构
```
ai-generated/
├── virtual-ip/           # 虚拟IP图像
├── videos/              # AI生成视频
├── thumbnails/          # 视频缩略图
├── audio/               # AI生成音频
└── image/               # 其他AI生成图像
```

### 🔧 API接口

#### AI生成接口（自动上传）
- `POST /api/v1/ai/generate/image` - 生成图像并自动上传
- `POST /api/v1/ai/generate/video` - 生成视频并自动上传  
- `POST /api/v1/ai/generate/speech` - 生成语音并自动上传

#### OSS存储管理接口
- `POST /api/v1/ai/storage/upload-url` - 从URL上传文件
- `POST /api/v1/ai/storage/batch-upload` - 批量上传文件
- `GET /api/v1/ai/storage/list` - 列出存储对象
- `GET /api/v1/ai/storage/info/{object_key}` - 获取对象信息
- `DELETE /api/v1/ai/storage/{object_key}` - 删除存储对象
- `GET /api/v1/ai/storage/signed-url/{object_key}` - 生成签名URL
- `GET /api/v1/ai/storage/status` - 获取OSS服务状态

## 配置说明

### 1. 阿里云OSS设置

在阿里云控制台完成以下步骤：

1. **创建OSS Bucket**
   - 登录阿里云控制台
   - 进入OSS服务
   - 创建新的Bucket（建议选择就近地域）
   - 设置访问权限为"公共读"

2. **获取访问密钥**
   - 进入AccessKey管理
   - 创建新的AccessKey
   - 记录AccessKey ID和AccessKey Secret

3. **配置跨域访问**（可选）
   ```json
   {
     "allowedOrigins": ["*"],
     "allowedMethods": ["GET", "PUT", "POST", "DELETE"],
     "allowedHeaders": ["*"],
     "exposeHeaders": ["ETag"]
   }
   ```

### 2. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 阿里云OSS配置
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
ALIYUN_OSS_BUCKET=your-bucket-name
ALIYUN_OSS_DOMAIN=https://your-custom-domain.com  # 可选，自定义域名
```

**配置说明：**
- `ALIYUN_ACCESS_KEY_ID`: 阿里云AccessKey ID
- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云AccessKey Secret  
- `ALIYUN_OSS_ENDPOINT`: OSS服务端点（根据Bucket地域选择）
- `ALIYUN_OSS_BUCKET`: OSS Bucket名称
- `ALIYUN_OSS_DOMAIN`: 自定义域名（可选，不配置则使用默认域名）

### 3. 常用Endpoint地址

| 地域 | Endpoint |
|------|----------|
| 华北2（北京） | https://oss-cn-beijing.aliyuncs.com |
| 华东1（杭州） | https://oss-cn-hangzhou.aliyuncs.com |
| 华东2（上海） | https://oss-cn-shanghai.aliyuncs.com |
| 华南1（深圳） | https://oss-cn-shenzhen.aliyuncs.com |

## 使用示例

### 1. 生成图像并自动上传

```python
import httpx

async def generate_image():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ai/generate/image",
            json={
                "prompt": "一个可爱的卡通角色",
                "style": "anime",
                "width": 1024,
                "height": 1024
            },
            headers={"Authorization": "Bearer your-token"}
        )
        
        result = response.json()
        if result["success"]:
            print(f"图像已生成并上传: {result['data']['images'][0]}")
            print(f"OSS链接: {result['data'].get('oss_upload', {}).get('file_url')}")
```

### 2. 批量上传文件

```python
async def batch_upload():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ai/storage/batch-upload",
            json={
                "urls": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.png"
                ],
                "file_type": "image",
                "prefix": "batch-upload",
                "metadata": {
                    "batch_id": "batch_001",
                    "source": "external"
                }
            },
            headers={"Authorization": "Bearer your-token"}
        )
        
        result = response.json()
        print(f"成功上传: {result['data']['success_count']} 个文件")
```

### 3. 列出存储文件

```python
async def list_files():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/ai/storage/list",
            params={
                "prefix": "ai-generated/",
                "max_keys": 50
            },
            headers={"Authorization": "Bearer your-token"}
        )
        
        result = response.json()
        for obj in result["data"]["objects"]:
            print(f"文件: {obj['key']}, 大小: {obj['size']}, URL: {obj['url']}")
```

## 响应格式

### AI生成接口响应

```json
{
  "success": true,
  "data": {
    "images": ["https://your-bucket.oss-cn-beijing.aliyuncs.com/ai-generated/image/20241215/12345678.png"],
    "original_image_url": "https://original-provider-url.com/image.png",
    "oss_upload": {
      "success": true,
      "object_key": "ai-generated/image/20241215/12345678.png",
      "file_url": "https://your-bucket.oss-cn-beijing.aliyuncs.com/ai-generated/image/20241215/12345678.png",
      "file_size": 1024000,
      "content_type": "image/png",
      "upload_time": "2024-12-15T10:30:00.000Z",
      "metadata": {
        "style": "anime",
        "provider": "openai",
        "model": "dall-e-3"
      }
    },
    "provider_used": "openai",
    "model_used": "dall-e-3"
  }
}
```

### 存储管理接口响应

```json
{
  "success": true,
  "data": {
    "objects": [
      {
        "key": "ai-generated/image/20241215/12345678.png",
        "size": 1024000,
        "last_modified": "2024-12-15T10:30:00.000Z",
        "etag": "\"d41d8cd98f00b204e9800998ecf8427e\"",
        "url": "https://your-bucket.oss-cn-beijing.aliyuncs.com/ai-generated/image/20241215/12345678.png"
      }
    ],
    "is_truncated": false,
    "next_marker": ""
  }
}
```

## 安全建议

### 1. AccessKey安全
- 定期轮换AccessKey
- 使用RAM子账号，仅授予必要权限
- 不要在代码中硬编码AccessKey

### 2. Bucket权限
- 合理设置Bucket访问权限
- 启用防盗链保护
- 配置访问日志记录

### 3. 文件安全
- 定期备份重要文件
- 启用版本控制
- 设置生命周期规则自动清理临时文件

## 故障排除

### 常见问题

1. **上传失败: 403 Forbidden**
   - 检查AccessKey权限
   - 确认Bucket访问策略
   - 验证Endpoint地址是否正确

2. **上传失败: 404 Not Found**
   - 检查Bucket名称是否正确
   - 确认Endpoint与Bucket地域匹配

3. **文件访问失败**
   - 检查Bucket读权限设置
   - 确认文件是否存在
   - 验证自定义域名配置

### 调试方法

1. **检查OSS服务状态**
   ```bash
   curl -H "Authorization: Bearer your-token" \
        http://localhost:8000/api/v1/ai/storage/status
   ```

2. **查看服务日志**
   ```bash
   tail -f logs/app.log | grep OSS
   ```

3. **测试基本连接**
   ```python
   from app.services.storage.oss_service import oss_service
   
   # 测试连接
   result = oss_service.list_objects(max_keys=1)
   print(result)
   ```

## 扩展功能

### 自定义存储策略

可以通过修改 `OSSService` 类来实现：

1. **自定义对象键生成规则**
2. **添加文件类型验证**
3. **实现智能压缩**
4. **添加水印功能**
5. **集成CDN加速**

### 监控和统计

建议集成以下监控功能：

1. **上传成功率统计**
2. **存储容量监控**
3. **访问量统计**
4. **成本分析**

---

通过以上集成，您的AI视频工作室现在具备了强大的云存储能力，可以自动管理AI生成的所有媒体文件，提供更好的用户体验和系统性能。