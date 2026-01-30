列出基础模型。

## 调试

<APILink link="https://api.volcengine.com/api-explorer/?action=ListFoundationModels&groupName=%E7%AE%A1%E7%90%86%E5%9F%BA%E7%A1%80%E6%A8%A1%E5%9E%8B&serviceCode=ark&version=2024-01-01"></APILink>

## 请求参数

下表仅列出该接口特有的请求参数和部分公共参数。更多信息请见[公共参数](https://www.volcengine.com/docs/6369/67268)。

```mixin-react
const columns = [
  {
    width: '20%',
    title: '参数',
    dataIndex: 'Name',
    className: 'openapi-doc-parameter-table-name'
  },
  {
    width: 130,
    title: '类型',
    dataIndex: 'DataType',
    className: 'openapi-doc-parameter-table-type'
  },
  {
    width: 90,
    title: '是否必填',
    dataIndex: 'IsRequired',
    className: 'openapi-doc-parameter-table-required'
  },
  {
    width: '20%',
    title: '示例值',
    dataIndex: 'Example',
    className: 'openapi-doc-parameter-table-example'
  },
  {
    title: '描述',
    dataIndex: 'Description',
    className: 'openapi-doc-parameter-table-description'
  },
];

const data = [
  {
    rowKey: '->Action',
    Name: 'Action',
    DataType: 'String',
    IsRequired: '是',
    Example: <RenderMd content={"ListFoundationModels"} />,
    Description: <RenderMd content={"要执行的操作，取值：ListFoundationModels。"} />,
    children: [
    ]
  },
  {
    rowKey: '->Version',
    Name: 'Version',
    DataType: 'String',
    IsRequired: '是',
    Example: <RenderMd content={"2024-01-01"} />,
    Description: <RenderMd content={"API的版本，取值：2024-01-01。"} />,
    children: [
    ]
  },
  {
    rowKey: '->PageNumber',
    Name: 'PageNumber',
    DataType: 'Integer',
    IsRequired: '否',
    Example: <RenderMd content={"1"} />,
    Description: <RenderMd content={"分页查询时的起始页码，从 1 开始，默认为 1。\n"} />,
    children: [
    ]
  },
  {
    rowKey: '->PageSize',
    Name: 'PageSize',
    DataType: 'Integer',
    IsRequired: '否',
    Example: <RenderMd content={"10"} />,
    Description: <RenderMd content={"分页查询时每页显示的记录数，取值： - 最小值：1 - 最大值：100 - 默认值：10\n"} />,
    children: [
    ]
  },
  {
    rowKey: '->Filter',
    Name: 'Filter',
    DataType: 'Object',
    IsRequired: '否',
    Example: <RenderMd content={"\\-"} />,
    Description: <RenderMd content={"待查询基础模型的筛选条件\n"} />,
    children: [
        {
          rowKey: '->Filter->SupportedCustomizationTypes',
          Name: 'SupportedCustomizationTypes',
          DataType: 'Array of String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型支持的精调类型，精准匹配"} />,
          children: [
          ]
        },
        {
          rowKey: '->Filter->Names',
          Name: 'Names',
          DataType: 'Array of String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型名称列表，精准匹配"} />,
          children: [
          ]
        },
        {
          rowKey: '->Filter->Name',
          Name: 'Name',
          DataType: 'String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型名称，模糊匹配"} />,
          children: [
          ]
        },
        {
          rowKey: '->Filter->FoundationModelTag',
          Name: 'FoundationModelTag',
          DataType: 'Object',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型特定标签"} />,
          children: [
            {
              rowKey: '->Filter->FoundationModelTag->Languages',
              Name: 'Languages',
              DataType: 'Array of String',
              IsRequired: '否',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型支持语言列表"} />,
              children: [
              ]
            },
            {
              rowKey: '->Filter->FoundationModelTag->UsedLibraries',
              Name: 'UsedLibraries',
              DataType: 'Array of String',
              IsRequired: '否',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型使用库列表"} />,
              children: [
              ]
            },
            {
              rowKey: '->Filter->FoundationModelTag->TaskTypes',
              Name: 'TaskTypes',
              DataType: 'Array of String',
              IsRequired: '否',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型支持任务类型列表\n    \"TextGeneration\": \"文本生成\",\n    \"VisualQuestionAnswering\": \"图片内容理解\",\n    \"TextToImage\": \"文生图\",\n    \"ImageToImage\": \"图生图\",\n    \"TextToVideo\": \"文生视频\",\n    \"ImageToVideo\": \"图生视频\",\n    \"TextTo3D\": \"文生 3D\",\n    \"ImageTo3D\": \"图生 3D\",\n    \"VoiceClone\": \"声音复刻\",\n    \"TextToSpeech\": \"文本转语音\",\n    \"SpeechToText\": \"语音转文本\",\n    \"SpeechToSpeech\": \"同声传译\",\n    \"TextEmbedding\": \"文本向量化\",\n    \"ImageEmbedding\": \"图像向量化\",\n    \"MultimodalEmbedding\": \"多模态向量化\""} />,
              children: [
              ]
            },
            {
              rowKey: '->Filter->FoundationModelTag->Domains',
              Name: 'Domains',
              DataType: 'Array of String',
              IsRequired: '否',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型支持领域列表\n- LLM: 大语言模型\n- Audio: 语音大模型\n- ComputerVision: 视觉大模型\n- MultiModal: 多模态\n- Embedding: 向量模型\n- VLM: VLM 模型"} />,
              children: [
              ]
            },
          ]
        },
        {
          rowKey: '->Filter->Description',
          Name: 'Description',
          DataType: 'String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型描述，模糊匹配"} />,
          children: [
          ]
        },
        {
          rowKey: '->Filter->Introduction',
          Name: 'Introduction',
          DataType: 'String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型介绍，模糊匹配"} />,
          children: [
          ]
        },
        {
          rowKey: '->Filter->DisplayName',
          Name: 'DisplayName',
          DataType: 'String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型展示名，模糊匹配"} />,
          children: [
          ]
        },
        {
          rowKey: '->Filter->AccessTypes',
          Name: 'AccessTypes',
          DataType: 'Array of String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型访问模式列表，精准匹配"} />,
          children: [
          ]
        },
    ]
  },
  {
    rowKey: '->SortOrder',
    Name: 'SortOrder',
    DataType: 'String',
    IsRequired: '否',
    Example: <RenderMd content={"Desc"} />,
    Description: <RenderMd content={"指定排序顺序。 可指定值:\n- Asc：升序排列\n- Desc：降序排列"} />,
    children: [
    ]
  },
  {
    rowKey: '->SortBy',
    Name: 'SortBy',
    DataType: 'String',
    IsRequired: '否',
    Example: <RenderMd content={"\\-"} />,
    Description: <RenderMd content={"指定排序指标。 可指定值：\n- CreateTime 创建时间\n- UpdateTime 更新时间"} />,
    children: [
    ]
  },
  {
    rowKey: '->TagFilters',
    Name: 'TagFilters',
    DataType: 'Array of Object',
    IsRequired: '否',
    Example: <RenderMd content={"\\-"} />,
    Description: <RenderMd content={"基于绑定的标签的筛选条件"} />,
    children: [
        {
          rowKey: '->TagFilters->Key',
          Name: 'Key',
          DataType: 'String',
          IsRequired: '是',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"标签键"} />,
          children: [
          ]
        },
        {
          rowKey: '->TagFilters->Values',
          Name: 'Values',
          DataType: 'Array of String',
          IsRequired: '否',
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"标签值"} />,
          children: [
          ]
        },
    ]
  },

];

return (<Table
  rowKey="rowKey"
  className="openapi-doc-parameter-table"
  columns={columns}
  data={data}
  border={ { cell: true, wrapper: true } }
  scroll={ { x: "auto" } }
  pagination={false}
/>);
```

## 返回参数

下表仅列出本接口特有的返回参数。更多信息请参见[返回结构](https://www.volcengine.com/docs/6369/80336)。

```mixin-react
const columns = [
  {
    width: '25%',
    title: '参数',
    dataIndex: 'Name',
    className: 'openapi-doc-parameter-table-name',
  },
  {
    width: 130,
    title: '类型',
    dataIndex: 'DataType',
    className: 'openapi-doc-parameter-table-type'
  },
  {
    width: '25%',
    title: '示例值',
    dataIndex: 'Example',
    className: 'openapi-doc-parameter-table-example'
  },
  {
    title: '描述',
    dataIndex: 'Description',
    className: 'openapi-doc-parameter-table-description'
  },
];

const data = [
  {
    rowKey: "->TotalCount",
    Name: "TotalCount",
    DataType: "Integer",
    Example: <RenderMd content={"2"} />,
    Description: <RenderMd content={"总基础模型数"} />,
    children: [
    ]
  },
  {
    rowKey: "->PageNumber",
    Name: "PageNumber",
    DataType: "Integer",
    Example: <RenderMd content={"1"} />,
    Description: <RenderMd content={"分页查询时的起始页码，从 1 开始，默认为 1。\n"} />,
    children: [
    ]
  },
  {
    rowKey: "->PageSize",
    Name: "PageSize",
    DataType: "Integer",
    Example: <RenderMd content={"1"} />,
    Description: <RenderMd content={"分页查询时每页显示的记录数，取值： - 最小值：1 - 最大值：100 - 默认值：10\n"} />,
    children: [
    ]
  },
  {
    rowKey: "->Items",
    Name: "Items",
    DataType: "Array of Object",
    Example: <RenderMd content={"\\-"} />,
    Description: <RenderMd content={"基础模型列表"} />,
    children: [
        {
          rowKey: "->Items->Name",
          Name: "Name",
          DataType: "String",
          Example: <RenderMd content={"test-foundation-model"} />,
          Description: <RenderMd content={"基础模型名称"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->Description",
          Name: "Description",
          DataType: "String",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型描述"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->Introduction",
          Name: "Introduction",
          DataType: "String",
          Example: <RenderMd content={"language models"} />,
          Description: <RenderMd content={"基础模型介绍。 由于返回值尺寸原因，本字段在ListFoundationModels API中不返回"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->VendorName",
          Name: "VendorName",
          DataType: "String",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型提供方名称"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->DisplayName",
          Name: "DisplayName",
          DataType: "String",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型展示名称"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->FeaturedImage",
          Name: "FeaturedImage",
          DataType: "Object",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型显示图片"} />,
          children: [
            {
              rowKey: "->Items->FeaturedImage->ObjectKey",
              Name: "ObjectKey",
              DataType: 'String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"TOS对象路径"} />,
              children: [
              ]
            },
            {
              rowKey: "->Items->FeaturedImage->BucketName",
              Name: "BucketName",
              DataType: 'String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"TOS桶名称\n在创建和选择 TOS 桶时请注意，当前火山方舟只支持 华北2-北京 地域（region: cn-beijing）的存储桶。"} />,
              children: [
              ]
            },
          ]
        },
        {
          rowKey: "->Items->PrimaryVersion",
          Name: "PrimaryVersion",
          DataType: "String",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型主版本"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->FoundationModelTag",
          Name: "FoundationModelTag",
          DataType: "Object",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型特定标签"} />,
          children: [
            {
              rowKey: "->Items->FoundationModelTag->Languages",
              Name: "Languages",
              DataType: 'Array of String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型支持语言列表"} />,
              children: [
              ]
            },
            {
              rowKey: "->Items->FoundationModelTag->UsedLibraries",
              Name: "UsedLibraries",
              DataType: 'Array of String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型使用库列表"} />,
              children: [
              ]
            },
            {
              rowKey: "->Items->FoundationModelTag->TaskTypes",
              Name: "TaskTypes",
              DataType: 'Array of String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型支持任务类型列表\n    \"TextGeneration\": \"文本生成\",\n    \"VisualQuestionAnswering\": \"图片内容理解\",\n    \"TextToImage\": \"文生图\",\n    \"ImageToImage\": \"图生图\",\n    \"TextToVideo\": \"文生视频\",\n    \"ImageToVideo\": \"图生视频\",\n    \"TextTo3D\": \"文生 3D\",\n    \"ImageTo3D\": \"图生 3D\",\n    \"VoiceClone\": \"声音复刻\",\n    \"TextToSpeech\": \"文本转语音\",\n    \"SpeechToText\": \"语音转文本\",\n    \"SpeechToSpeech\": \"同声传译\",\n    \"TextEmbedding\": \"文本向量化\",\n    \"ImageEmbedding\": \"图像向量化\",\n    \"MultimodalEmbedding\": \"多模态向量化\""} />,
              children: [
              ]
            },
            {
              rowKey: "->Items->FoundationModelTag->Domains",
              Name: "Domains",
              DataType: 'Array of String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"基础模型支持领域列表\n- LLM: 大语言模型\n- Audio: 语音大模型\n- ComputerVision: 视觉大模型\n- MultiModal: 多模态\n- Embedding: 向量模型\n- VLM: VLM 模型"} />,
              children: [
              ]
            },
          ]
        },
        {
          rowKey: "->Items->AccessType",
          Name: "AccessType",
          DataType: "String",
          Example: <RenderMd content={"Public"} />,
          Description: <RenderMd content={"基础模型访问模式。 可指定值:\n- Public 公开模型\n- Private 非公开模型"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->Tags",
          Name: "Tags",
          DataType: "Array of Object",
          Example: <RenderMd content={""} />,
          Description: <RenderMd content={"基础模型绑定的标签"} />,
          children: [
            {
              rowKey: "->Items->Tags->Key",
              Name: "Key",
              DataType: 'String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"标签键"} />,
              children: [
              ]
            },
            {
              rowKey: "->Items->Tags->Value",
              Name: "Value",
              DataType: 'String',
              Example: <RenderMd content={""} />,
              Description: <RenderMd content={"标签值"} />,
              children: [
              ]
            },
          ]
        },
        {
          rowKey: "->Items->ProjectName",
          Name: "ProjectName",
          DataType: "String",
          Example: <RenderMd content={"default"} />,
          Description: <RenderMd content={"项目名称"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->CreateTime",
          Name: "CreateTime",
          DataType: "String",
          Example: <RenderMd content={"2006-01-02T15:04:05Z07:00\n"} />,
          Description: <RenderMd content={"基础模型创建时间，RFC3339格式"} />,
          children: [
          ]
        },
        {
          rowKey: "->Items->UpdateTime",
          Name: "UpdateTime",
          DataType: "String",
          Example: <RenderMd content={"2006-01-02T15:04:05Z07:00\n"} />,
          Description: <RenderMd content={"基础模型更新时间，RFC3339格式"} />,
          children: [
          ]
        },
    ]
  },
];

return (<Table
  rowKey="rowKey"
  className="openapi-doc-parameter-table"
  columns={columns}
  data={data}
  border={ { cell: true, wrapper: true } }
  scroll={ { x: "auto" } }
  pagination={false}
/>);
```

## 请求示例

```text
POST /?Action=ListFoundationModels&Version=2024-01-01 HTTP/1.1
Host: open.volcengineapi.com
Content-Type: application/json; charset=UTF-8
X-Date: 20240514T130015Z
X-Content-Sha256: 287e874e******d653b44d21e
Authorization: HMAC-SHA256 Credential=Adfks******wekfwe/20240514/cn-beijing/ark/request, SignedHeaders=host;x-content-sha256;x-date, Signature=47a7d934ff7b37c03938******cd7b8278a40a1057690c401e92246a0e41085f

{
  "PageNumber": 1,
  "PageSize": 10,
  "Filter": {
    "Name": "1yEK",
    "Names": [
      "b4"
    ],
    "FoundationModelTag": {
      "Languages": [
        "Tv0mxXamkC5"
      ],
      "TaskTypes": [
        "hmqgZGGni"
      ],
      "CustomizedTags": [
        "zafcaqOy"
      ],
      "Domains": [
        "RRamYGIqLt"
      ],
      "UsedLibraries": [
        "Rctg97iyG0G"
      ]
    },
    "Introduction": "sdQb3Q",
    "Description": "ncjtG458V89",
    "DisplayName": "NBgVWD3XwHJ",
    "AccessTypes": [
      "b6Qw9wRLBb"
    ]
  },
  "SortOrder": "Desc",
  "SortBy": "\\-",
  "TagFilters": [
    {
      "Key": "DcuMJa",
      "Values": [
        "5M8sMT"
      ]
    }
  ]
}
```

## 返回示例

```json
{
  "ResponseMetadata": {
    "RequestId": "20240514210020173184054004BACCC8",
    "Action": "ListFoundationModels",
    "Version": "2024-01-01",
    "Service": "ark",
    "Region": "cn-beijing"
  },
  "Result": {
    "TotalCount": 2,
    "PageNumber": 1,
    "PageSize": 1,
    "Items": [
      {
        "Name": "test-foundation-model",
        "Description": "wxr",
        "Introduction": "language models",
        "VendorName": "vERtPPat6Xz",
        "DisplayName": "sBEA",
        "FeaturedImage": {
          "ObjectKey": "J3Og",
          "BucketName": "5E"
        },
        "PrimaryVersion": "zYCdJe3n",
        "FoundationModelTag": {
          "Languages": ["XEQL2sR"],
          "TaskTypes": ["ZpMo3"],
          "CustomizedTags": ["80woxH8k3Ly"],
          "Domains": ["0DQGJbb"],
          "UsedLibraries": ["Jijubh2yS"]
        },
        "AccessType": "Public",
        "Tags": [
          {
            "Key": "3",
            "Value": "V"
          }
        ],
        "ProjectName": "default",
        "CreateTime": "2006-01-02T15:04:05Z07:00\n",
        "UpdateTime": "2006-01-02T15:04:05Z07:00\n"
      }
    ]
  }
}
```

## 错误码

您可访问[公共错误码](https://www.volcengine.com/docs/82379/1299023)，获取更多错误码信息。

<style>
.volc-md-viewer .arco-table-th {
	min-width: 100px;
}
.volc-md-viewer .openapi-doc-parameter-table-description{
  min-width: 150px;
}
.volc-md-viewer .openapi-doc-errorcode-table-errorcode {
  min-width: 150px;
}
.volc-md-viewer .openapi-doc-errorcode-table-errormessage {
  min-width: 150px;
}
.volc-md-viewer .openapi-doc-errorcode-table-description{
  min-width: 150px;
}
.volc-md-viewer .openapi-doc-parameter-table .arco-table-tr>.arco-table-td:first-child .arco-table-cell {
  display: flex;
}
.volc-md-viewer .openapi-doc-parameter-table .arco-table-tr>.arco-table-td:nth-child(2) .arco-table-cell {
  word-break: normal;
}
</style>
