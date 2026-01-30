Seedance 模型具备出色的语义理解能力，可根据用户输入的文本、图片等内容，快速生成优质的视频片段。通过这篇教程，您可学习到如何调用 <a href="https://www.volcengine.com/docs/82379/1520758">Video Generation API</a> 生成视频。
<span id="2c6a9e64"></span>

# 集成说明（ai-video-studio）

- 分镜视频生成默认走 `doubao-seedance-1-0-pro-250528`，支持首帧/首尾帧（`role: first_frame/last_frame`）。
- 后端调用会自动打开 `return_last_frame=true`，回填 `video_url/thumbnail_url/last_frame_url`。
- 生成的 视频/缩略图/尾帧 会自动上传到 OSS（前缀 `ai-generated/videos`、`ai-generated/thumbnails`、`ai-generated/video-last-frames`）。

# 快速开始

视频生成API为异步接口。本示例代码完整演示了视频生成任务的4项操作，包括：

- 创建一个视频生成任务
- 查询视频生成任务的详细状态与结果
- 查询并列出符合特定条件（如状态、模型）的任务列表
- 删除或取消视频生成任务

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Curl" key="WQYVFjFQVA"><RenderMd content={`创建视频生成任务
\`\`\`Bash
curl https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $ARK_API_KEY" \\
  -d '{
    "model": "doubao-seedance-1-0-pro-250528",
    "content": [
        {
            "type": "text",
            "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
            }
        }
    ]
}'
\`\`\`

查询视频生成任务
\`\`\`Bash
//请将 cgt-2025**** 替换为“创建视频生成任务”时获取的视频生成任务 ID。
curl https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/cgt-2025**** \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $ARK_API_KEY"
\`\`\`

查询视频生成任务列表
\`\`\`Bash
curl https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks?page_size=2&filter.status=succeeded& \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $ARK_API_KEY"
\`\`\`

取消或删除视频生成任务
\`\`\`Bash
//请将 cgt-2025**** 替换为“创建视频生成任务”时获取的视频生成任务 ID。
curl https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/cgt-2025**** \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $ARK_API_KEY"
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Python" key="snKgPzrrpq"><RenderMd content={`\`\`\`Python
import os
import time
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Ark client to read your API Key from an environment variable
client = Ark(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.environ.get("ARK_API_KEY"),
)

print("----- create request -----")
# Create a video generation task
create_result = client.content_generation.tasks.create(
    model="doubao-seedance-1-0-pro-250528",  # Replace with Model ID
    content=[
        {
            # Combination of text prompt and parameters
            "type": "text",
            "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5"
        },
        },
        {
            # The URL of the first frame image
            "type": "image_url",
            "image_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
            }
        }
    ]
)
print(create_result)


print("----- get request -----")
# Get task details
get_result = client.content_generation.tasks.get(task_id=create_result.id)
print(get_result)


print("----- list request -----")
# List tasks that meet specific criteria
list_result = client.content_generation.tasks.list(
    page_num=1,
    page_size=10,
    status="queued",
)
print(list_result)


print("----- delete request -----")
# Delete a task by its ID
try:
    client.content_generation.tasks.delete(task_id=create_result.id)
    print(create_result.id)
except Exception as e:
    print(f"failed to delete task: {e}")
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="vgytlQUyz1"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import com.volcengine.ark.runtime.model.content.generation.CreateContentGenerationTaskRequest.Content;
import com.volcengine.ark.runtime.model.content.generation.*;
import com.volcengine.ark.runtime.runtime.service.ArkService;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class ContentGenerationTaskExample {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder()
           .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation
           .dispatcher(dispatcher)
           .connectionPool(connectionPool)
           .apiKey(apiKey)
           .build();

    public static void main(String[] args) {
        String model = "doubao-seedance-1-0-pro-250528"; // Replace with Model ID

        System.out.println("----- create request -----");
        List<Content> contents = new ArrayList<>();

        // Combination of text prompt and parameters
        contents.add(Content.builder()
                .type("text")
                .text("女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5")
                .build());
        // The URL of the first frame image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png")
                        .build())
                .build());

         // Create a video generation task
        CreateContentGenerationTaskRequest createRequest = CreateContentGenerationTaskRequest.builder()
                .model(model)
                .content(contents)
                .build();
        CreateContentGenerationTaskResult createResult = service.createContentGenerationTask(createRequest);
        System.out.println(createResult);

        System.out.println("----- GET Task Request -----");

        // Get the details of the task
        String taskId = createResult.getId();
        GetContentGenerationTaskRequest getRequest = GetContentGenerationTaskRequest.builder()
                .taskId(taskId)
                .build();

        GetContentGenerationTaskResponse getResult = service.getContentGenerationTask(getRequest);
        System.out.println(getResult);

        System.out.println("----- LIST Task Request -----");

        // List tasks that meet specific criteria
        ListContentGenerationTasksRequest listRequest = ListContentGenerationTasksRequest.builder()
                .pageNum(1)
                .pageSize(10)
                .status(TaskStatus.RUNNING)
                .addTaskId(createResult.getId())
                .model(model)
                .build();

        ListContentGenerationTasksResponse listResponse = service.listContentGenerationTasks(listRequest);
        System.out.println(listResponse);

        System.out.println("----- DELETE Task Request -----");

        // Delete a task by its ID
        DeleteContentGenerationTaskRequest deleteRequest = DeleteContentGenerationTaskRequest.builder()
                .taskId(getResult.getId())
                .build();

        try {
            DeleteContentGenerationTaskResponse deleteResult = service.deleteContentGenerationTask(deleteRequest);
            System.out.println(deleteResult);
        } catch (Exception e) {
            System.out.println(e.getMessage());
        }

        service.shutdownExecutor();
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="sD3wOoUV8R"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"

    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    client := arkruntime.NewClientWithApiKey(
        // Get your API Key from the environment variable. This is the default mode and you can modify it as required
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    ctx := context.Background()

    modelEp := "doubao-seedance-1-0-pro-250528" // Replace with Model ID

    // Generate a task
    fmt.Println("----- create request -----")
    createReq := model.CreateContentGenerationTaskRequest{
        Model: modelEp,
        Content: []*model.CreateContentGenerationContentItem{
            {
                // Combination of text prompt and parameters
                Type: model.ContentGenerationContentItemTypeText,
                Text: volcengine.String("女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5"),
            },
            {
                // The URL of the first frame image
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png",
                },
            },
        },
    }
    createResp, err := client.CreateContentGenerationTask(ctx, createReq)
    if err != nil {
        fmt.Printf("create content generation error: %v", err)
        return
    }
    fmt.Printf("Task Created with ID: %s", createResponse.ID)

    fmt.Println("----- get content generation task -----")
    // Get the details of the task
    taskID := createResponse.ID

    getRequest := model.GetContentGenerationTaskRequest{ID: taskID}

    getResponse, err := client.GetContentGenerationTask(ctx, getRequest)
    if err != nil {
        fmt.Printf("get content generation task error: %v", err)
        return
    }

    fmt.Printf("Task ID: %s", getResponse.ID)
    fmt.Printf("Model: %s", getResponse.Model)
    fmt.Printf("Status: %s", getResponse.Status)
    fmt.Printf("Video URL: %s", getResponse.Content.VideoURL)
    fmt.Printf("Completion Tokens: %d", getResponse.Usage.CompletionTokens)
    fmt.Printf("Created At: %d", getResponse.CreatedAt)
    fmt.Printf("Updated At: %d", getResponse.UpdatedAt)
    if getResponse.Error != nil {
        fmt.Printf("Error Code: %s", getResponse.Error.Code)
        fmt.Printf("Error Message: %s", getResponse.Error.Message)
    }

    fmt.Println("----- list content generation task -----")

    // List tasks that meet specific criteria
    listRequest := model.ListContentGenerationTasksRequest{
        PageNum:  volcengine.Int(1),
        PageSize: volcengine.Int(10),
        Filter: &model.ListContentGenerationTasksFilter{
            Status: volcengine.String(model.StatusSucceeded),
        },
    }

    listResponse, err := client.ListContentGenerationTasks(ctx, listRequest)
    if err != nil {
        fmt.Printf("failed to list content generation tasks: %v", err)
    }

    fmt.Printf("ListContentGenerationTasks returned %v results", listResponse.Total)

    fmt.Println("----- delete content generation task -----")

    // Delete a task by its ID
    deleteRequest := model.DeleteContentGenerationTaskRequest{ID: taskID}

    err = client.DeleteContentGenerationTask(ctx, deleteRequest)
    if err != nil {
        fmt.Printf("delete content generation task error: %v", err)
    } else {
        fmt.Println("successfully deleted task id: ", taskID)
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
```

