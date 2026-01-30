# 删除音色

> 使用本接口，对于生成的部分音色进行删除。

## OpenAPI

```yaml api-reference/speech/voice-management/api/openapi.json post /v1/delete_voice
openapi: 3.1.0
info:
  title: MiniMax Voice Management API
  description: MiniMax Voice Management API with support for getting and deleting voices
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/delete_voice:
    post:
      tags:
        - Voice
      summary: Delete Voice
      description: Delete a voice by ID and type
      operationId: deleteVoice
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
              $ref: "#/components/schemas/DeleteVoiceReq"
        required: true
      responses:
        "200":
          description: Successful response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/DeleteVoiceResp"
components:
  schemas:
    DeleteVoiceReq:
      type: object
      required:
        - voice_type
        - voice_id
      properties:
        voice_type:
          type: string
          description: >-
            取值范围：`voice_cloning`（克隆的音色）/`voice_generation`（基于文本提示生成的音色），注意仅支持删除这两种类别的音色
          enum:
            - voice_cloning
            - voice_generation
        voice_id:
          type: string
          description: 希望删除音色的 voice_id
      example:
        voice_type: voice_cloning
        voice_id: yanshang11123
    DeleteVoiceResp:
      type: object
      properties:
        voice_id:
          type: string
          description: 被删除声音的 voice_id
        created_time:
          type: string
          description: 该音色生成请求提交的时间，非首次调用生效激活时间，格式为 `yyyy-mm-dd`
        base_resp:
          $ref: "#/components/schemas/DeleteBaseResp"
      example:
        voice_id: yanshang11123
        created_time: "1728962464"
        base_resp:
          status_code: 0
          status_msg: success
    DeleteBaseResp:
      type: object
      description: 状态码及状态详情
      properties:
        status_code:
          type: integer
          format: int64
          description: |-
            状态码

            - `0`: 删除成功
            - `2013`: 输入参数信息不正常

            更多内容可查看 [错误码查询列表](/api-reference/errorcode) 了解详情
        status_msg:
          type: string
          description: 状态详情
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
