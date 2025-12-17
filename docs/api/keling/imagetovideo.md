# Kling AI API - 图生视频

## 创建任务

### 接口信息

| 网络协议 | 请求地址 | 请求方法 | 请求格式 | 响应格式 |
|---------|---------|---------|---------|---------|
| https | /v1/videos/image2video | POST | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 请求体

> **注意**
> 为了保持命名统一，原 `model` 字段变更为 `model_name` 字段，未来请您使用该字段来指定需要调用的模型版本。
> 同时，我们保持了行为上的向前兼容，如您继续使用原 `model` 字段，不会对接口调用有任何影响、不会有任何异常，等价于 `model_name` 为空时的默认行为（即调用V1模型）

#### 请求示例

```bash
curl --location --request POST 'https://api-beijing.klingai.com/v1/videos/image2video' \
--header 'Authorization: Bearer xxx' \
--header 'Content-Type: application/json' \
--data-raw '{
    "model_name": "kling-v1",
    "mode": "pro",
    "duration": "5",
    "image": "https://h2.inkwai.com/bs2/upload-ylab-stunt/se/ai_portal_queue_mmu_image_upscale_aiweb/3214b798-e1b4-4b00-b7af-72b5b0417420_raw_image_0.jpg",
    "prompt": "宇航员站起身走了",
    "cfg_scale": 0.5,
    "static_mask": "https://h2.inkwai.com/bs2/upload-ylab-stunt/ai_portal/1732888177/cOLNrShrSO/static_mask.png",
    "dynamic_masks": [
      {
        "mask": "https://h2.inkwai.com/bs2/upload-ylab-stunt/ai_portal/1732888130/WU8spl23dA/dynamic_mask_1.png",
        "trajectories": [
          {"x":279,"y":219},{"x":417,"y":65}
        ]
      }
    ]
}'
```

