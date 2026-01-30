所有接口请求中都必须携带公共参数，为了避免重复说明，产品的API文档中可能不再重复描述这部分参数，请您在请求API时携带这部分参数，否则请求将无法通过合法性验证。

## 公共参数如下表

### 1\. Action与Version

:::tip
Action和Version必须放在query当中
:::
| 名称 | 类型 | 是否必填 | 参数格式 | 描述 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| Action | String | 是 | \[a-zA-Z\]+ | 接口名称。实际调用时请参考您使用的产品的API文档取值。 | CreateUser |
| Version | String | 是 | YYYY-MM-DD | 接口的版本。 实际调用时请参考您使用的产品的API文档取值。| 2018-01-01 |
| X-Expires | Int | 否 | 整数 | 签名的有效时间，单位为秒，不填时默认值为900。 | 900 |

### 2\. 签名参数

:::tip
签名参数可以在query中，也可以在header中。
:::

#### （1）在Header中的场景

| 名称             | 类型   | 是否必填 | 描述                                                                                                                                                                                                         | 示例值                                                                                                                                                                                                                                                                                                                    |
| ---------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| X-Date           | String | 是       | 使用UTC时间，精确到秒，使用遵循ISO 8601标准的格式：`YYYYMMDD'T'HHMMSS'Z'`                                                                                                                                    | `20201103T104027Z`                                                                                                                                                                                                                                                                                                        |
| Authorization    | String | 是       | `HMAC-SHA256 Credential={AccessKeyId}/{ShortDate}/{Region}/{Service}/request, SignedHeaders={SignedHeaders}, Signature={Signature}` 。如何构建，请参考[签名方法](https://www.volcengine.com/docs/6369/67269) | `HMAC-SHA256 Credential=AKLTMjI2ODVlYzI3ZGY1NGU4ZjhjYWRjMTlmNTM5OTZkYzE/20201230/cn-north-1/iam/request, SignedHeaders=content-type;host;x-content-sha256;x-date, Signature=28eeabbbd726b87002e0fe58ad8c1c768e619b06e2646f35b6ad7ed029a6d8a7`                                                                             |
| X-Security-Token | String | 否       | 指安全令牌服务（Security Token Service，STS） 颁发的临时安全凭证中的SessionToken，使用长期密钥时无需填写该参数。                                                                                             | `nCitKRW94N1M5aTcwQ0tTY2dpRlM0bHczaVlaekpHdnZUd253QkI2OWxQSE9N.Cj8KK09aVXA4TEstYVg5RkE3dHdqTVhNVk8wRnFjdGI3WF9mQ0RQZ3JwV3d3eTgSEFbw1JQe0EEKsrdI3CLVHosQsMXHqQYYwOHHqQYgoJaAASgBMKCWgAE6B0V4YW1wbGVCA2lhbVIMU2Vzc2lvbiBOYW1lWAFgAQ.TEMEegRPn47UwXZqD742jSTU2tzCPUWaTSsQw7CuSXGa1PlhtQfjXFbPodBHhKTdMCF8_K10OhBF6FXy4eoPQw` |

Authorization中的信息含义：
| 名称 | 类型 | 备注 | 示例值 |
| --- | --- | --- | --- |
| AccessKeyId | String | 请求的Access Key ID。 | `AKLTMjI2ODVlYzI3ZGY1NGU4ZjhjYWRjMTlmNTM5OTZkYzE` |
| ShortDate | String | 请求的短时间，使用UTC时间，精确到日。请使用格式：`YYYYMMDD` | `20180201` |
| Region | String | 请求的地域，例如：`cn-beijing` 。当您使用的产品按Region提供服务时，该参数值请填写您实际要访问的Region；当您使用非Region服务类产品时，您可以填写任一region，例如`cn-beijing`。| `cn-beijing` |
| Service | String | 请求的服务名，请参考您使用的产品的API文档获取Service值，例如访问控制服务名为`iam` | `iam` |
| SignedHeaders | String | 参与签名的Header，多个Header间用分号分隔，目的是指明哪些header参与签名计算，从而忽略请求被proxy添加的额外header，其中host、x-date如果存在header中则必选参与。 | `content-type;host;x-content-sha256;x-date` |
| Signature | String | 计算完毕的签名。详细说明请参考[签名方法](https://www.volcengine.com/docs/6369/67269)| `28eeabbbd726b87002e0fe58ad8c1c768e619b06e2646f35b6ad7ed029a6d8a7` |

#### （2）在Query中的场景

| 名称            | 类型   | 是否必填 | 描述                                                                                                                                                          | 示例值                                                                            |
| --------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| X-Date          | String | 是       | 使用UTC时间，精确到秒                                                                                                                                         | `20201103T104027Z`                                                                |
| X-Algorithm     | String | 是       | 固定值：`HMAC-SHA256`                                                                                                                                         | `HMAC-SHA256`                                                                     |
| X-Credential    | String | 是       | 由`{AccessKeyId}/{ShortDate}/{Region}/{Service}/request`组成。                                                                                                | `AKLTMjI2ODVlYzI3ZGY1NGU4ZjhjYWRjMTlmNTM5OTZkYzE/20201230/cn-north-1/iam/request` |
| X-SignedHeaders | String | 是       | 参与签名的Header，多个Header间用分号分隔，目的是指明哪些header参与签名计算，从而忽略请求被proxy添加的额外header，其中host、x-date如果存在header中则必选参与。 | `content-type;host;x-content-sha256;x-date`                                       |
| X-Signature     | String | 是       | 计算完毕的签名。详细说明请参考[签名方法](https://www.volcengine.com/docs/6369/67269)                                                                          | `28eeabbbd726b87002e0fe58ad8c1c768e619b06e2646f35b6ad7ed029a6d8a7`                |
