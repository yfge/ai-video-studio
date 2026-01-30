# 音乐生成 (Music Generation)

> 使用本接口，输入歌词和歌曲描述，进行歌曲生成。

## OpenAPI

```yaml api-reference/music/api/openapi.json post /v1/music_generation
openapi: 3.1.0
info:
  title: MiniMax Music Generation API
  description: >-
    MiniMax music generation API with support for creating music from text
    prompts and lyrics
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/music_generation:
    post:
      tags:
        - Music
      summary: Music Generation
      operationId: generateMusic
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
              $ref: "#/components/schemas/GenerateMusicReq"
        required: true
      responses:
        "200":
          description: ""
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenerateMusicResp"
components:
  schemas:
    GenerateMusicReq:
      type: object
      required:
        - model
        - prompt
        - lyrics
      properties:
        model:
          type: string
          description: 使用的模型名称，`music-2.0`
          enum:
            - music-2.0
        prompt:
          type: string
          description: 音乐的描述，用于指定风格、情绪和场景。例如“流行音乐, 难过, 适合在下雨的晚上”。长度限制为 [10, 2000] 个字符
          minLength: 10
          maxLength: 2000
        lyrics:
          type: string
          description: |-
            歌曲的歌词。使用
             分隔每行。你可以在歌词中加入 `[Intro]`, `[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]` 等结构标签来优化生成的音乐结构。长度限制为 [10, 3000] 个字符
          minLength: 10
          maxLength: 3000
        stream:
          type: boolean
          description: 是否使用流式传输，默认为 `false`
          default: false
        output_format:
          type: string
          description: >-
            音频的返回格式，可选值为 `url` 或 `hex`，默认为 `hex`。当 `stream` 为 `true` 时，仅支持 `hex`
            格式。注意：url 的有效期为 24 小时，请及时下载
          enum:
            - url
            - hex
          default: hex
        audio_setting:
          $ref: "#/components/schemas/AudioSetting"
        aigc_watermark:
          type: boolean
          description: "是否在音频末尾添加水印，默认为 `false`。仅在非流式 (`stream: false`) 请求时生效"
      example:
        model: music-2.0
        prompt: 独立民谣,忧郁,内省,渴望,独自漫步,咖啡馆
        lyrics: |-
          [verse]
          街灯微亮晚风轻抚
          影子拉长独自漫步
          旧外套裹着深深忧郁
          不知去向渴望何处
          [chorus]
          推开木门香气弥漫
          熟悉的角落陌生人看
        audio_setting:
          sample_rate: 44100
          bitrate: 256000
          format: mp3
    GenerateMusicResp:
      type: object
      properties:
        data:
          $ref: "#/components/schemas/MusicData"
        base_resp:
          $ref: "#/components/schemas/BaseResp"
      example:
        data:
          audio: hex编码的音频数据
          status: 2
        trace_id: 04ede0ab069fb1ba8be5156a24b1e081
        extra_info:
          music_duration: 25364
          music_sample_rate: 44100
          music_channel: 2
          bitrate: 256000
          music_size: 813651
        analysis_info: null
        base_resp:
          status_code: 0
          status_msg: success
    AudioSetting:
      type: object
      description: 音频输出配置
      properties:
        sample_rate:
          type: integer
          description: 采样率。可选值：`16000`, `24000`, `32000`, `44100`
        bitrate:
          type: integer
          description: 比特率。可选值：`32000`, `64000`, `128000`, `256000`
        format:
          type: string
          description: 音频编码格式。
          enum:
            - mp3
            - wav
            - pcm
    MusicData:
      type: object
      properties:
        status:
          type: integer
          description: |-
            音乐合成状态：
            1: 合成中
            2: 已完成
        audio:
          type: string
          description: 当 `output_format` 为 `hex` 时返回，是音频文件的 16 进制编码字符串
    BaseResp:
      type: object
      description: 状态码及详情
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：

            `0`: 请求成功

            `1002`: 触发限流，请稍后再试

            `1004`: 账号鉴权失败，请检查 API-Key 是否填写正确

            `1008`: 账号余额不足

            `1026`: 图片描述涉及敏感内容

            `2013`: 传入参数异常，请检查入参是否按要求填写

            `2049`: 无效的api key

            更多内容可查看 [错误码查询列表](/api-reference/errorcode) 了解详情
        status_msg:
          type: string
          description: 具体错误详情
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
