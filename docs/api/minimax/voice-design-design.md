# 音色设计

> 使用本接口，输入文本内容，进行音色设计。

## OpenAPI

```yaml api-reference/speech/voice-design/api/openapi.json post /v1/voice_design
openapi: 3.1.0
info:
  title: MiniMax Voice Design API
  description: MiniMax Voice Design API with support for voice generation from text prompts
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/voice_design:
    post:
      tags:
        - Voice
      summary: Voice Design
      operationId: voiceDesign
      parameters:
        - name: Content-Type
          in: header
          required: true
          description: 请求体的媒介类型，请设置为 `application/json`，确保请求数据的格式为 JSON
          schema:
            type: string
            enum:
              - application/json
            default: application/json
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/T2VReq"
        required: true
      responses:
        "200":
          description: ""
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/T2VResp"
components:
  schemas:
    T2VReq:
      type: object
      required:
        - prompt
        - preview_text
      properties:
        prompt:
          type: string
          description: 音色描述。
        preview_text:
          type: string
          description: |-
            试听音频文本。
            注：试听音频的合成将收取 2 元/万字符的费用
        voice_id:
          type: string
          description: 自定义生成音色的 voice_id。当不传入此参数时，将自动生成并返回一个唯一的 `voice_id`
        aigc_watermark:
          type: boolean
          description: 是否在合成试听音频的末尾添加音频节奏标识，默认值为 False
      example:
        prompt: 讲述悬疑故事的播音员，声音低沉富有磁性，语速时快时慢，营造紧张神秘的氛围。
        preview_text: 夜深了，古屋里只有他一人。窗外传来若有若无的脚步声，他屏住呼吸，慢慢地，慢慢地，走向那扇吱呀作响的门……
    T2VResp:
      type: object
      properties:
        voice_id:
          type: string
          description: 生成的音色 ID，可用于语音合成
        trial_audio:
          type: string
          description: 使用生成的音色合成的试听音频，以 hex 编码形式返回
        base_resp:
          type: object
          description: 状态码和状态详情
          properties:
            status_code:
              type: integer
              format: int64
              description: |-
                状态码。

                - `0`: 请求结果正常
                - `1000`: 未知错误
                - `1001`: 超时
                - `1002`: 触发 RPM 限流
                - `1004`: 鉴权失败
                - `1008`: 余额不足
                - `1013`: 服务内部错误
                - `1027`: 输出内容错误
                - `1039`: 触发 TPM 限流
                - `2013`: 输入格式信息不正常

                更多内容可查看 [错误码查询列表](/api-reference/errorcode) 了解详情
            status_msg:
              type: string
              description: 状态详情
      example:
        trial_audio: hex 编码音频
        voice_id: ttv-voice-2025060717322425-xxxxxxxx
        base_resp:
          status_code: 0
          status_msg: success
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |-
        `HTTP: Bearer Auth`
         - Security Scheme Type: http
         - HTTP Authorization Scheme: Bearer API_key，用于验证账户信息，可在 [账户管理>接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 中查看。
```

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt
