# Kling AI API - 图像生成

## 创建任务

### 接口信息

| 网络协议 | 请求地址 | 请求方法 | 请求格式 | 响应格式 |
|---------|---------|---------|---------|---------|
| https | /v1/images/generations | POST | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 请求体

> **注意**
> 为了保持命名统一，原 `model` 字段变更为 `model_name` 字段，未来请您使用该字段来指定需要调用的模型版本。
> 同时，我们保持了行为上的向前兼容，如您继续使用原 `model` 字段，不会对接口调用有任何影响、不会有任何异常，等价于 `model_name` 为空时的默认行为（即调用V1模型）

#### 请求参数

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| model_name | string | 可选 | kling-v1 | **模型名称**<br>枚举值：`kling-v1`, `kling-v1-5`, `kling-v2`, `kling-v2-new`, `kling-v2-1` |
| prompt | string | 必须 | 无 | **正向文本提示词**<br>不能超过2500个字符 |
| negative_prompt | string | 可选 | 空 | **负向文本提示词**<br>- 不能超过2500个字符<br>- 注：图生图（即 `image` 字段不为空时）场景下，不支持负向提示词 |
| image | string | 可选 | 空 | **参考图像**<br>- 支持传入图片Base64编码或图片URL（确保可访问）<br>- 图片格式支持 `.jpg` / `.jpeg` / `.png`<br>- 图片文件大小不能超过10MB<br>- 图片宽高尺寸不小于300px<br>- 图片宽高比介于 1:2.5 ~ 2.5:1 之间<br>- `image_reference` 参数不为空时，当前参数必填<br><br>**Base64编码注意事项：**<br>请确保您传递的所有图像数据参数均采用Base64编码格式。在提交数据时，请不要在Base64编码字符串前添加任何前缀（如 `data:image/png;base64,`）。<br><br>正确示例：`iVBORw0KGgoAAAANSUhEUgAAAAUA...`<br>错误示例：`data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...` |
| image_reference | string | 可选 | 无 | **图片参考类型**<br>枚举值：<br>- `subject`：角色特征参考<br>- `face`：人物长相参考<br><br>- 使用 `face`（人物长相参考）时，上传图片需仅含1张人脸<br>- 使用 `kling-v1-5` 且 `image` 参数不为空时，当前参数必填<br>- 仅 `kling-v1-5` 支持当前参数 |
| image_fidelity | float | 可选 | 0.5 | **生成过程中对用户上传图片的参考强度**<br>取值范围：[0, 1]，数值越大参考强度越大 |
| human_fidelity | float | 可选 | 0.45 | **面部参考强度**<br>即参考图中人物五官相似度<br>- 仅 `image_reference` 参数为 `subject` 时生效<br>- 取值范围：[0, 1]，数值越大参考强度越大 |
| resolution | string | 可选 | 1k | **生成图片的清晰度**<br>枚举值：`1k`, `2k`<br>- `1k`：1K标清<br>- `2k`：2K高清<br>- 不同模型版本支持范围不同，详见能力地图 |
| n | int | 可选 | 1 | **生成图片数量**<br>取值范围：[1, 9] |
| aspect_ratio | string | 可选 | 16:9 | **生成图片的画面纵横比**（宽:高）<br>枚举值：`16:9`, `9:16`, `1:1`, `4:3`, `3:4`, `3:2`, `2:3`, `21:9`<br>不同模型版本支持的范围不同，详见能力地图 |
| callback_url | string | 可选 | 无 | **本次任务结果回调通知地址**<br>如果配置，服务端会在任务状态发生变更时主动通知<br>具体通知的消息schema见"Callback协议" |

### 响应体

```json
{
  "code": 0,                      // 错误码；具体定义见错误码
  "message": "string",            // 错误信息
  "request_id": "string",         // 请求ID，系统生成，用于跟踪请求、排查问题
  "data": {
    "task_id": "string",          // 任务ID，系统生成
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
| https | /v1/images/generations/{id} | GET | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 请求路径参数

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| task_id | string | 必须 | 无 | 图片生成的任务ID<br>请求路径参数，直接将值填写在请求路径中 |

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
    "created_at": 1722769557708,   // 任务创建时间，Unix时间戳、单位ms
    "updated_at": 1722769557708,   // 任务更新时间，Unix时间戳、单位ms
    "task_result": {
      "images": [
        {
          "index": 0,              // 图片编号，0-9
          "url": "string"          // 生成图片的URL（请注意，为保障信息安全，生成的图片/视频会在30天后被清理，请及时转存）
        }
      ]
    }
  }
}
```

---

## 查询任务（列表）

### 接口信息

| 网络协议 | 请求地址 | 请求方法 | 请求格式 | 响应格式 |
|---------|---------|---------|---------|---------|
| https | /v1/images/generations | GET | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 查询参数

请求示例：`/v1/images/generations?pageNum=1&pageSize=30`

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
      "created_at": 1722769557708, // 任务创建时间，Unix时间戳、单位ms
      "updated_at": 1722769557708, // 任务更新时间，Unix时间戳、单位ms
      "task_result": {
        "images": [
          {
            "index": 0,            // 图片编号，0-9
            "url": "string"        // 生成图片的URL（请注意，为保障信息安全，生成的图片/视频会在30天后被清理，请及时转存）
          }
        ]
      }
    }
  ]
}
```
