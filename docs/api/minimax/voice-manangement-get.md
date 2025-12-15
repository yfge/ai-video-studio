# 查询可用音色ID

> 使用本接口支持查询不同分类下的音色信息。

## OpenAPI

````yaml api-reference/speech/voice-management/api/openapi.json post /v1/get_voice
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
  /v1/get_voice:
    post:
      tags:
        - Voice
      summary: Get Voice
      operationId: getVoice
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
        description: ''
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GetVoiceReq'
        required: true
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetVoiceResp'
components:
  schemas:
    GetVoiceReq:
      type: object
      required:
        - voice_type
      properties:
        voice_type:
          type: string
          description: |-
            希望查询音色类型，支持以下取值：

            - `system`: 系统音色
            - `voice_cloning`: 快速复刻的音色，仅在成功用于语音合成后才可查询
            - `voice_generation`: 文生音色接口生成的音色，仅在成功用于语音合成后才可查询
            - `all`: 以上全部
          enum:
            - system
            - voice_cloning
            - voice_generation
            - all
      example:
        voice_type: all
    GetVoiceResp:
      type: object
      properties:
        system_voice:
          type: array
          items:
            $ref: '#/components/schemas/SystemVoiceInfo'
          description: 包含系统预定义的音色。
        voice_cloning:
          type: array
          items:
            $ref: '#/components/schemas/VoiceCloningInfo'
          description: 包含音色快速复刻的音色数据
        voice_generation:
          type: array
          items:
            $ref: '#/components/schemas/VoiceGenerationInfo'
          description: 包含音色生成接口产生的音色数据
        base_resp:
          $ref: '#/components/schemas/BaseResp'
      example:
        system_voice:
          - voice_id: Chinese (Mandarin)_Reliable_Executive
            description:
              - 一位沉稳可靠的中年男性高管声音，标准普通话，传递出值得信赖的感觉。
            voice_name: 沉稳高管
            created_time: '1970-01-01'
          - voice_id: Chinese (Mandarin)_News_Anchor
            description:
              - 一位专业、播音腔的中年女性新闻主播，标准普通话。
            voice_name: 新闻女声
            created_time: '1970-01-01'
        voice_cloning:
          - voice_id: test12345
            description: []
            created_time: '2025-08-20'
          - voice_id: test12346
            description: []
            created_time: '2025-08-21'
        voice_generation:
          - voice_id: ttv-voice-2025082011321125-2uEN0X1S
            description: []
            created_time: '2025-08-20'
          - voice_id: ttv-voice-2025082014225025-ZCQt0U0k
            description: []
            created_time: '2025-08-20'
        base_resp:
          status_code: 0
          status_msg: success
    SystemVoiceInfo:
      type: object
      properties:
        voice_id:
          type: string
          description: 音色 ID
        voice_name:
          type: string
          description: 音色名称，非调用的音色 ID
        description:
          type: array
          items:
            type: string
          description: 音色描述
    VoiceCloningInfo:
      type: object
      properties:
        voice_id:
          type: string
          description: 音色 ID
        description:
          type: array
          items:
            type: string
          description: 生成音色时填写的音色描述
        created_time:
          type: string
          description: 创建时间，格式 yyyy-mm-dd
    VoiceGenerationInfo:
      type: object
      properties:
        voice_id:
          type: string
          description: 音色 ID
        description:
          type: array
          items:
            type: string
          description: 生成音色时填写的音色描述
        created_time:
          type: string
          description: 创建时间，格式 yyyy-mm-dd
    BaseResp:
      type: object
      description: 本次请求的状态码和详情
      properties:
        status_code:
          type: integer
          format: int64
          description: |-
            状态码。

            - `0`: 请求结果正常
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

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt