
# 视频下载

> 通过本接口进行生成视频文件下载。

## OpenAPI

````yaml api-reference/video/generation/api/openapi.json get /v1/files/retrieve
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
  /v1/files/retrieve:
    get:
      tags:
        - Files
      summary: Retrieve File
      operationId: retrieveFile
      parameters:
        - name: file_id
          in: query
          required: true
          description: |-
            文件的唯一标识符
            支持视频任务状态查询接口获得的 `file_id`
          schema:
            type: integer
            format: int64
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RetrieveFileResp'
components:
  schemas:
    RetrieveFileResp:
      type: object
      properties:
        file:
          $ref: '#/components/schemas/FileObject'
        base_resp:
          $ref: '#/components/schemas/RetrieveFileBaseResp'
      example:
        file:
          file_id: ${file_id}
          bytes: 5896337
          created_at: 1700469398
          filename: output_aigc.mp4
          purpose: video_generation
          download_url: www.downloadurl.com
        base_resp:
          status_code: 0
          status_msg: success
    FileObject:
      type: object
      properties:
        file_id:
          type: integer
          format: int64
          description: 文件的唯一标识符
        bytes:
          type: integer
          format: int64
          description: 文件大小，以字节为单位
        created_at:
          type: integer
          format: int64
          description: 创建文件时的 Unix 时间戳，以秒为单位
        filename:
          type: string
          description: 文件的名称
        purpose:
          type: string
          description: 文件的使用目的
        download_url:
          type: string
          format: url
          description: 文件下载的url地址
    RetrieveFileBaseResp:
      type: object
      properties:
        status_code:
          type: integer
          description: |-
            状态码如下：
            - 1000, 未知错误
            - 1001, 超时
            - 1002, 触发RPM限流
            - 1004, 鉴权失败
            - 1008, 余额不足
            - 1013, 服务内部错误
            - 1026, 输入内容错误
            - 1027, 输出内容错误
            - 1039, 触发TPM限流
            - 2013, 输入格式信息不正常

            更多内容可查看[错误码查询列表](/api-reference/errorcode)了解详情
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

