# Kling AI API - 公共信息

## 调用域名

```
https://api-beijing.klingai.com
```

## 接口鉴权

### Step-1：获取 AccessKey + SecretKey

从 Kling AI 开发者平台获取您的 AccessKey 和 SecretKey。

### Step-2：生成 API Token

您每次请求API的时候，需要按照固定加密方法生成API Token。

**加密方法**：遵循JWT（Json Web Token, RFC 7519）标准

JWT由三个部分组成：Header、Payload、Signature

#### Python 示例

```python
import time
import jwt

ak = "" # 填写access key
sk = "" # 填写secret key

def encode_jwt_token(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800, # 有效时间，此处示例代表当前时间+1800s(30min)
        "nbf": int(time.time()) - 5 # 开始生效的时间，此处示例代表当前时间-5秒
    }
    token = jwt.encode(payload, sk, headers=headers)
    return token

api_token = encode_jwt_token(ak, sk)
print(api_token) # 打印生成的API_TOKEN
```

### Step-3：组装 Authorization Header

用第二步生成的API Token组装成Authorization，填写到 Request Header 里。

**组装方式**：`Authorization = "Bearer XXX"`

其中 XXX 填写第二步生成的API Token（注意 Bearer 跟 XXX 之间有空格）

## 错误码

| HTTP状态码 | 业务码 | 业务码定义 | 业务码解释 | 建议解决方案 |
|----------|------|---------|----------|------------|
| 200 | 0 | 请求成功 | - | - |
| 401 | 1000 | 身份验证失败 | 身份验证失败 | 检查Authorization是否正确 |
| 401 | 1001 | 身份验证失败 | Authorization为空 | 在RequestHeader中填写正确的Authorization |
| 401 | 1002 | 身份验证失败 | Authorization值非法 | 在RequestHeader中填写正确的Authorization |
| 401 | 1003 | 身份验证失败 | Authorization未到有效时间 | 检查token的开始生效时间，等待生效或重新签发 |
| 401 | 1004 | 身份验证失败 | Authorization已失效 | 检查token的有效期，重新签发 |
| 429 | 1100 | 账户异常 | 账户异常 | 检查账户配置信息 |
| 429 | 1101 | 账户异常 | 账户欠费 (后付费场景) | 进行账户充值，确保余额充足 |
| 429 | 1102 | 账户异常 | 资源包已用完/已过期（预付费场景）| 购买额外的资源包，或开通后付费服务（如有）|
| 403 | 1103 | 账户异常 | 请求的资源无权限，如接口/模型 | 检查账户权限 |
| 400 | 1200 | 请求参数非法 | 请求参数非法 | 检查请求参数是否正确 |
| 400 | 1201 | 请求参数非法 | 参数非法，如key写错或value非法 | 参考返回体中message字段的具体信息，修改请求参数 |
| 404 | 1202 | 请求参数非法 | 请求的method无效 | 查看接口文档，使用正确的requestmethod |
| 404 | 1203 | 请求参数非法 | 请求的资源不存在，如模型 | 参考返回体中message字段的具体信息，修改请求参数 |
| 400 | 1300 | 触发策略 | 触发平台策略 | 检查是否触发平台策略 |
| 400 | 1301 | 触发策略 | 触发平台的内容安全策略 | 检查输入内容，修改后重新发起请求 |
| 429 | 1302 | 触发策略 | API请求过快，超过平台速率限制 | 降低请求频率、稍后重试，或联系客服增加限额 |
| 429 | 1303 | 触发策略 | 并发或QPS超出预付费资源包限制 | 降低请求频率、稍后重试，或联系客服增加限额 |
| 429 | 1304 | 触发策略 | 触发平台的IP白名单策略 | 联系客服 |
| 500 | 5000 | 内部错误 | 服务器内部错误 | 稍后重试，或联系客服 |
| 503 | 5001 | 内部错误 | 服务器暂时不可用，通常是在维护 | 稍后重试，或联系客服 |
| 504 | 5002 | 内部错误 | 服务器内部超时，通常是发生积压 | 稍后重试，或联系客服 |