#### 请求参数

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| model_name | string | 可选 | kling-v1 | 模型名称<br>枚举值：`kling-v1`, `kling-v1-5`, `kling-v1-6`, `kling-v2-master`, `kling-v2-1`, `kling-v2-1-master`, `kling-v2-5-turbo`, `kling-v2-6` |
| image | string | 必须 | 空 | **参考图像**<br>- 支持传入图片Base64编码或图片URL（确保可访问）<br>- 图片格式支持 `.jpg` / `.jpeg` / `.png`<br>- 图片文件大小不能超过10MB<br>- 图片宽高尺寸不小于300px<br>- 图片宽高比介于 1:2.5 ~ 2.5:1 之间<br>- `image` 参数与 `image_tail` 参数至少二选一，二者不能同时为空<br>- `image + image_tail` 参数、`dynamic_masks/static_mask` 参数、`camera_control` 参数三选一，不能同时使用<br><br>**Base64编码注意事项：**<br>请确保您传递的所有图像数据参数均采用Base64编码格式。在提交数据时，请不要在Base64编码字符串前添加任何前缀（如 `data:image/png;base64,`）。<br><br>正确示例：`iVBORw0KGgoAAAANSUhEUgAAAAUA...`<br>错误示例：`data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...` |
| image_tail | string | 可选 | 空 | **参考图像 - 尾帧控制**<br>- 支持传入图片Base64编码或图片URL（确保可访问）<br>- 图片格式支持 `.jpg` / `.jpeg` / `.png`<br>- 图片文件大小不能超过10MB<br>- 图片宽高尺寸不小于300px<br>- `image` 参数与 `image_tail` 参数至少二选一，二者不能同时为空<br>- `image+image_tail` 参数、`dynamic_masks/static_mask` 参数、`camera_control` 参数三选一，不能同时使用<br>- Base64编码注意事项同 `image` 字段 |
| prompt | string | 可选 | 无 | **正向文本提示词**<br>- 不能超过2500个字符<br>- 用 `<<<voice_1>>>` 来指定音色，序号同 `voice_list` 参数所引用音色的排列顺序<br>- 一次视频生成任务至多引用2个音色；指定音色时，`sound` 参数值必须为 `on`<br>- 语法结构越简单越好，如：男人`<<<voice_1>>>`说："你好"<br>- 当 `voice_list` 参数不为空且 `prompt` 参数中引用音色ID时，视频生成任务按"有指定音色"计量计费 |
| negative_prompt | string | 可选 | 空 | **负向文本提示词**<br>不能超过2500个字符 |
| voice_list | array | 可选 | 无 | **生成视频时所引用的音色的列表**<br>- 一次视频生成任务至多引用2个音色<br>- 当 `voice_list` 参数不为空且 `prompt` 参数中引用音色ID时，视频生成任务按"有指定音色"计量计费<br><br>示例：<br>```json<br>"voice_list":[<br>  {"voice_id":"voice_id_1"},<br>  {"voice_id":"voice_id_2"}<br>]<br>``` |
| sound | string | 可选 | off | **生成视频时是否同时生成声音**<br>枚举值：`on`, `off`<br>仅V2.6及后续版本模型支持当前参数 |
| cfg_scale | float | 可选 | 0.5 | **生成视频的自由度**<br>值越大，模型自由度越小，与用户输入的提示词相关性越强<br>取值范围：[0, 1]<br>kling-v2.x模型不支持当前参数 |
| mode | string | 可选 | std | **生成视频的模式**<br>枚举值：`std`, `pro`<br>- `std`：标准模式，基础模式，性价比高<br>- `pro`：专家模式（高品质），高表现模式，生成视频质量更佳 |
| duration | string | 可选 | 5 | **生成视频时长**，单位：秒<br>枚举值：`5`, `10` |
| static_mask | string | 可选 | 无 | **静态笔刷涂抹区域**（用户通过运动笔刷涂抹的 mask 图片）<br>- "运动笔刷"能力包含"动态笔刷 `dynamic_masks`"和"静态笔刷 `static_mask`"两种<br>- 支持传入图片Base64编码或图片URL（确保可访问，格式要求同 `image` 字段）<br>- 图片格式支持 `.jpg` / `.jpeg` / `.png`<br>- 图片长宽比必须与输入图片相同（即 `image` 字段），否则任务失败<br>- `static_mask` 和 `dynamic_masks.mask` 这两张图片的分辨率必须一致，否则任务失败 |
| dynamic_masks | array | 可选 | 无 | **动态笔刷配置列表**<br>可配置多组（最多6组），每组包含"涂抹区域 mask"与"运动轨迹 trajectories"序列 |
| dynamic_masks[].mask | string | 可选 | 无 | **动态笔刷涂抹区域**（用户通过运动笔刷涂抹的 mask 图片）<br>- 支持传入图片Base64编码或图片URL（确保可访问，格式要求同 `image` 字段）<br>- 图片格式支持 `.jpg` / `.jpeg` / `.png`<br>- 图片长宽比必须与输入图片相同（即 `image` 字段），否则任务失败<br>- `static_mask` 和 `dynamic_masks.mask` 这两张图片的分辨率必须一致，否则任务失败 |
| dynamic_masks[].trajectories | array | 可选 | 无 | **运动轨迹坐标序列**<br>- 生成5s的视频，轨迹长度不超过77，即坐标个数取值范围：[2, 77]<br>- 轨迹坐标系，以图片左下角为坐标原点<br>- 注1：坐标点个数越多轨迹刻画越准确，如只有2个轨迹点则为这两点连接的直线<br>- 注2：轨迹方向以传入顺序为指向，以最先传入的坐标为轨迹起点，依次链接后续坐标形成运动轨迹 |
| dynamic_masks[].trajectories[].x | int | 可选 | 无 | 轨迹点横坐标（在像素二维坐标系下，以输入图片 `image` 左下为原点的像素坐标）|
| dynamic_masks[].trajectories[].y | int | 可选 | 无 | 轨迹点纵坐标（在像素二维坐标系下，以输入图片 `image` 左下为原点的像素坐标）|
| camera_control | object | 可选 | 空 | **控制摄像机运动的协议**<br>如未指定，模型将根据输入的文本/图片进行智能匹配 |
| camera_control.type | string | 可选 | 无 | **预定义的运镜类型**<br>枚举值：<br>- `simple`：简单运镜，此类型下可在 `config` 中六选一进行运镜<br>- `down_back`：镜头下压并后退 → 下移拉远，此类型下 `config` 参数无需填写<br>- `forward_up`：镜头前进并上仰 → 推进上移，此类型下 `config` 参数无需填写<br>- `right_turn_forward`：先右旋转后前进 → 右旋推进，此类型下 `config` 参数无需填写<br>- `left_turn_forward`：先左旋并前进 → 左旋推进，此类型下 `config` 参数无需填写 |
| camera_control.config | object | 可选 | 无 | **包含六个字段，用于指定摄像机在不同方向上的运动或变化**<br>- 当运镜类型指定 `simple` 时必填，指定其他类型时不填<br>- 以下参数6选1，即只能有一个参数不为0，其余参数为0 |
| camera_control.config.horizontal | float | 可选 | 无 | **水平运镜**<br>控制摄像机在水平方向上的移动量（沿x轴平移）<br>取值范围：[-10, 10]，负值表示向左平移，正值表示向右平移 |
| camera_control.config.vertical | float | 可选 | 无 | **垂直运镜**<br>控制摄像机在垂直方向上的移动量（沿y轴平移）<br>取值范围：[-10, 10]，负值表示向下平移，正值表示向上平移 |
| camera_control.config.pan | float | 可选 | 无 | **水平摇镜**<br>控制摄像机在水平面上的旋转量（绕y轴旋转）<br>取值范围：[-10, 10]，负值表示绕y轴向左旋转，正值表示绕y轴向右旋转 |
| camera_control.config.tilt | float | 可选 | 无 | **垂直摇镜**<br>控制摄像机在垂直面上的旋转量（沿x轴旋转）<br>取值范围：[-10, 10]，负值表示绕x轴向下旋转，正值表示绕x轴向上旋转 |
| camera_control.config.roll | float | 可选 | 无 | **旋转运镜**<br>控制摄像机的滚动量（绕z轴旋转）<br>取值范围：[-10, 10]，负值表示绕z轴逆时针旋转，正值表示绕z轴顺时针旋转 |
| camera_control.config.zoom | float | 可选 | 无 | **变焦**<br>控制摄像机的焦距变化，影响视野的远近<br>取值范围：[-10, 10]，负值表示焦距变长、视野范围变小，正值表示焦距变短、视野范围变大 |
| callback_url | string | 可选 | 无 | **本次任务结果回调通知地址**<br>如果配置，服务端会在任务状态发生变更时主动通知<br>具体通知的消息schema见"Callback协议" |
| external_task_id | string | 可选 | 无 | **自定义任务ID**<br>- 用户自定义任务ID，传入不会覆盖系统生成的任务ID，但支持通过该ID进行任务查询<br>- 请注意，单用户下需要保证唯一性 |

### 响应体

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
| https | /v1/videos/image2video/{id} | GET | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 请求路径参数

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|------|-------|------|
| task_id | string | 可选 | 无 | 图生视频的任务ID<br>请求路径参数，直接将值填写在请求路径中，与 `external_task_id` 两种查询方式二选一 |
| external_task_id | string | 可选 | 无 | 图生视频的自定义任务ID<br>创建任务时填写的 `external_task_id`，与 `task_id` 两种查询方式二选一 |

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
| https | /v1/videos/image2video | GET | application/json | application/json |

### 请求头

| 字段 | 值 | 描述 |
|-----|-----|-----|
| Content-Type | application/json | 数据交换格式 |
| Authorization | Bearer {token} | 鉴权信息，参考接口鉴权 |

### 查询参数

请求示例：`/v1/videos/image2video?pageNum=1&pageSize=30`

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
