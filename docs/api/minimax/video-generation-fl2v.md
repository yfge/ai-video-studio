# 首尾帧生成视频

> 使用本接口上传首尾帧图片及文本内容，创建视频生成任务。

## OpenAPI

````yaml api-reference/video/generation/api/start-end-to-video.json post /v1/video_generation
openapi: 3.1.0
info:
  title: MiniMax API
  description: MiniMax video generation and file management API
  license:
    name: MIT
  version: 1.0.0
servers:
  - url: https://api.minimaxi.com
security:
  - bearerAuth: []
paths:
  /v1/video_generation:
    post:
      tags:
        - Video
      summary: Video Generation
      operationId: videoGeneration
      parameters:
        - name: Content-Type
          in: header
          required: true
          description: 请求体的媒介类型，请设置为 `application/json` 确保请求数据的格式为 JSON.
          schema:
            type: string
            enum:
              - application/json
            default: application/json
      requestBody:
        description: ""
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/VideoGenerationReq"
        required: true
      responses:
        "200":
          description: ""
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/VideoGenerationResp"
components:
  schemas:
    VideoGenerationReq:
      type: object
      required:
        - model
        - last_frame_image
      properties:
        model:
          type: string
          description: |-
            模型名称。可用值： `MiniMax-Hailuo-02`。

            注意：首尾帧生成功能不支持 512P 分辨率。
          enum:
            - MiniMax-Hailuo-02
        prompt:
          type: string
          description: "视频的文本描述，最大 2000 字符。对于 `MiniMax-Hailuo-02` ，支持使用 `[指令]` 语法进行运镜控制。\n可在 prompt 中通过 [指令] 格式添加运镜指令，以实现精确的镜头控制。\n\n- 支持 15 种运镜指令的指令:\n\t - 左右移: [左移], [右移]\n\t - 左右摇: [左摇], [右摇]\n\t - 推拉: [推进], [拉远]\n\t - 升降: [上升], [下降]\n\t - 上下摇: [上摇], [下摇]\n\t - 变焦: [变焦推近], [变焦拉远]\n\t - 其他: [晃动], [跟随], [固定]\n\n - 使用规则:\n\t - 组合运镜: 同一组 [] 内的多个指令会同时生效，如 [左摇,上升]，建议组合不超过 3 个\n\t - 顺序运镜: prompt 中前后出现的指令会依次生效，如 \"...[推进], 然后...[拉远]\"\n\t - 自然语言: 也支持通过自然语言描述运镜，但使用标准指令能获得更准确的响应 "
        first_frame_image:
          type: string
          description: "将指定图片作为视频的**起始帧**。支持公网 URL 或 Base64 编码的 [Data URL](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data) (`data:image/jpeg;base64,...`)\n\n- 图片要求：\n\t- 格式：JPG, JPEG, PNG, WebP\n\t- 体积：小于 20MB\n\t- 尺寸：短边像素大于 300px，长宽比在 2:5 和 5:2 之间 \n\n⚠️ 生成视频尺寸遵循首帧图片"
        last_frame_image:
          type: string
          description: "将指定图片作为视频的**结束帧**。支持公网 URL 或 Base64 编码的 [Data URL](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data) (`data:image/jpeg;base64,...`)\n\n- 图片要求：\n\t- 格式：JPG, JPEG, PNG, WebP\n\t- 体积：小于 20MB\n\t- 尺寸：短边像素大于 300px，长宽比在 2:5 和 5:2 之间\n\n⚠️ 生成视频尺寸遵循首帧图片，当首帧和尾帧的图片尺寸不一致时，模型将参考首帧对尾帧图片进行裁剪"
        prompt_optimizer:
          type: boolean
          description: 是否自动优化 `prompt`，默认为 `true`。设为 `false` 可进行更精确的控制
        duration:
          type: integer
          description: |-
            视频时长（秒），默认值为 6。首尾帧生成可用值与分辨率相关：

            | Model | 768P | 1080P |
            | :--- | :--- | :--- |
            | MiniMax-Hailuo-02 | `6` 或 `10` | `6` |
        resolution:
          type: string
          description: |-
            视频分辨率。首尾帧生成支持 768P 和 1080P：
            | Model | 6s | 10s |
            | :--- | :--- | :--- |
            | MiniMax-Hailuo-02 | `768P` (默认), `1080P` | `768P` |
          enum:
            - 768P
            - 1080P
        callback_url:
          type: string
          description: "接收任务状态更新通知的回调 URL。支持通过 callback_url 参数可以配置回调，以接收任务状态的更新的异步通知。\n\n地址验证：配置后，MiniMax 服务器会向 callback_url 发送一个 POST 请求，请求体中包含 challenge 字段。服务端需要在 3 秒内原样返回该 challenge 值以完成验证\n状态更新：验证成功后，每当任务状态变更时，MiniMax 都会向该 URL 推送最新的任务状态。推送的数据结构与调用查询视频生成任务接口的响应体一致\n\n回调返回的\"status\"包括以下状态：\n- `\"processing\"` - 生成中\n- `\"success\"` - 成功\n- `\"failed\"` - 失败\n\n```python\nfrom fastapi import FastAPI, HTTPException, Request\r\nimport json\r\n\r\napp = FastAPI()\r\n\r\n@app.post(\"/get_callback\")\r\nasync def get_callback(request: Request):\r\n    try:\r\n        json_data = await request.json()\r\n        challenge = json_data.get(\"challenge\")\r\n        if challenge is not None:\r\n            # Validation request, echo back challenge\r\n            return {\"challenge\": challenge}\r\n        else:\r\n            # Status update request, handle accordingly\r\n            # {\r\n            #     \"task_id\": \"115334141465231360\",\r\n            #     \"status\": \"success\",\r\n            #     \"file_id\": \"205258526306433\",\r\n            #     \"base_resp\": {\r\n            #         \"status_code\": 0,\r\n            #         \"status_msg\": \"success\"\r\n            #     }\r\n            # }\r\n            return {\"status\": \"success\"}\r\n    except Exception as e:\r\n        raise HTTPException(status_code=500, detail=str(e))\r\n\r\nif __name__ == \"__main__\":\r\n    import uvicorn\r\n    uvicorn.run(\r\n        app,  # 必选\r\n        host=\"0.0.0.0\",  # 必选\r\n        port=8000,  # 必选，端口可设置\r\n        # ssl_keyfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n        # ssl_certfile=\"yourname.yourDomainName.com.key\",  # 可选，看是否开启ssl\r\n    )\n```"
        aigc_watermark:
          type: boolean
          description: 是否在生成的视频中添加水印，默认为 `false`
      example:
        prompt: A little girl grow up.
        first_frame_image: >-
          https://filecdn.minimax.chat/public/fe9d04da-f60e-444d-a2e0-18ae743add33.jpeg
        last_frame_image: >-
          https://filecdn.minimax.chat/public/97b7cd08-764e-4b8b-a7bf-87a0bd898575.jpeg
        model: MiniMax-Hailuo-02
        duration: 6
        resolution: 1080P
    VideoGenerationResp:
      type: object
      properties:
        task_id:
          type: string
          description: 视频生成任务的 ID，用于后续查询任务状态
        base_resp:
          $ref: "#/components/schemas/BaseResp"
      example:
        task_id: "106916112212032"
        base_resp:
          status_code: 0
          status_msg: success
    BaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 API-Key 是否填写正确
            - 1008：账号余额不足
            - 1026：视频描述涉及敏感内容，请调整
            - 2013：传入参数异常，请检查入参是否按要求填写
            - 2049：无效的api key，请检查api key

            更多内容可查看[错误码列表](/api-reference/errorcode)
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
````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://platform.minimaxi.com/docs/llms.txt
