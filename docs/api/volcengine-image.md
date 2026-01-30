`POST https://ark.cn-beijing.volces.com/api/v3/images/generations` [运行](https://api.volcengine.com/api-explorer/?action=ImageGenerations&groupName=%E5%9B%BE%E7%89%87%E7%94%9F%E6%88%90API&serviceCode=ark&version=2024-01-01&tab=2#N4IgTgpgzgDg9gOyhA+gMzmAtgQwC4gBcIArmADYgA0IUAlgF4REgBMA0tSAO74TY4wAayJoc5ZDSxwAJhErEZcEgCMccALTIIMyDiwaALBoAMG1gFYTADlbWuMMHCwwCxQPhmgUTTA-l6Ao2MAw-4CLeYB4tkHBgDOJgE2KgF+KgABygGHxgNf6gPSmgN2egCwegHEegCFugLCagCfKgOhKgGbx-oBFRoBjkYCTkZGA34qA2Ur+gKyugI76gOSagOJO-oDU5oCnpoBHphWA+Ib+gBVKI4Cf2oAr1oBOQf5wAMaATHaAy+b+gJKKgP1+gL-xgFRxY4CABoCEVoBTPv6A9maAj7b+gKGxgA3OgHnagNxygJJy-peAuyH+gNyugEbpgFgJgHH4wBjfoBvQOygAY5QAz2tkZoBLfUAQjqAQmtAIoagAIEp6AZXlAHBygC51c7+QAUsUNAPjuD38gHSzQKAOYzADMB52y6xagAlTQA55oBSELR0UA2DaAF7V-IAXU0xgB9FQDuioAvIMA9OaAbz1AM8GI0AHJqAAn1soB-PUAS5GAeASKmz-IAAAPW-kAs8qAEB1-IBA80AL4GMlr+QBc+oBUfUagDwVQA2aiAAL5AA)
本文介绍图片生成模型如 Seedream 4.5 的调用 API ，包括输入输出参数，取值范围，注意事项等信息，供您使用接口时查阅字段含义。
:::warning
Seedream 4.5 模型首周 （2025年12月03日\-12月09日）公测，公测期间每个账号的 IPM 为 50，12月10日开始恢复为 500。

:::
**不同模型支持的图片生成能力简介**

- **doubao\-seedream\-4.5==^new^==** **、doubao\-seedream\-4.0**
  - 生成组图（组图：基于您输入的内容，生成的一组内容关联的图片；需配置 **sequential_image_generation ** 为`auto` **）**
    - 多图生组图，根据您输入的 **++多张参考图片（2\-14）++ ** +++文本提示词++ 生成一组内容关联的图片（输入的参考图数量+最终生成的图片数量≤15张）。
    - 单图生组图，根据您输入的 ++单张参考图片+文本提示词++ 生成一组内容关联的图片（最多生成14张图片）。
    - 文生组图，根据您输入的 ++文本提示词++ 生成一组内容关联的图片（最多生成15张图片）。
  - 生成单图（配置 **sequential_image_generation ** 为`disabled` **）**
    - 多图生图，根据您输入的 **++多张参考图片（2\-14）++ ** +++文本提示词++ 生成单张图片。
    - 单图生图，根据您输入的 ++单张参考图片+文本提示词++ 生成单张图片。
    - 文生图，根据您输入的 ++文本提示词++ 生成单张图片。
- **doubao\-seedream\-3.0\-t2i**
  - 文生图，根据您输入的 ++文本提示词++ 生成单张图片。
- **doubao\-seededit\-** **3.0** **\-i2i**
  - 图生图，根据您输入的 ++单张参考图片+文本提示词++ 生成单张图片。

&nbsp;

```mixin-react
return (<Tabs>
<Tabs.TabPane title="快速入口" key="oOTdY3Sn"><RenderMd content={` [ ](#)[体验中心](https://console.volcengine.com/ark/region:ark+cn-beijing/experience/vision?type=GenImage)       <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_2abecd05ca2779567c6d32f0ddc7874d.png =20x) </span>[模型列表](https://www.volcengine.com/docs/82379/1330310#%E5%9B%BE%E7%89%87%E7%94%9F%E6%88%90%E8%83%BD%E5%8A%9B)       <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_a5fdd3028d35cc512a10bd71b982b6eb.png =20x) </span>[模型计费](https://www.volcengine.com/docs/82379/1544106#%E5%9B%BE%E7%89%87%E7%94%9F%E6%88%90%E6%A8%A1%E5%9E%8B)       <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_afbcf38bdec05c05089d5de5c3fd8fc8.png =20x) </span>[API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey?apikey=%7B%7D)
 <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_57d0bca8e0d122ab1191b40101b5df75.png =20x) </span>[调用教程](https://www.volcengine.com/docs/82379/1548482)       <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_f45b5cd5863d1eed3bc3c81b9af54407.png =20x) </span>[接口文档](https://www.volcengine.com/docs/82379/1666945)       <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_1609c71a747f84df24be1e6421ce58f0.png =20x) </span>[常见问题](https://www.volcengine.com/docs/82379/1359411)       <span>![图片](https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_bef4bc3de3535ee19d0c5d6c37b0ffdd.png =20x) </span>[开通模型](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&OpenTokenDrawer=false)
`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="鉴权说明" key="bCgTrLVs"><RenderMd content={`本接口仅支持 API Key 鉴权，请在 [获取 API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 页面，获取长效 API Key。
`}></RenderMd></Tabs.TabPane></Tabs>);
```

---

<span id="7thx2dVa"></span>

## 请求参数

<span id="BFVUvDi6"></span>

### 请求体

---

**model** `string` %%require%%
本次请求使用模型的 [Model ID](https://www.volcengine.com/docs/82379/1513689) 或[推理接入点](https://www.volcengine.com/docs/82379/1099522) (Endpoint ID)。

---

**prompt ** `string` %%require%%
用于生成图像的提示词，支持中英文。（查看提示词指南：[Seedream 4.0](https://www.volcengine.com/docs/82379/1829186) 、[Seedream 3.0](https://www.volcengine.com/docs/82379/1795150)）
建议不超过300个汉字或600个英文单词。字数过多信息容易分散，模型可能因此忽略细节，只关注重点，造成图片缺失部分元素。

---

**image** `string/array`

> doubao\-seededit\-3.0\-t2i 不支持该参数

输入的图片信息，支持 URL 或 Base64 编码。其中，doubao\-seedream\-4.5、doubao\-seedream\-4.0 支持单图或多图输入（[查看多图融合示例](https://www.volcengine.com/docs/82379/1824121#%E5%A4%9A%E5%9B%BE%E8%9E%8D%E5%90%88%EF%BC%88%E5%A4%9A%E5%9B%BE%E8%BE%93%E5%85%A5%E5%8D%95%E5%9B%BE%E8%BE%93%E5%87%BA%EF%BC%89)），doubao\-seededit\-3.0\-i2i 仅支持单图输入。

- 图片URL：请确保图片URL可被访问。
- Base64编码：请遵循此格式`data:image/<图片格式>;base64,<Base64编码>`。注意 `<图片格式>` 需小写，如 `data:image/png;base64,<base64_image>`。

:::tip

- 传入图片需要满足以下条件：
  - 图片格式：jpeg、png（doubao\-seedream\-4.5、doubao\-seedream\-4.0 模型新增支持 webp、bmp、tiff、gif 格式**==^new^==**）
  - 宽高比（宽/高）范围：
    - [1/16, 16] (适用模型：doubao\-seedream\-4.5、doubao\-seedream\-4.0）
    - [1/3, 3] (适用模型：doubao\-seededit\-3.0\-t2i、doubao\-seededit\-3.0\-i2i）
  - 宽高长度（px） \> 14
  - 大小：不超过 10MB
  - 总像素：不超过 `6000×6000` px
- doubao\-seedream\-4.5、doubao\-seedream\-4.0 最多支持传入 14 张参考图。

## :::

**size ** `string`

```mixin-react
return (<Tabs>
<Tabs.TabPane title="doubao-seedream-4.5" key="BMB6AP1M"><RenderMd content={`指定生成图像的尺寸信息，支持以下两种方式，不可混用。

* 方式 1 | 指定生成图像的分辨率，并在prompt中用自然语言描述图片宽高比、图片形状或图片用途，最终由模型判断生成图片的大小。
   * 可选值：\`2K\`、\`4K\`
* 方式 2 | 指定生成图像的宽高像素值：
   * 默认值：\`2048x2048\`
   * 总像素取值范围：[\`2560x1440=3686400\`, \`4096x4096=16777216\`]
   * 宽高比取值范围：[1/16, 16]

:::tip
采用方式 2 时，需同时满足总像素取值范围和宽高比取值范围。其中，总像素是对宽度和高度的像素乘积限制，而不是对宽度或高度的单独值进行限制。

* **有效示例**：\`3750x1250\`

总像素值 3750x1250=4687500，符合 [3686400, 16777216] 的区间要求；宽高比 3750/1250=3，符合 [1/16, 16] 的区间要求，故该示例值有效。

* **无效示例**：\`1500x1500\`

总像素值 1500x1500=2250000，未达到 3686400 的最低要求；宽高 1500/1500=1，虽符合 [1/16, 16] 的区间要求，但因其未同时满足两项限制，故该示例值无效。
:::
推荐的宽高像素值：

|宽高比 |宽高像素值 |
|---|---|
|1:1 |\`2048x2048\` |
|4:3 |\`2304x1728\` |
|3:4 |\`1728x2304\` |
|16:9 |\`2560x1440\` |
|9:16 |\`1440x2560\` |
|3:2 |\`2496x1664\` |
|2:3 |\`1664x2496\` |
|21:9 |\`3024x1296\` |

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="doubao-seedream-4.0" key="kghENadO"><RenderMd content={`指定生成图像的尺寸信息，支持以下两种方式，不可混用。

* 方式 1 | 指定生成图像的分辨率，并在prompt中用自然语言描述图片宽高比、图片形状或图片用途，最终由模型判断生成图片的大小。
   * 可选值：\`1K\`、\`2K\`、\`4K\`
* 方式 2 | 指定生成图像的宽高像素值：
   * 默认值：\`2048x2048\`
   * 总像素取值范围：[\`1280x720=921600\`, \`4096x4096=16777216\`]
   * 宽高比取值范围：[1/16, 16]

:::tip
采用方式 2 时，需同时满足总像素取值范围和宽高比取值范围。其中，总像素是对宽度和高度的像素乘积限制，而不是对宽度或高度的单独值进行限制。

* **有效示例**：\`1600x600\`

总像素值 1600x600=960000，符合 [921600, 16777216] 的区间要求；宽高比 1600/600=8/3，符合 [1/16, 16] 的区间要求，故该示例值有效。

* **无效示例**：\`800x800\`

总像素值 800x800=640000，未达到 921600 的最低要求；宽高 800/800=1，虽符合 [1/16, 16] 的区间要求，但因其未同时满足两项限制，故该示例值无效。
:::
推荐的宽高像素值：

|宽高比 |宽高像素值 |
|---|---|
|1:1 |\`2048x2048\` |
|4:3 |\`2304x1728\` |
|3:4 |\`1728x2304\` |
|16:9 |\`2560x1440\` |
|9:16 |\`1440x2560\` |
|3:2 |\`2496x1664\` |
|2:3 |\`1664x2496\` |
|21:9 |\`3024x1296\` |

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="doubao-seedream-3.0-t2i" key="MKsftGMr"><RenderMd content={`指定生成图像的宽高像素值。

* 默认值：\`1024x1024\`
* 总像素取值范围： [\`512x512\`, \`2048x2048\`]

推荐的宽高像素值：

|宽高比 |宽高像素值 |
|---|---|
|1:1 |\`1024x1024\` |
|4:3 |\`1152x864\` |
|3:4 |\`864x1152\` |
|16:9 |\`1280x720\` |
|9:16 |\`720x1280\` |
|3:2 |\`1248x832\` |
|2:3 |\`832x1248\` |
|21:9 |\`1512x648\` |

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="doubao-seededit-3.0-i2i" key="dUuqsxPhNL"><RenderMd content={`指定生成图像的宽高像素值。**当前仅支持 adaptive。**

* adaptive。将您的输入图片尺寸与下表中的尺寸进行对比，选择最接近的，作为输出图片的尺寸。具体而言，会按顺序从可选比例中，选取与原图宽高比**差值最小**的**第一个**，作为生成图片的比例。
* 预设的高宽像素


|宽/高 |宽 |高 |
|---|---|---|
|0.33 |512 |1536 |
|0.35 |544 |1536 |
|0.38 |576 |1536 |
|0.4 |608 |1536 |
|0.42 |640 |1536 |
|0.47 |640 |1376 |
|0.51 |672 |1312 |
|0.55 |704 |1280 |
|0.56 |736 |1312 |
|0.6 |768 |1280 |
|0.63 |768 |1216 |
|0.66 |800 |1216 |
|0.67 |832 |1248 |
|0.7 |832 |1184 |
|0.72 |832 |1152 |
|0.75 |864 |1152 |
|0.78 |896 |1152 |
|0.82 |896 |1088 |
|0.85 |928 |1088 |
|0.88 |960 |1088 |
|0.91 |992 |1088 |
|0.94 |1024 |1088 |
|0.97 |1024 |1056 |
|1 |1024 |1024 |
|1.06 |1056 |992 |
|1.1 |1088 |992 |
|1.17 |1120 |960 |
|1.24 |1152 |928 |
|1.29 |1152 |896 |
|1.33 |1152 |864 |
|1.42 |1184 |832 |
|1.46 |1216 |832 |
|1.5 |1248 |832 |
|1.56 |1248 |800 |
|1.62 |1248 |768 |
|1.67 |1280 |768 |
|1.74 |1280 |736 |
|1.82 |1280 |704 |
|1.78 |1312 |736 |
|1.86 |1312 |704 |
|1.95 |1312 |672 |
|2 |1344 |672 |
|2.05 |1376 |672 |
|2.1 |1408 |672 |
|2.2 |1408 |640 |
|2.25 |1440 |640 |
|2.3 |1472 |640 |
|2.35 |1504 |640 |
|2.4 |1536 |640 |
|2.53 |1536 |608 |
|2.67 |1536 |576 |
|2.82 |1536 |544 |
|3 |1536 |512 |

`}></RenderMd></Tabs.TabPane></Tabs>);
```

---

**seed** `integer` `默认值 -1`

> 仅 doubao\-seedream\-3.0\-t2i、doubao\-seededit\-3.0\-i2i 支持该参数

随机数种子，用于控制模型生成内容的随机性。取值范围为 [\-1, 2147483647]。
:::warning

- 相同的请求下，模型收到不同的seed值，如：不指定seed值或令seed取值为\-1（会使用随机数替代）、或手动变更seed值，将生成不同的结果。
- 相同的请求下，模型收到相同的seed值，会生成类似的结果，但不保证完全一致。

## :::

**sequential_image_generation** `string` `默认值 disabled`

> 仅 doubao\-seedream\-4.5、doubao\-seedream\-4.0 支持该参数 | [查看组图输出示例](https://www.volcengine.com/docs/82379/1824121?lang=zh#%E7%BB%84%E5%9B%BE%E8%BE%93%E5%87%BA%EF%BC%88%E5%A4%9A%E5%9B%BE%E8%BE%93%E5%87%BA%EF%BC%89)

控制是否关闭组图功能。
:::tip
组图：基于您输入的内容，生成的一组内容关联的图片。

:::

- `auto`：自动判断模式，模型会根据用户提供的提示词自主判断是否返回组图以及组图包含的图片数量。
- `disabled`：关闭组图功能，模型只会生成一张图。

---

**sequential_image_generation_options ** `object`

> 仅 doubao\-seedream\-4.5、doubao\-seedream\-4.0 支持该参数

组图功能的配置。仅当 **sequential_image_generation ** 为 `auto` 时生效。

属性

---

sequential_image_generation_options.**max_images ** \*\* \*\* `integer` `默认值 15`
指定本次请求，最多可生成的图片数量。

- 取值范围： [1, 15]

:::tip
实际可生成的图片数量，除受到 **max_images ** 影响外 **，** 还受到输入的参考图数量影响。**输入的参考图数量+最终生成的图片数量≤15张**。

:::

---

**stream** `Boolean` `默认值 false`

> 仅 doubao\-seedream\-4.5、doubao\-seedream\-4.0 支持该参数 | [查看流式输出示例](https://www.volcengine.com/docs/82379/1824121#%E6%B5%81%E5%BC%8F%E8%BE%93%E5%87%BA)

控制是否开启流式输出模式。

- `false`：非流式输出模式，等待所有图片全部生成结束后再一次性返回所有信息。
- `true`：流式输出模式，即时返回每张图片输出的结果。在生成单图和组图的场景下，流式输出模式均生效。

---

**guidance_scale ** `Float`

> doubao\-seedream\-3.0\-t2i 默认值 2.5
> doubao\-seededit\-3.0\-i2i 默认值 5.5
> doubao\-seedream\-4.5、doubao\-seedream\-4.0 不支持

模型输出结果与prompt的一致程度，生成图像的自由度，又称为文本权重；值越大，模型自由度越小，与用户输入的提示词相关性越强。
取值范围：[`1`, `10`] 。

---

**response_format** `string` `默认值 url`
指定生成图像的返回格式。
生成的图片为 jpeg 格式，支持以下两种返回方式：

- `url`：返回图片下载链接；**链接在图片生成后24小时内有效，请及时下载图片。**
- `b64_json`：以 Base64 编码字符串的 JSON 格式返回图像数据。

---

**watermark** `Boolean` `默认值 true`
是否在生成的图片中添加水印。

- `false`：不添加水印。
- `true`：在图片右下角添加“AI生成”字样的水印标识。

---

**optimize_prompt_options==^new^==** \*\* \*\* `object`

> 仅 doubao\-seedream\-4.5（当前仅支持 `standard` 模式）、doubao\-seedream\-4.0 支持该参数

提示词优化功能的配置。

属性
optimize_prompt_options.**mode ** `string` `默认值 standard`
设置提示词优化功能使用的模式。

- `standard`：标准模式，生成内容的质量更高，耗时较长。
- `fast`：快速模式，生成内容的耗时更短，质量一般。

---

&nbsp;
<span id="7P96iLnc"></span>

## 响应参数

<span id="Hrya4y9k"></span>

### 流式响应参数

请参见[文档](https://www.volcengine.com/docs/82379/1824137?lang=zh)。
&nbsp;
<span id="1AxnwQZN"></span>

### 非流式响应参数

---

**model** `string`
本次请求使用的模型 ID （`模型名称-版本`）。

---

**created** `integer`
本次请求创建时间的 Unix 时间戳（秒）。

---

**data** `array`
输出图像的信息。
:::tip
doubao\-seedream\-4.5、doubao\-seedream\-4.0 模型生成组图场景下，组图生成过程中某张图生成失败时：

- 若失败原因为审核不通过：仍会继续请求下一个图片生成任务，即不影响同请求内其他图片的生成流程。
- 若失败原因为内部服务异常（500）：不会继续请求下一个图片生成任务。

:::
可能类型
图片信息 `object`
生成成功的图片信息。

属性
data.**url ** `string`
图片的 url 信息，当 **response_format ** 指定为 `url` 时返回。该链接将在生成后 **24 小时内失效**，请务必及时保存图像。

---

data.**b64_json** `string`
图片的 base64 信息，当 **response_format ** 指定为 `b64_json` 时返回。

---

data.**size** `string`

> 仅 doubao\-seedream\-4.5、doubao\-seedream\-4.0 支持该字段。

图像的宽高像素值，格式 `<宽像素>x<高像素>`，如`2048×2048`。

---

错误信息 `object`
某张图片生成失败，错误信息。

属性
data.**error** `object`
错误信息结构体。

属性

---

data.error.**code**
某张图片生成错误的错误码，请参见[错误码](https://www.volcengine.com/docs/82379/1299023)。

---

data.error.**message**
某张图片生成错误的提示信息。

---

**usage** `object`
本次请求的用量信息。

属性

---

usage.**generated_images ** `integer`
模型成功生成的图片张数，不包含生成失败的图片。
仅对成功生成图片按张数进行计费。

---

usage.**output_tokens** `integer`
模型生成的图片花费的 token 数量。
计算逻辑为：计算 `sum(图片长*图片宽)/256` ，然后取整。

---

usage.**total_tokens** `integer`
本次请求消耗的总 token 数量。
当前不计算输入 token，故与 **output_tokens** 值一致。

**error** `object`
本次请求，如发生错误，对应的错误信息。

属性

---

error.**code** `string`
请参见[错误码](https://www.volcengine.com/docs/82379/1299023)。

---

error.**message** `string`
错误提示信息

&nbsp;