<span id="e7b4c498"></span>

# 支持模型

| | | | | | | | | | \
|**模型名称** |\
|<div style="width:150px"></div> |**版本** |\
| |<div style="width:120px"></div> |**模型 ID（Model ID）** |\
| | |<div style="width:150px"></div> |**模型能力** |\
| | | |<div style="width:130px"></div> |**输出视频格式** |\
| | | | |<div style="width:150px"></div> | **限流** |\
| | | | | |> default（在线推理） |\
| | | | | |> flex（离线推理） |\
| | | | | | |\
| | | | | |<div style="width:170px"></div> |**并发数限制** |\
| | | | | | |<div style="width:100px"></div> |**免费额度** |\
| | | | | | | |（token） |\
| | | | | | | |<div style="width:100px"></div> |**定价** |\
| | | | | | | | |(元/百万 token) |\
| | | | | | | | |<div style="width:100px"></div> |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | \
|[doubao-seedance-1.0-pro](/docs/82379/1587798) |250528`强烈推荐` |doubao-seedance-1-0-pro-250528 |图生视频-首尾帧 |\
| | | |图生视频-首帧 |\
| | | |文生视频 |分辨率： |\
| | | | |480p， |\
| | | | |720p， |\
| | | | |1080p`参考图场景不支持` |\
| | | | |帧率：24 fps |\
| | | | |时长：2~12 秒 |\
| | | | |视频格式：mp4 |\
| | | | | |default：RPM 600 |\
| | | | | |flex：TPD 5000亿 |default：10 |\
| | | | | | |flex：无 |default：200万 |\
| | | | | | | |flex：无 |[视频生成模型](/docs/82379/1544106#02affcb8) |
| | | | |^^| | | | | \
|[doubao-seedance-1.0-pro-fast](/docs/82379/1901652) |251015`强烈推荐` |doubao-seedance-1-0-pro-fast-251015 |图生视频-首帧 |\
| | | |文生视频 | |default：RPM 600 |\
| | | | | |flex：TPD 5000亿 |default：10 |\
| | | | | | |flex：无 |default：200万 |\
| | | | | | | |flex：无 |[视频生成模型](/docs/82379/1544106#02affcb8) |
| | | | |^^| | | | | \
|[doubao-seedance-1.0-lite](/docs/82379/1553576) |250428 |doubao-seedance-1-0-lite-t2v-250428 |文生视频 | |default：RPM 300 |\
| | | | | |flex：TPD 2500亿 |default：5 |\
| | | | | | |flex：无 |default：200万 |\
| | | | | | | |flex：无 |[视频生成模型](/docs/82379/1544106#02affcb8) |
|^^| | | |^^| | | | | \
| |250428 |doubao-seedance-1-0-lite-i2v-250428 |图生视频-参考图 |\
| | | |图生视频-首尾帧 |\
| | | |图生视频-首帧 | |default：RPM 300 |\
| | | | | |flex：TPD 2500亿 |default：5 |\
| | | | | | |flex：无 |default：200万 |\
| | | | | | | |flex：无 |[视频生成模型](/docs/82379/1544106#02affcb8) |

<span id="f5531933"></span>

# 前提条件

- [获取 API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 。
- [开通模型服务](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&OpenTokenDrawer=false)。
- 在[模型列表](/docs/82379/1330310)获取所需 Model ID 。
  - 通过 Endpoint ID 调用模型服务请参考[获取 Endpoint ID（创建自定义推理接入点）](/docs/82379/1099522)。

<span id="754e68e3"></span>

# 基础使用

<span id="42750622"></span>

## 文生视频

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Python" key="BL8EAEHNaO"><RenderMd content={`\`\`\`Python
import os
import time
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Ark client to read your API Key from an environment variable
client = Ark(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.environ.get("ARK_API_KEY"),
)

if __name__ == "__main__":
    print("----- create request -----")
    create_result = client.content_generation.tasks.create(
        model="doubao-seedance-1-0-pro-250528", # Replace with Model ID
        content=[
            {
                # Combination of text prompt and parameters
                "type": "text",
                "text": "一位身穿绿色亮片礼服的女性站在粉红色背景前，周围飘落着五彩斑斓的彩纸 --wm true --dur 5"
            }
        ]
    )
    print(create_result)

    # Polling query section
    print("----- polling task status -----")
    task_id = create_result.id
    while True:
        get_result = client.content_generation.tasks.get(task_id=task_id)
        status = get_result.status
        if status == "succeeded":
            print("----- task succeeded -----")
            print(get_result)
            break
        elif status == "failed":
            print("----- task failed -----")
            print(f"Error: {get_result.error}")
            break
        else:
            print(f"Current status: {status}, Retrying after 1 seconds...")
            time.sleep(1)
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="tzn8oXNsY7"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import com.volcengine.ark.runtime.model.content.generation.CreateContentGenerationTaskRequest.Content;
import com.volcengine.ark.runtime.model.content.generation.*;
import com.volcengine.ark.runtime.runtime.service.ArkService;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class ContentGenerationTaskExample {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder()
           .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation
           .dispatcher(dispatcher)
           .connectionPool(connectionPool)
           .apiKey(apiKey)
           .build();

    public static void main(String[] args) {
        String model = "doubao-seedance-1-0-pro-250528"; // Replace with Model ID

        System.out.println("----- create request -----");
        List<Content> contents = new ArrayList<>();

        // Combination of text prompt and parameters
        contents.add(Content.builder()
                .type("text")
                .text("一位身穿绿色亮片礼服的女性站在粉红色背景前，周围飘落着五彩斑斓的彩纸 --wm true --dur 5")
                .build());

        // Create a video generation task
        CreateContentGenerationTaskRequest createRequest = CreateContentGenerationTaskRequest.builder()
                .model(model)
                .content(contents)
                .build();

        CreateContentGenerationTaskResult createResult = service.createContentGenerationTask(createRequest);
        System.out.println(createResult);

        // Get the details of the task
        String taskId = createResult.getId();
        GetContentGenerationTaskRequest getRequest = GetContentGenerationTaskRequest.builder()
                .taskId(taskId)
                .build();

        // Polling query section
        System.out.println("----- polling task status -----");
        while (true) {
            try {
                GetContentGenerationTaskResponse getResponse = service.getContentGenerationTask(getRequest);
                String status = getResponse.getStatus();
                if ("succeeded".equalsIgnoreCase(status)) {
                    System.out.println("----- task succeeded -----");
                    System.out.println(getResponse);
                    break;
                } else if ("failed".equalsIgnoreCase(status)) {
                    System.out.println("----- task failed -----");
                    System.out.println("Error: " + getResponse.getStatus());
                    break;
                } else {
                    System.out.printf("Current status: %s, Retrying in 1 seconds...", status);
                    TimeUnit.SECONDS.sleep(1);
                }
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                System.err.println("Polling interrupted");
                break;
            }
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="dQWyeFOKQ1"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    client := arkruntime.NewClientWithApiKey(
        // Get your API Key from the environment variable. This is the default mode and you can modify it as required
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    ctx := context.Background()
    // Replace with Model ID
    modelEp := "doubao-seedance-1-0-pro-250528"

    // Generate a task
    fmt.Println("----- create request -----")
    createReq := model.CreateContentGenerationTaskRequest{
        Model: modelEp,
        Content: []*model.CreateContentGenerationContentItem{
            {
                // Combination of text prompt and parameters
                Type: model.ContentGenerationContentItemTypeText,
                Text: volcengine.String("一位身穿绿色亮片礼服的女性站在粉红色背景前，周围飘落着五彩斑斓的彩纸 --wm true --dur 5"),
            },
        },
    }
    createResp, err := client.CreateContentGenerationTask(ctx, createReq)
    if err != nil {
        fmt.Printf("create content generation error: %v", err)
        return
    }
    taskID := createResp.ID
    fmt.Printf("Task Created with ID: %s", taskID)

    // Polling query section
    fmt.Println("----- polling task status -----")
    for {
        getReq := model.GetContentGenerationTaskRequest{ID: taskID}
        getResp, err := client.GetContentGenerationTask(ctx, getReq)
        if err != nil {
            fmt.Printf("get content generation task error: %v", err)
            return
        }

        status := getResp.Status
        if status == "succeeded" {
            fmt.Println("----- task succeeded -----")
            fmt.Printf("Task ID: %s \\n", getResp.ID)
            fmt.Printf("Model: %s \\n", getResp.Model)
            fmt.Printf("Video URL: %s \\n", getResp.Content.VideoURL)
            fmt.Printf("Completion Tokens: %d \\n", getResp.Usage.CompletionTokens)
            fmt.Printf("Created At: %d, Updated At: %d", getResp.CreatedAt, getResp.UpdatedAt)
            return
        } else if status == "failed" {
            fmt.Println("----- task failed -----")
            if getResp.Error != nil {
                fmt.Printf("Error Code: %s, Message: %s", getResp.Error.Code, getResp.Error.Message)
            }
            return
        } else {
            fmt.Printf("Current status: %s, Retrying in 1 seconds... \\n", status)
            time.Sleep(1 * time.Second)
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
```

<span id="979b2d28"></span>

## 图生视频-基于首帧

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Python" key="edp0ZvDZps"><RenderMd content={`\`\`\`Python
import os
import time
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Ark client to read your API Key from an environment variable
client = Ark(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.environ.get("ARK_API_KEY"),
)

if __name__ == "__main__":
    print("----- create request -----")
    create_result = client.content_generation.tasks.create(
        model="doubao-seedance-1-0-pro-fast-251015", # Replace with Model ID
        content=[
            {
                # Combination of text prompt and parameters
                "type": "text",
                "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5"
            },
            {
                # The URL of the first frame image
                "type": "image_url",
                "image_url": {
                    "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
                }
            }
        ]
    )
    print(create_result)

    # Polling query section
    print("----- polling task status -----")
    task_id = create_result.id
    while True:
        get_result = client.content_generation.tasks.get(task_id=task_id)
        status = get_result.status
        if status == "succeeded":
            print("----- task succeeded -----")
            print(get_result)
            break
        elif status == "failed":
            print("----- task failed -----")
            print(f"Error: {get_result.error}")
            break
        else:
            print(f"Current status: {status}, Retrying after 1 seconds...")
            time.sleep(1)
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="vX4TbXleOZ"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import com.volcengine.ark.runtime.model.content.generation.CreateContentGenerationTaskRequest.Content;
import com.volcengine.ark.runtime.model.content.generation.*;
import com.volcengine.ark.runtime.runtime.service.ArkService;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class ContentGenerationTaskExample {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder()
           .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation
           .dispatcher(dispatcher)
           .connectionPool(connectionPool)
           .apiKey(apiKey)
           .build();

    public static void main(String[] args) {
        String model = "doubao-seedance-1-0-pro-fast-251015"; // Replace with Model ID

        System.out.println("----- create request -----");
        List<Content> contents = new ArrayList<>();

        // Combination of text prompt and parameters
        contents.add(Content.builder()
                .type("text")
                .text("女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5")
                .build());
        // The URL of the first frame image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png")
                        .build())
                .build());

        // Create a video generation task
        CreateContentGenerationTaskRequest createRequest = CreateContentGenerationTaskRequest.builder()
                .model(model)
                .content(contents)
                .build();

        CreateContentGenerationTaskResult createResult = service.createContentGenerationTask(createRequest);
        System.out.println(createResult);

        // Get the details of the task
        String taskId = createResult.getId();
        GetContentGenerationTaskRequest getRequest = GetContentGenerationTaskRequest.builder()
                .taskId(taskId)
                .build();

        // Polling query section
        System.out.println("----- polling task status -----");
        while (true) {
            try {
                GetContentGenerationTaskResponse getResponse = service.getContentGenerationTask(getRequest);
                String status = getResponse.getStatus();
                if ("succeeded".equalsIgnoreCase(status)) {
                    System.out.println("----- task succeeded -----");
                    System.out.println(getResponse);
                    break;
                } else if ("failed".equalsIgnoreCase(status)) {
                    System.out.println("----- task failed -----");
                    System.out.println("Error: " + getResponse.getStatus());
                    break;
                } else {
                    System.out.printf("Current status: %s, Retrying in 1 seconds...", status);
                    TimeUnit.SECONDS.sleep(1);
                }
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                System.err.println("Polling interrupted");
                break;
            }
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="Vo3xSviXlt"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    client := arkruntime.NewClientWithApiKey(
        // Get your API Key from the environment variable. This is the default mode and you can modify it as required
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    ctx := context.Background()
    // Replace with Model ID
    modelEp := "doubao-seedance-1-0-pro-fast-251015"

    // Generate a task
    fmt.Println("----- create request -----")
    createReq := model.CreateContentGenerationTaskRequest{
        Model: modelEp,
        Content: []*model.CreateContentGenerationContentItem{
            {
                // Combination of text prompt and parameters
                Type: model.ContentGenerationContentItemTypeText,
                Text: volcengine.String("女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动 --wm true --dur 5"),
            },
            {
                // The URL of the first frame image
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png",
                },
            },
        },
    }
    createResp, err := client.CreateContentGenerationTask(ctx, createReq)
    if err != nil {
        fmt.Printf("create content generation error: %v", err)
        return
    }
    taskID := createResp.ID
    fmt.Printf("Task Created with ID: %s", taskID)

    // Polling query section
    fmt.Println("----- polling task status -----")
    for {
        getReq := model.GetContentGenerationTaskRequest{ID: taskID}
        getResp, err := client.GetContentGenerationTask(ctx, getReq)
        if err != nil {
            fmt.Printf("get content generation task error: %v", err)
            return
        }

        status := getResp.Status
        if status == "succeeded" {
            fmt.Println("----- task succeeded -----")
            fmt.Printf("Task ID: %s \\n", getResp.ID)
            fmt.Printf("Model: %s \\n", getResp.Model)
            fmt.Printf("Video URL: %s \\n", getResp.Content.VideoURL)
            fmt.Printf("Completion Tokens: %d \\n", getResp.Usage.CompletionTokens)
            fmt.Printf("Created At: %d, Updated At: %d", getResp.CreatedAt, getResp.UpdatedAt)
            return
        } else if status == "failed" {
            fmt.Println("----- task failed -----")
            if getResp.Error != nil {
                fmt.Printf("Error Code: %s, Message: %s", getResp.Error.Code, getResp.Error.Message)
            }
            return
        } else {
            fmt.Printf("Current status: %s, Retrying in 1 seconds... \\n", status)
            time.Sleep(1 * time.Second)
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
```

<span id="0d55ca07"></span>

## 图生视频-基于首尾帧

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Python" key="EOlyxb0z0U"><RenderMd content={`\`\`\`Python
import os
import time
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Ark client to read your API Key from an environment variable
client = Ark(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.environ.get("ARK_API_KEY"),


 if __name__ == "__main__":
    print("----- create request -----")
    create_result = client.content_generation.tasks.create(
        model="doubao-seedance-1-0-pro-250528", # Replace with Model ID
        content=[
            {
                # Combination of text prompt and parameters
                "type": "text",
                "text": "360度环绕运镜"
            },
            {
                # The URL of the first frame image
                "type": "image_url",
                "image_url": {
                    "url": " https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_first_frame.jpeg"
                }，
                "role": "first_frame"
            },
            {
                # The URL of the last frame image
                "type": "image_url",
                "image_url": {
                    "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_last_frame.jpeg"
                }，
                "role": "last_frame"
            }
        ]
    )
    print(create_result)



    # Polling query section
    print("----- polling task status -----")
    task_id = create_result.id
    while True:
        get_result = client.content_generation.tasks.get(task_id=task_id)
        status = get_result.status
        if status == "succeeded":
            print("----- task succeeded -----")
            print(get_result)
            break
        elif status == "failed":
            print("----- task failed -----")
            print(f"Error: {get_result.error}")
            break
        else:
            print(f"Current status: {status}, Retrying after 1 seconds...")
            time.sleep(1)
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="bZ7fziOF0q"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import com.volcengine.ark.runtime.model.content.generation.CreateContentGenerationTaskRequest.Content;
import com.volcengine.ark.runtime.model.content.generation.*;
import com.volcengine.ark.runtime.runtime.service.ArkService;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class ContentGenerationTaskExample {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder()
           .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation
           .dispatcher(dispatcher)
           .connectionPool(connectionPool)
           .apiKey(apiKey)
           .build();

    public static void main(String[] args) {
        String model = "doubao-seedance-1-0-pro-250528"; // Replace with Model ID

        System.out.println("----- create request -----");
        List<Content> contents = new ArrayList<>();

        // Combination of text prompt and parameters
        contents.add(Content.builder()
                .type("text")
                .text("360度环绕运镜")
                .build());
         // The URL of the first frame image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_first_frame.jpeg")
                        .build())
                .role("first_frame")
                .build());

        // The URL of the last frame image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_last_frame.jpeg")
                        .build())
                .role("last_frame")
                .build());

        // Create a video generation task
        CreateContentGenerationTaskRequest createRequest = CreateContentGenerationTaskRequest.builder()
                .model(model)
                .content(contents)
                .build();

        CreateContentGenerationTaskResult createResult = service.createContentGenerationTask(createRequest);
        System.out.println(createResult);

        // Get the details of the task
        String taskId = createResult.getId();
        GetContentGenerationTaskRequest getRequest = GetContentGenerationTaskRequest.builder()
                .taskId(taskId)
                .build();

        // Polling query section
        System.out.println("----- polling task status -----");
        while (true) {
            try {
                GetContentGenerationTaskResponse getResponse = service.getContentGenerationTask(getRequest);
                String status = getResponse.getStatus();
                if ("succeeded".equalsIgnoreCase(status)) {
                    System.out.println("----- task succeeded -----");
                    System.out.println(getResponse);
                    break;
                } else if ("failed".equalsIgnoreCase(status)) {
                    System.out.println("----- task failed -----");
                    System.out.println("Error: " + getResponse.getStatus());
                    break;
                } else {
                    System.out.printf("Current status: %s, Retrying in 1 seconds...", status);
                    TimeUnit.SECONDS.sleep(1);
                }
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                System.err.println("Polling interrupted");
                break;
            }
        }
    }
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="hWGVoZWRMr"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    client := arkruntime.NewClientWithApiKey(
        // Get your API Key from the environment variable. This is the default mode and you can modify it as required
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    ctx := context.Background()
    // Replace with Model ID
    modelEp := "doubao-seedance-1-0-pro-250528" // Model ID

    // Generate a task
    fmt.Println("----- create request -----")
    createReq := model.CreateContentGenerationTaskRequest{
        Model: modelEp,
        Content: []*model.CreateContentGenerationContentItem{
            {
                // Combination of text prompt and parameters
                Type: model.ContentGenerationContentItemTypeText,
                Text: volcengine.String("360度环绕运镜"),
            },
            {
                // The URL of the first frame image
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_first_frame.jpeg",
                },
                Role: volcengine.String("first_frame"),
            },
            {
                // The URL of the last frame image
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_last_frame.jpeg",
                },
                Role: volcengine.String("last_frame"),
            },
        },
    }
    createResp, err := client.CreateContentGenerationTask(ctx, createReq)
    if err != nil {
        fmt.Printf("create content generation error: %v", err)
        return
    }
    taskID := createResp.ID
    fmt.Printf("Task Created with ID: %s", taskID)

    // Polling query section
    fmt.Println("----- polling task status -----")
    for {
        getReq := model.GetContentGenerationTaskRequest{ID: taskID}
        getResp, err := client.GetContentGenerationTask(ctx, getReq)
        if err != nil {
            fmt.Printf("get content generation task error: %v", err)
            return
        }

        status := getResp.Status
        if status == "succeeded" {
            fmt.Println("----- task succeeded -----")
            fmt.Printf("Task ID: %s \\n", getResp.ID)
            fmt.Printf("Model: %s \\n", getResp.Model)
            fmt.Printf("Video URL: %s \\n", getResp.Content.VideoURL)
            fmt.Printf("Completion Tokens: %d \\n", getResp.Usage.CompletionTokens)
            fmt.Printf("Created At: %d, Updated At: %d", getResp.CreatedAt, getResp.UpdatedAt)
            return
        } else if status == "failed" {
            fmt.Println("----- task failed -----")
            if getResp.Error != nil {
                fmt.Printf("Error Code: %s, Message: %s", getResp.Error.Code, getResp.Error.Message)
            }
            return
        } else {
            fmt.Printf("Current status: %s, Retrying in 1 seconds... \\n", status)
            time.Sleep(1 * time.Second)
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
```

<span id="c5f5f577"></span>

## 图生视频-基于参考图

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Python" key="iNPVTFShUY"><RenderMd content={`\`\`\`Python
import os
import time
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Ark client to read your API Key from an environment variable
client = Ark(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.environ.get("ARK_API_KEY"),
)

if __name__ == "__main__":
    print("----- create request -----")
    try:
        create_result = client.content_generation.tasks.create(
            model="doubao-seedance-1-0-lite-i2v-250428",  # Replace with Model ID
            content=[
                {
                    # Combination of text prompt and parameters
                    "type": "text",
                    "text": "[图1]戴着眼镜穿着蓝色T恤的男生和[图2]的柯基小狗，坐在[图3]的草坪上，视频卡通风格"
                },
                {
                    # The URL of the first reference image
                    # 1-4 reference images need to be provided
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_1.png"
                    },
                    "role": "reference_image"
                },
                {
                    # The URL of the second reference image
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_2.png"
                    },
                    "role": "reference_image"
                },
                {
                    # The URL of the third reference image
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_3.png"
                    },
                    "role": "reference_image"
                }
            ]
        )
        print(create_result)

        # Polling query section
        print("----- polling task status -----")
        task_id = create_result.id
        while True:
            get_result = client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            if status == "succeeded":
                print("----- task succeeded -----")
                print(get_result)
                break
            elif status == "failed":
                print("----- task failed -----")
                print(f"Error: {get_result.error}")
                break
            else:
                print(f"Current status: {status}, Retrying after 1 seconds...")
                time.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="ZwWI65aRs9"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import com.volcengine.ark.runtime.model.content.generation.CreateContentGenerationTaskRequest.Content;
import com.volcengine.ark.runtime.model.content.generation.*;
import com.volcengine.ark.runtime.runtime.service.ArkService;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;


public class ContentGenerationTaskExample {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder()
           .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation
           .dispatcher(dispatcher)
           .connectionPool(connectionPool)
           .apiKey(apiKey)
           .build();

    public static void main(String[] args) {
        String model = "doubao-seedance-1-0-lite-i2v-250428"; // Replace with Model ID

        System.out.println("----- create request -----");
        List<Content> contents = new ArrayList<>();

        // Combination of text prompt and parameters
        contents.add(Content.builder()
                .type("text")
                .text("[图1]戴着眼镜穿着蓝色T恤的男生和[图2]的柯基小狗，坐在[图3]的草坪上，视频卡通风格")
                .build());
        // The URL of the first reference image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_1.png")
                        .build())
                .role("reference_image")
                .build());
        // The URL of the second reference image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_2.png")
                        .build())
                .role("reference_image")
                .build());
        // The URL of the third reference image
        contents.add(Content.builder()
                .type("image_url")
                .imageUrl(CreateContentGenerationTaskRequest.ImageUrl.builder()
                        .url("https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_3.png")
                        .build())
                .role("reference_image")
                .build());

        // Create a video generation task
        CreateContentGenerationTaskRequest createRequest = CreateContentGenerationTaskRequest.builder()
                .model(model)
                .content(contents)
                .build();

        CreateContentGenerationTaskResult createResult = service.createContentGenerationTask(createRequest);
        System.out.println(createResult);

        // Get the details of the task
        String taskId = createResult.getId();
        GetContentGenerationTaskRequest getRequest = GetContentGenerationTaskRequest.builder()
                .taskId(taskId)
                .build();

        // Polling query section
        System.out.println("----- polling task status -----");
        while (true) {
            try {
                GetContentGenerationTaskResponse getResponse = service.getContentGenerationTask(getRequest);
                String status = getResponse.getStatus();
                if ("succeeded".equalsIgnoreCase(status)) {
                    System.out.println("----- task succeeded -----");
                    System.out.println(getResponse);
                    break;
                } else if ("failed".equalsIgnoreCase(status)) {
                    System.out.println("----- task failed -----");
                    System.out.println("Error: " + getResponse.getStatus());
                    break;
                } else {
                    System.out.printf("Current status: %s, Retrying in 1 seconds...", status);
                    TimeUnit.SECONDS.sleep(1);
                }
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                System.err.println("Polling interrupted");
                break;
            }
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="vFyPrz9cGy"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    // Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    // Initialize the Ark client to read your API Key from an environment variable
    client := arkruntime.NewClientWithApiKey(
        // Get your API Key from the environment variable. This is the default mode and you can modify it as required
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    ctx := context.Background()
    // Replace with Model ID
    modelEp := "doubao-seedance-1-0-lite-i2v-250428"

    // Generate a task
    fmt.Println("----- create request -----")
    createReq := model.CreateContentGenerationTaskRequest{
        Model: modelEp,
        Content: []*model.CreateContentGenerationContentItem{
            {
                // Combination of text prompt and parameters
                Type: model.ContentGenerationContentItemTypeText,
                Text: volcengine.String("[图1]戴着眼镜穿着蓝色T恤的男生和[图2]的柯基小狗，坐在[图3]的草坪上，视频卡通风格"),
            },
            {
                // The URL of the first reference image
                // # 1-4 reference images need to be provided
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_1.png",
                },
                Role: volcengine.String("reference_image"),
            },
            {
                // The URL of the second reference image
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_2.png",
                },
                Role: volcengine.String("reference_image"),
            },
            {
                // The URL of the third reference image
                Type: model.ContentGenerationContentItemTypeImage,
                ImageURL: &model.ImageURL{
                    URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_ref_3.png",
                },
                Role: volcengine.String("reference_image"),
            },
        },
    }

    createResp, err := client.CreateContentGenerationTask(ctx, createReq)
    if err != nil {
        fmt.Printf("create content generation error: %v", err)
        return
    }
    taskID := createResp.ID
    fmt.Printf("Task Created with ID: %s", taskID)

    // Polling query section
    fmt.Println("----- polling task status -----")
    for {
        getReq := model.GetContentGenerationTaskRequest{ID: taskID}
        getResp, err := client.GetContentGenerationTask(ctx, getReq)
        if err != nil {
            fmt.Printf("get content generation task error: %v", err)
            return
        }

        status := getResp.Status
        if status == "succeeded" {
            fmt.Println("----- task succeeded -----")
            fmt.Printf("Task ID: %s \\n", getResp.ID)
            fmt.Printf("Model: %s \\n", getResp.Model)
            fmt.Printf("Video URL: %s \\n", getResp.Content.VideoURL)
            fmt.Printf("Completion Tokens: %d \\n", getResp.Usage.CompletionTokens)
            fmt.Printf("Created At: %d, Updated At: %d", getResp.CreatedAt, getResp.UpdatedAt)
            return
        } else if status == "failed" {
            fmt.Println("----- task failed -----")
            if getResp.Error != nil {
                fmt.Printf("Error Code: %s, Message: %s", getResp.Error.Code, getResp.Error.Message)
            }
            return
        } else {
            fmt.Printf("Current status: %s, Retrying in 1 seconds... \\n", status)
            time.Sleep(1 * time.Second)
        }
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
```

<span id="9fe4cce0"></span>

## 设置输出视频格式

通过在文本提示词后追加`--[parameters]`的方式，可控制视频输出的规格，包括宽高比、帧率、分辨率等。

```Shell
// 指定生成视频的宽高比为16:9，时长为 5 秒，帧率为 24 fps，分辨率为720p，包含水印，种子整数为11，不固定摄像头
"content": [
        {
            "type": "text",
            "text": "小猫对着镜头打哈欠。 --rs 720p --rt 16:9 --dur 5 --fps 24 --wm true --seed 11 --cf false"
        }
 ]
```

| | | | | | \
| |doubao-seedance-1-0-pro |\
| |<div style="width:150px"></div> |doubao-seedance-1-0-pro-fast |\
| | |<div style="width:150px"></div> |doubao-seedance-1-0-lite-t2v |\
| | | |<div style="width:150px"></div> |doubao-seedance-1-0-lite-i2v |\
| | | | |<div style="width:150px"></div> |
|---|---|---|---|---|
| | || || \
|resolution |\
|分辨率 |_ 480p |\
| |_ 720p |\
| |_ 1080p | |_ 480p |\
| | | |_ 720p |\
| | | |_ 1080p`参考图场景不支持` | |
| | || | | \
|ratio |\
|宽高比 | |\
| | |\
| |_ 16:9 |\
| |_ 4:3 |\
| |_ 1:1 |\
| |_ 3:4 |\
| |_ 9:16 |\
| |_ 21:9 |\
| |_ adaptive |\
| | |\
| | |\
| |480p 各画面比例的宽高像素值如下 |\
| | |\
| |_ `16:9`：864×480 |\
| |_ `4:3`：736×544 |\
| |_ `1:1`：640×640 |\
| |_ `3:4`：544×736 |\
| |_ `9:16`：480×864 |\
| |_ `21:9`：960×416 |\
| | |\
| |720p 各画面比例的宽高像素值如下 |\
| | |\
| |_ `16:9`：1248×704 |\
| |_ `4:3`：1120×832 |\
| |_ `1:1`：960×960 |\
| |_ `3:4`：832×1120 |\
| |_ `9:16`：704×1248 |\
| |_ `21:9`：1504×640 |\
| | |\
| |1080p 各画面比例的宽高像素值如下 |\
| | |\
| |_ `16:9`：1920×1088 |\
| |_ `4:3`：1664×1248 |\
| |_ `1:1`：1440×1440 |\
| |_ `3:4`：1248×1664 |\
| |_ `9:16`：1088×1920 |\
| |_ `21:9`：2176×928 | | |\
| | | | |\
| | | |_ 16:9 |\
| | | |_ 4:3 |\
| | | |_ 1:1 |\
| | | |_ 3:4 |\
| | | |_ 9:16 |\
| | | |_ 21:9 |\
| | | | |\
| | | | |\
| | | | |\
| | | |480p 各画面比例的宽高像素值如下 |\
| | | | |\
| | | |_ `16:9`：864×480 |\
| | | |_ `4:3`：736×544 |\
| | | |_ `1:1`：640×640 |\
| | | |_ `3:4`：544×736 |\
| | | |_ `9:16`：480×864 |\
| | | |_ `21:9`：960×416 |\
| | | | |\
| | | |720p 各画面比例的宽高像素值如下 |\
| | | | |\
| | | |_ `16:9`：1248×704 |\
| | | |_ `4:3`：1120×832 |\
| | | |_ `1:1`：960×960 |\
| | | |_ `3:4`：832×1120 |\
| | | |_ `9:16`：704×1248 |\
| | | |_ `21:9`：1504×640 |\
| | | | |\
| | | |1080p 各画面比例的宽高像素值如下 |\
| | | | |\
| | | |_ `16:9`：1920×1088 |\
| | | |_ `4:3`：1664×1248 |\
| | | |_ `1:1`：1440×1440 |\
| | | |_ `3:4`：1248×1664 |\
| | | |_ `9:16`：1088×1920 |\
| | | |_ `21:9`：2176×928 | |\
| | | | | |\
| | | | |_ 16:9 |\
| | | | |_ 4:3 |\
| | | | |_ 1:1 |\
| | | | |_ 3:4 |\
| | | | |_ 9:16 |\
| | | | |_ 21:9 |\
| | | | |_ adaptive`参考图场景不支持` |\
| | | | | |\
| | | | | |\
| | | | |480p 各画面比例的宽高像素值如下 |\
| | | | | |\
| | | | |_ `16:9`：864×480 |\
| | | | |_ `4:3`：736×544 |\
| | | | |_ `1:1`：640×640 |\
| | | | |_ `3:4`：544×736 |\
| | | | |_ `9:16`：480×864 |\
| | | | |_ `21:9`：960×416 |\
| | | | | |\
| | | | |720p 各画面比例的宽高像素值如下 |\
| | | | | |\
| | | | |_ `16:9`：1248×704 |\
| | | | |_ `4:3`：1120×832 |\
| | | | |_ `1:1`：960×960 |\
| | | | |_ `3:4`：832×1120 |\
| | | | |_ `9:16`：704×1248 |\
| | | | |_ `21:9`：1504×640 |\
| | | | | |\
| | | | |1080p 各画面比例的宽高像素值如下`参考图场景不支持` |\
| | | | | |\
| | | | |_ `16:9`：1920×1088 |\
| | | | |_ `4:3`：1664×1248 |\
| | | | |_ `1:1`：1440×1440 |\
| | | | |_ `3:4`：1248×1664 |\
| | | | |_ `9:16`：1088×1920 |\
| | | | |_ `21:9`：2176×928 |
| | || || \
|duration |\
|生成视频时长（秒） |2 ~12 秒 | |2 ~12 秒 | |
| | || || \
|frames |\
|生成视频帧数 |支持 [29, 289] 区间内所有满足 25 + 4n 格式的整数值，其中 n 为正整数。 | |支持 [29, 289] 区间内所有满足 25 + 4n 格式的整数值，其中 n 为正整数。 | |
| | || || \
|framespersecond |\
|帧率 |24 | |24 | |
| | || || \
|seed |\
| 种子整数 |![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/aba4522e4aab46318574c8c3e460d20b~tplv-goo7wpa0wc-image.image =20x) | |![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/aba4522e4aab46318574c8c3e460d20b~tplv-goo7wpa0wc-image.image =20x) | |
| | || || \
|camerafixed |\
|是否固定摄像头 |![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/aba4522e4aab46318574c8c3e460d20b~tplv-goo7wpa0wc-image.image =20x) | |![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/aba4522e4aab46318574c8c3e460d20b~tplv-goo7wpa0wc-image.image =20x) |\
| | | |`参考图场景不支持` | |
| | || || \
|watermark |\
|是否包含水印 |![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/aba4522e4aab46318574c8c3e460d20b~tplv-goo7wpa0wc-image.image =20x) | |![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/aba4522e4aab46318574c8c3e460d20b~tplv-goo7wpa0wc-image.image =20x) | |

<span id="e190e738"></span>

# 进阶使用

<span id="c30d9829"></span>

## 离线推理

针对推理时延敏感度低的场景，建议将 `service_tier` 设为 `flex`，一键切换至离线推理模式——价格仅为在线推理的 50%，显著降低业务成本。
注意根据业务场景设置合适的超时时间，超过该时间后任务将自动终止。

```Shell
curl https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-0-pro-250528",
    "content": [
        {
            "type": "text",
            "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动  --ratio adaptive  --dur 5"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
            }
        }
    ],
   "service_tier": "flex",
   "execution_expires_after": 172800
}'
```

<span id="141cf7fa"></span>

## 生成多个连续视频

使用前一个生成视频的尾帧，作为后一个视频任务的首帧，循环生成多个连续的视频。

```Python
import os
import time
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Ark client to read your API Key from an environment variable
client = Ark(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.environ.get("ARK_API_KEY"),
)

def generate_video_with_last_frame(prompt, initial_image_url=None):
    """
    Generate video and return video URL and last frame URL
    Parameters:
    prompt: Text prompt for video generation
    initial_image_url: Initial image URL (optional)
    Returns:
    video_url: Generated video URL
    last_frame_url: URL of the last frame of the video
    """
    print(f"----- Generating video: {prompt} -----")

    # Build content list
    content = [{
        "text": prompt,
        "type": "text"
    }]

    # If initial image is provided, add to content
    if initial_image_url:
        content.append({
            "image_url": {
                "url": initial_image_url
            },
            "type": "image_url"
        })

    # Create video generation task
    create_result = client.content_generation.tasks.create(
        model="doubao-seedance-1-0-pro-250528",
        content=content,
        return_last_frame=True
    )

    # Poll to check task status
    task_id = create_result.id
    while True:
        get_result = client.content_generation.tasks.get(task_id=task_id)
        status = get_result.status

        if get_result.status == "succeeded":
            print("Video generation succeeded")
            try:
                if hasattr(get_result, 'content') and hasattr(get_result.content, 'video_url') and hasattr(get_result.content, 'last_frame_url'):
                    return get_result.content.video_url, get_result.content.last_frame_url
                print("Failed to obtain video URL or last frame URL")
                return None, None
            except Exception as e:
                print(f"Error occurred while obtaining video URL and last frame URL: {e}")
                return None, None
        elif status == "failed":
            print(f"----- Video generation failed -----")
            print(f"Error: {get_result.error}")
            return None, None
        else:
            print(f"Current status: {status}, retrying in 10 seconds...")
            time.sleep(10)



if __name__ == "__main__":
    # Define 3 video prompts
    prompts = [
        "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动  --ratio adaptive  --dur 5",
        "女孩和狐狸在草地上奔跑，阳光明媚，女孩的笑容灿烂，狐狸欢快地跳跃  --ratio adaptive  --dur 5",
        "女孩和狐狸坐在树下休息，女孩轻轻抚摸狐狸的毛发，狐狸温顺地趴在女孩腿上  --ratio adaptive  --dur 5"
    ]

    # Store generated video URLs
    video_urls = []

    # Initial image URL
    initial_image_url = "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"

    # Generate 3 short videos
    for i, prompt in enumerate(prompts):
        print(f"Generating video {i+1}")
        video_url, last_frame_url = generate_video_with_last_frame(prompt, initial_image_url)

        if video_url and last_frame_url:
            video_urls.append(video_url)
            print(f"Video {i+1} URL: {video_url}")
            # Use the last frame of the current video as the first frame of the next video
            initial_image_url = last_frame_url
        else:
            print(f"Video {i+1} generation failed, exiting program")
            exit(1)

    print("All videos generated successfully!")
    print("Generated video URL list:")
    for i, url in enumerate(video_urls):
        print(f"Video {i+1}: {url}")
```

后续您可以自行使用 FFmpeg 等工具，将生成的多个短视频拼接成一个完整长视频。
<span id="b046a676"></span>

# 提示词建议

- 用简洁准确的自然语言写出你想要的效果。
- 如果有较为明确的效果预期，建议先用生图模型生成符合预期的图片，再用图生视频进行视频片段的生成
- 文生视频会有较大的结果随机性，可以用于激发创作灵感
- 图生视频时请尽量上传高清高质量的图片，上传图片的质量对图生视频影响较大。
- 当生成的视频不符合预期时，建议修改提示词，将抽象描述换成具象描述，并注意删除不重要的部分，将重要内容前置。
- 更多提示词的使用技巧请参见 [Seedance 提示词指南](https://www.volcengine.com/docs/82379/1587797)。

<span id="66cb028f"></span>

# 使用限制

<span id="2760a484"></span>

## 保存时间

任务数据（如任务状态、视频URL等）仅保留24小时，超时后会被自动清除。请您务必及时保存生成的视频。
<span id="b25b1821"></span>

## 限流说明

<span id="946ba4cf"></span>

### 模型限流

**default（在线推理）**

- RPM 限流：账号下同模型（区分模型版本）每分钟允许创建的任务数量上限。若超过该限制，创建视频生成任务时会报错。
- 并发数限制：账号下同模型（区分模型版本）同一时刻在处理中的任务数量上限。超过此限制的任务将进入队列等待处理。
- 不同模型的限制值不同，详见[视频生成能力](/docs/82379/1330310#2705b333)。

**flex（离线推理）**

- TPD 限流：账号在一天内对同一模型（区分模型版本）的总调用 token 上限。超过此限制的调用请求将被拒绝。不同模型的 TPD 限流值不同，详见[视频生成能力](/docs/82379/1330310#2705b333)。

<span id="f76aafc8"></span>

## 图片裁剪规则

**Seedance 系列模型的图生视频场景，支持设置生成视频的宽高比。​**当选择的视频宽高与您上传的图片宽高比不一致时，方舟会对您的图片进行裁剪，裁剪时会居中裁剪。详细规则如下：
:::tip
若要呈现出较好的视频效果，建议所指定的视频宽高比（ratio）与实际上传图片的宽高比尽可能接近。
:::

1. 输入参数：
   - 原始图片宽度记为`W`（单位：像素），高度记为`H`（单位：像素）。
   - 目标比例记为`A:B`（例如，21:9），这表示裁剪后的宽度与高度之比应为 `A/B`（如 21/9≈2.333）。
2. 比较宽高比：

- 计算原始图片的宽高比`Ratio_原始=W/H`。
- 计算目标比例的比值`Ratio_目标=A/B`（例如，21:9 的 Ratio目标=21/9≈2.333)。
- 根据比较结果，决定裁剪基准：
  - 如果`Ratio_原始<Ratio_目标`（即原始图片“太高”或“竖高”），则以宽度为基准裁剪。
  - 如果`Ratio_原始>Ratio_目标`（即原始图片“太宽”或“横宽”），则以高度为基准裁剪。
  - 如果相等，则无需裁剪，直接使用全图。

3. 裁剪尺寸计算（量化公式）：
   - 以宽度为基准（适用于竖高图片）：
     - 裁剪宽度`Crop_W=W`（使用整个原始宽度）。
     - 裁剪高度`Crop_H=(B/A)×W`（根据目标比例等比例计算高度）。
     - 裁剪区域的起始坐标（居中定位）：
       - X 坐标（水平）：总是 0（因为宽度全用，从左侧开始）。
       - Y 坐标（垂直）：`(H−Crop_H)/2`（确保垂直居中，从顶部开始）。
   - 以高度为基准（适用于横宽图片）：
     - 裁剪高度`Crop_H=H`（使用整个原始高度）。
     - 裁剪宽度`Crop_W=(A/B)×H`（根据目标比例等比例计算宽度）。
     - 裁剪区域的起始坐标（居中定位）：
       - X 坐标（水平）：`(W−Crop_W)/2`（确保水平居中，从左侧开始）。
       - Y 坐标（垂直）：总是 0（因为高度全用，从顶部开始）。
4. 裁剪结果：
   - 最终裁剪出的图片尺寸为`Crop_W×Crop_H`，比例严格为`A:B`，且完全位于原始图片内部，无黑边。
   - 裁剪区域总是以原始图片中心为基准，因此内容居中。
5. 裁剪示例：

> 以 Seedance 1.0 Pro 首帧图生视频功能为例

| | | | \
|输入的首帧图片 |指定的宽高比ratio |生成的视频结果 |
|---|---|---|
| | | | \
|16:9 |\
| |\
|![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/c66d7faff6104320a981b36149dc713f~tplv-goo7wpa0wc-image.image =1920x) |\
| |21:9 |\
| | | |\
| | |<BytedReactXgplayer config={{ url: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/db372038e0ba464f9656364f0b5aabba~tplv-goo7wpa0wc-image.image', poster: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/db372038e0ba464f9656364f0b5aabba~tplv-goo7wpa0wc-video-poster.jpeg' }} ></BytedReactXgplayer> |\
| | | |\
| | | |
|^^| | | \
| |16:9 | |\
| | |<BytedReactXgplayer config={{ url: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/a3b21bf79c1948ff8f43cbed05c48d66~tplv-goo7wpa0wc-image.image', poster: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/a3b21bf79c1948ff8f43cbed05c48d66~tplv-goo7wpa0wc-video-poster.jpeg' }} ></BytedReactXgplayer> |\
| | | |\
| | | |\
| | | |
|^^| | | \
| |4:3 | |\
| | |<BytedReactXgplayer config={{ url: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/3917539f20904631a1a0fae540b708ae~tplv-goo7wpa0wc-image.image', poster: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/3917539f20904631a1a0fae540b708ae~tplv-goo7wpa0wc-video-poster.jpeg' }} ></BytedReactXgplayer> |\
| | | |\
| | | |
|^^| | | \
| |1:1 | |\
| | |<BytedReactXgplayer config={{ url: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/ccc12b9d3b0f43f088316e5a22f2b75e~tplv-goo7wpa0wc-image.image', poster: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/ccc12b9d3b0f43f088316e5a22f2b75e~tplv-goo7wpa0wc-video-poster.jpeg' }} ></BytedReactXgplayer> |\
| | | |\
| | | |
|^^| | | \
| |3:4 | |\
| | |<BytedReactXgplayer config={{ url: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/9c42b44d5a0949ab8afa8da59cdf9786~tplv-goo7wpa0wc-image.image', poster: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/9c42b44d5a0949ab8afa8da59cdf9786~tplv-goo7wpa0wc-video-poster.jpeg' }} ></BytedReactXgplayer> |\
| | | |\
| | | |
|^^| | | \
| |9:16 | |\
| | |<BytedReactXgplayer config={{ url: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/9b0bc3b269a94f0b8a02c537b176075f~tplv-goo7wpa0wc-image.image', poster: 'https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/9b0bc3b269a94f0b8a02c537b176075f~tplv-goo7wpa0wc-video-poster.jpeg' }} ></BytedReactXgplayer> |\
| | | |\
| | | |

<span id="5ab4d3aa"></span>

# API 参数

视频生成的 API 接口详细介绍请参见 [视频生成 API](https://www.volcengine.com/docs/82379/1520758)。

<style>
    /* 表格容器：小屏横向滚动，限制最大宽度避免过宽 */
    .table-container {
        overflow-x: auto;
        max-width: 100%; /* 容器占满父级，不超出页面 */
    }
    /* 表格：宽度自适应，内容优先 */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    /* 单元格：垂直顶格，内边距优化，宽度按内容/比例分配 */
    td {
        vertical-align: top;
        padding: 8px;
    }
    /* 图片：自适应单元格，保持比例 */
    img {
        max-width: 100%;
        height: auto;
    }
    /* 响应式：小屏（如手机）下优化显示 */
    @media (max-width: 768px) {
        td {
            width: 100%; /* 小屏时列垂直堆叠 */
            display: block;
        }
        tr {
            display: block;
            margin-bottom: 15px;
            border: 1px solid #ddd;
        }
    }
</style>
