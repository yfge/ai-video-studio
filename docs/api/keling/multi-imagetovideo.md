# Kling AI API - 多图参考生视频

## 创建任务

### 接口信息

| 网络协议 | 请求地址 | 请求方法 | 请求格式 | 响应格式 |
|---------|---------|---------|---------|---------|
| https | /v1/videos/multi-image2video | POST | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 请求体

#### 请求参数

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| model_name | string | 可选 | kling-v1-6 | **模型名称**<br>枚举值：`kling-v1-6` |
| image_list | array | 必须 | 空 | **图片列表**<br>- 最多支持4张图片<br>- API端无裁剪逻辑，请直接上传已选主体后的图片<br>- 支持传入图片Base64编码或图片URL（确保可访问）<br>- 图片格式支持 `.jpg` / `.jpeg` / `.png`<br>- 图片文件大小不能超过10MB<br>- 图片宽高尺寸不小于300px<br>- 图片宽高比介于 1:2.5 ~ 2.5:1 之间<br><br>**Base64编码注意事项：**<br>请确保您传递的所有图像数据参数均采用Base64编码格式。在提交数据时，请不要在Base64编码字符串前添加任何前缀（如 `data:image/png;base64,`）。<br><br>正确示例：`iVBORw0KGgoAAAANSUhEUgAAAAUA...`<br>错误示例：`data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...`<br><br>**格式示例：**<br>```json<br>"image_list":[<br>  {"image":"image_url"},<br>  {"image":"image_url"},<br>  {"image":"image_url"},<br>  {"image":"image_url"}<br>]<br>``` |
| prompt | string | 必须 | 无 | **正向文本提示词**<br>不能超过2500个字符 |
| negative_prompt | string | 可选 | 空 | **负向文本提示词**<br>不能超过2500个字符 |
| mode | string | 可选 | std | **生成视频的模式**<br>枚举值：`std`, `pro`<br>- `std`：标准模式，基础模式，性价比高<br>- `pro`：专家模式（高品质），高表现模式，生成视频质量更佳 |
| duration | string | 可选 | 5 | **生成视频时长**，单位：秒<br>枚举值：`5`, `10` |
| aspect_ratio | string | 可选 | 16:9 | **生成图片的画面纵横比**（宽:高）<br>枚举值：`16:9`, `9:16`, `1:1` |
| callback_url | string | 可选 | 无 | **本次任务结果回调通知地址**<br>如果配置，服务端会在任务状态发生变更时主动通知<br>具体通知的消息schema见"Callback协议" |
| external_task_id | string | 可选 | 无 | **自定义任务ID**<br>- 用户自定义任务ID，传入不会覆盖系统生成的任务ID，但支持通过该ID进行任务查询<br>- 请注意，单用户下需要保证唯一性 |

### 响应体

创建任务的响应体结构与图生视频接口相同。

```json
{
  "code": 0,                      // 错误码；具体定义见错误码
  "message": "string",            // 错误信息
  "request_id": "string",         // 请求ID，系统生成，用于跟踪请求、排查问题
  "data": {
    "task_id": "string",          // 任务ID，系统生成
    "task_info": {
      "external_task_id": "string" // 客户自定义任务ID
    },
    "task_status": "string",      // 任务状态，枚举值：submitted（已提交）、processing（处理中）、succeed（成功）、failed（失败）
    "created_at": 1722769557708,  // 任务创建时间，Unix时间戳、单位ms
    "updated_at": 1722769557708   // 任务更新时间，Unix时间戳、单位ms
  }
}
```

---

## 查询任务（单个）

### 接口信息

| 网络协议 | 请求地址 | 请求方法 | 请求格式 | 响应格式 |
|---------|---------|---------|---------|---------|
| https | /v1/videos/multi-image2video/{id} | GET | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 请求路径参数

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| task_id | string | 可选 | 无 | 多图参考生视频的任务ID<br>请求路径参数，直接将值填写在请求路径中，与 `external_task_id` 两种查询方式二选一 |
| external_task_id | string | 可选 | 无 | 多图参考生视频的自定义任务ID<br>创建任务时填写的 `external_task_id`，与 `task_id` 两种查询方式二选一 |

### 请求体

无

### 响应体

```json
{
  "code": 0,                       // 错误码；具体定义见错误码
  "message": "string",             // 错误信息
  "request_id": "string",          // 请求ID，系统生成，用于跟踪请求、排查问题
  "data": {
    "task_id": "string",           // 任务ID，系统生成
    "task_status": "string",       // 任务状态，枚举值：submitted（已提交）、processing（处理中）、succeed（成功）、failed（失败）
    "task_status_msg": "string",   // 任务状态信息，当任务失败时展示失败原因（如触发平台的内容风控等）
    "task_info": {
      "external_task_id": "string" // 客户自定义任务ID
    },
    "task_result": {
      "videos": [
        {
          "id": "string",          // 生成的视频ID；全局唯一
          "url": "string",         // 生成视频的URL（请注意，为保障信息安全，生成的图片/视频会在30天后被清理，请及时转存）
          "duration": "string"     // 视频总时长，单位s
        }
      ]
    },
    "created_at": 1722769557708,   // 任务创建时间，Unix时间戳、单位ms
    "updated_at": 1722769557708    // 任务更新时间，Unix时间戳、单位ms
  }
}
```

---

## 查询任务（列表）

### 接口信息

| 网络协议 | 请求地址 | 请求方法 | 请求格式 | 响应格式 |
|---------|---------|---------|---------|---------|
| https | /v1/videos/multi-image2video | GET | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 查询参数

请求示例：`/v1/videos/multi-image2video?pageNum=1&pageSize=30`

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| pageNum | int | 可选 | 1 | 页码<br>取值范围：[1, 1000] |
| pageSize | int | 可选 | 30 | 每页数据量<br>取值范围：[1, 500] |

### 请求体

无

### 响应体

```json
{
  "code": 0,                       // 错误码；具体定义见错误码
  "message": "string",             // 错误信息
  "request_id": "string",          // 请求ID，系统生成，用于跟踪请求、排查问题
  "data": [
    {
      "task_id": "string",         // 任务ID，系统生成
      "task_status": "string",     // 任务状态，枚举值：submitted（已提交）、processing（处理中）、succeed（成功）、failed（失败）
      "task_status_msg": "string", // 任务状态信息，当任务失败时展示失败原因（如触发平台的内容风控等）
      "task_info": {
        "external_task_id": "string" // 客户自定义任务ID
      },
      "task_result": {
        "videos": [
          {
            "id": "string",        // 生成的视频ID；全局唯一
            "url": "string",       // 生成视频的URL（请注意，为保障信息安全，生成的图片/视频会在30天后被清理，请及时转存）
            "duration": "string"   // 视频总时长，单位s
          }
        ]
      },
      "created_at": 1722769557708, // 任务创建时间，Unix时间戳、单位ms
      "updated_at": 1722769557708  // 任务更新时间，Unix时间戳、单位ms
    }
  ]
}
```
