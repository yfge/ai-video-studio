# 查询视频生成任务状态

> 使用本接口查询视频生成的任务状态。

## OpenAPI

```yaml api-reference/video/generation/api/openapi.json get /v1/query/video_generation
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
  /v1/query/video_generation:
    get:
      tags:
        - Video
      summary: Query Video Generation Task
      operationId: queryVideoGenerationTask
      parameters:
        - name: task_id
          in: query
          required: true
          description: 待查询的任务 ID。只能查询当前账号创建的任务
          schema:
            type: string
      responses:
        "200":
          description: ""
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/QueryVideoGenerationTaskResp"
components:
  schemas:
    QueryVideoGenerationTaskResp:
      type: object
      properties:
        task_id:
          type: string
          description: 被查询的任务 ID
        status:
          $ref: "#/components/schemas/VideoProcessStatus"
        file_id:
          type: string
          description: 任务成功时返回，用于获取视频文件的文件 ID
        video_width:
          type: integer
          description: 任务成功时返回，生成视频的宽度（像素）.
        video_height:
          type: integer
          description: 任务成功时返回，生成视频的高度（像素）
        base_resp:
          $ref: "#/components/schemas/QueryVideoGenerationTaskBaseResp"
      example:
        task_id: "176843862716480"
        status: Success
        file_id: "176844028768320"
        video_width: 1920
        video_height: 1080
        base_resp:
          status_code: 0
          status_msg: success
    VideoProcessStatus:
      type: string
      enum:
        - Preparing
        - Queueing
        - Processing
        - Success
        - Fail
      description: |-
        任务的当前状态。可能的状态值包括：
        - `Preparing` – 准备中
        - `Queueing` – 队列中
        - `Processing` – 生成中
        - `Success` – 成功
        - `Fail` – 失败
    QueryVideoGenerationTaskBaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码及其分别含义如下：
            - 0：请求成功
            - 1002：触发限流，请稍后再试
            - 1004：账号鉴权失败，请检查 api key是否填写正确
            - 1026：输入内容涉及敏感内容
            - 1027：生成视频涉及敏感内容

            更多内容可查看[错误码查询列表](/api-reference/errorcode)了解详情
        status_msg:
          type: string
          description: 状态信息，成功时为 `success`.
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
