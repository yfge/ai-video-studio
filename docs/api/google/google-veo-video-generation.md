# Google Veo Video Generation API

> Source: https://ai.google.dev/gemini-api/docs/video?hl=zh-cn

## Overview

Veo 3.1 represents Google's most advanced model for generating high-fidelity 8-second 720p or 1080p videos with stunning photorealism and native-generated audio. The model excels across various visual and cinematic styles.

### Key Features in Veo 3.1

- **Video Extension**: Extend previously generated Veo videos
- **Specified Frame Generation**: Generate videos by defining first and last frames
- **Image-Based Guidance**: Use up to three reference images to guide generated video content

## API Models and Endpoints

### Current Model Versions

| Model ID | Status | Input Types | Output | Text Limit |
|----------|--------|-------------|--------|------------|
| `veo-3.1-generate-preview` | Preview | Text, Images | Video with Audio | 1,024 tokens |
| `veo-3.1-fast-generate-preview` | Preview | Text, Images | Video with Audio | 1,024 tokens |
| `veo-3.0-generate-001` | Stable | Text, Images | Video with Audio | 1,024 tokens |
| `veo-3.0-fast-generate-001` | Stable | Text, Images | Video with Audio | 1,024 tokens |
| `veo-2.0-generate-001` | Stable | Text, Images | Video | Variable |

## Model Features Comparison

| Feature | Veo 3.1 | Veo 3 | Veo 2 |
|---------|---------|-------|-------|
| **Audio** | Native generation | Native generation | Muted only |
| **Input Types** | Text-to-video, Image-to-video, Video-to-video | Text-to-video, Image-to-video | Text-to-video, Image-to-video |
| **Resolution** | 720p, 1080p (8s only) | 720p, 1080p (16:9 only) | 720p |
| **Frame Rate** | 24 fps | 24 fps | 24 fps |
| **Video Duration** | 4s, 6s, 8s | 8s | 5-8s |
| **Videos Per Request** | 1 | 1 | 1 or 2 |
| **Status** | Preview | Stable | Stable |

## API Parameters Reference

| Parameter | Description | Type | Veo 3.1 | Veo 3 | Veo 2 |
|-----------|-------------|------|---------|-------|-------|
| `prompt` | Text description of the video. Supports audio prompts. | string | Yes | Yes | Yes |
| `negativePrompt` | Text describing what should NOT appear in the video. | string | Yes | Yes | Yes |
| `image` | Initial image to animate. | Image object | Yes | Yes | Yes |
| `lastFrame` | Final image for interpolation. Must pair with `image`. | Image object | Yes | Yes | Yes |
| `referenceImages` | Up to 3 images for style/content guidance. | VideoGenerationReferenceImage[] | Yes (3.1 only) | No | No |
| `video` | Video to extend. | Video object | Yes | No | No |
| `aspectRatio` | Video aspect ratio: "16:9" (default) or "9:16" | string | Yes | Yes | Yes |
| `resolution` | Output resolution: "720p" (default) or "1080p" | string | Yes | Yes | Limited |
| `durationSeconds` | Video length: 4, 6, or 8 seconds | number | Yes | Yes | Yes |
| `personGeneration` | Control person generation. Regional restrictions apply. | string | Limited | Limited | Limited |

## Code Examples

### Python - Text-to-Video Generation

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A close up of two people staring at a cryptic drawing on a wall,
torchlight flickering. A man murmurs, 'This must be it. That's the secret code.'
The woman looks at him and whispering excitedly, 'What did you find?'"""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video.
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("dialogue_example.mp4")
print("Generated video saved to dialogue_example.mp4")
```

### JavaScript - Text-to-Video Generation

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

const prompt = `A close up of two people staring at a cryptic drawing on a wall,
torchlight flickering. A man murmurs, 'This must be it. That's the secret code.'
The woman looks at him and whispering excitedly, 'What did you find?'`;

let operation = await ai.models.generateVideos({
    model: "veo-3.1-generate-preview",
    prompt: prompt,
});

// Poll the operation status until the video is ready.
while (!operation.done) {
    console.log("Waiting for video generation to complete...")
    await new Promise((resolve) => setTimeout(resolve, 10000));
    operation = await ai.operations.getVideosOperation({
        operation: operation,
    });
}

// Download the generated video.
ai.files.download({
    file: operation.response.generatedVideos[0].video,
    downloadPath: "dialogue_example.mp4",
});
console.log(`Generated video saved to dialogue_example.mp4`);
```

### Go - Text-to-Video Generation

```go
package main

import (
    "context"
    "log"
    "os"
    "time"

    "google.golang.org/genai"
)

func main() {
    ctx := context.Background()
    client, err := genai.NewClient(ctx, nil)
    if err != nil {
        log.Fatal(err)
    }

    prompt := `A close up of two people staring at a cryptic drawing on a wall,
    torchlight flickering. A man murmurs, 'This must be it. That's the secret code.'
    The woman looks at him and whispering excitedly, 'What did you find?'`

    operation, _ := client.Models.GenerateVideos(
        ctx,
        "veo-3.1-generate-preview",
        prompt,
        nil,
        nil,
    )

    // Poll the operation status until the video is ready.
    for !operation.Done {
        log.Println("Waiting for video generation to complete...")
        time.Sleep(10 * time.Second)
        operation, _ = client.Operations.GetVideosOperation(ctx, operation, nil)
    }

    // Download the generated video.
    video := operation.Response.GeneratedVideos[0]
    client.Files.Download(ctx, video.Video, nil)
    fname := "dialogue_example.mp4"
    _ = os.WriteFile(fname, video.Video.VideoBytes, 0644)
    log.Printf("Generated video saved to %s\n", fname)
}
```

### REST API - Text-to-Video Generation

```bash
#!/bin/bash
BASE_URL="https://generativelanguage.googleapis.com/v1beta"

# Send request to generate video and capture the operation name
operation_name=$(curl -s "${BASE_URL}/models/veo-3.1-generate-preview:predictLongRunning" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X "POST" \
  -d '{
    "instances": [{
        "prompt": "A close up of two people staring at a cryptic drawing on a wall, torchlight flickering."
      }
    ]
  }' | jq -r .name)

# Poll the operation status until the video is ready
while true; do
  status_response=$(curl -s -H "x-goog-api-key: $GEMINI_API_KEY" "${BASE_URL}/${operation_name}")
  is_done=$(echo "${status_response}" | jq .done)

  if [ "${is_done}" = "true" ]; then
    video_uri=$(echo "${status_response}" | jq -r '.response.generateVideoResponse.generatedSamples[0].video.uri')
    echo "Downloading video from: ${video_uri}"
    curl -L -o dialogue_example.mp4 -H "x-goog-api-key: $GEMINI_API_KEY" "${video_uri}"
    break
  fi
  sleep 10
done
```

## Image-to-Video Generation

### Python - Generate Image Then Video

```python
import time
from google import genai

client = genai.Client()

prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"

# Step 1: Generate an image with Nano Banana
image = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config={"response_modalities":['IMAGE']}
)

# Step 2: Generate video with Veo 3.1 using the image
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=image.parts[0].as_image(),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3_with_image_input.mp4")
print("Generated video saved to veo3_with_image_input.mp4")
```

### JavaScript - Generate Image Then Video

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

const prompt = "Panning wide shot of a calico kitten sleeping in the sunshine";

// Step 1: Generate an image with Nano Banana
const imageResponse = await ai.models.generateContent({
  model: "gemini-2.5-flash-image",
  prompt: prompt,
});

// Step 2: Generate video with Veo 3.1 using the image
let operation = await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  prompt: prompt,
  image: {
    imageBytes: imageResponse.generatedImages[0].image.imageBytes,
    mimeType: "image/png",
  },
});

// Poll the operation status until the video is ready
while (!operation.done) {
  console.log("Waiting for video generation to complete...")
  await new Promise((resolve) => setTimeout(resolve, 10000));
  operation = await ai.operations.getVideosOperation({
    operation: operation,
  });
}

// Download the video
ai.files.download({
    file: operation.response.generatedVideos[0].video,
    downloadPath: "veo3_with_image_input.mp4",
});
console.log(`Generated video saved to veo3_with_image_input.mp4`);
```

### REST API - Image-to-Video Generation (bytesBase64Encoded)

> Note: When calling `:predictLongRunning` directly via REST, the image payload uses `bytesBase64Encoded` (base64 string). Some SDK examples expose this as `imageBytes` and handle conversion internally.

```bash
#!/bin/bash
BASE_URL="https://generativelanguage.googleapis.com/v1beta"

# Prepare a small PNG/JPEG and base64-encode it as a single line (no newlines).
IMAGE_B64=$(base64 -w 0 ./start_frame.jpg)

operation_name=$(curl -s "${BASE_URL}/models/veo-3.1-generate-preview:predictLongRunning" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X "POST" \
  -d \"{
    \\\"instances\\\": [{
      \\\"prompt\\\": \\\"A cinematic shot of a woman walking into a dimly lit office.\\\",
      \\\"image\\\": {\\\"mimeType\\\": \\\"image/jpeg\\\", \\\"bytesBase64Encoded\\\": \\\"${IMAGE_B64}\\\"}
    }],
    \\\"parameters\\\": {\\\"aspectRatio\\\": \\\"16:9\\\", \\\"resolution\\\": \\\"720p\\\", \\\"durationSeconds\\\": 6}
  }\" | jq -r .name)

echo \"operation: ${operation_name}\"
```

## Reference Images Feature

### Python - Using Reference Images

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = "The video opens with a medium, eye-level shot of a beautiful woman with dark hair..."

dress_reference = types.VideoGenerationReferenceImage(
  image=dress_image,
  reference_type="asset"
)

sunglasses_reference = types.VideoGenerationReferenceImage(
  image=glasses_image,
  reference_type="asset"
)

woman_reference = types.VideoGenerationReferenceImage(
  image=woman_image,
  reference_type="asset"
)

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
      reference_images=[dress_reference, sunglasses_reference, woman_reference],
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_with_reference_images.mp4")
```

## First and Last Frame Interpolation

### Python - Using First and Last Frame

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = "A cinematic, haunting video. A ghostly woman with long white hair..."

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=first_image,
    config=types.GenerateVideosConfig(
      last_frame=last_image
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_with_interpolation.mp4")
```

## Video Extension/Continuation

### Python - Extending a Video

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = "Track the butterfly into the garden as it lands on an orange origami flower."

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=operation.response.generated_videos[0].video,
    prompt=prompt,
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        resolution="720p"
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_extension.mp4")
```

## Using Parameters

### Python Example

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A cinematic shot of a majestic lion in the savannah.",
    config=types.GenerateVideosConfig(
        negative_prompt="cartoon, drawing, low quality",
        aspect_ratio="16:9",
        resolution="720p",
        duration_seconds="8"
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("parameters_example.mp4")
```

### JavaScript Example

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

let operation = await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  prompt: "A cinematic shot of a majestic lion in the savannah.",
  config: {
    aspectRatio: "16:9",
    negativePrompt: "cartoon, drawing, low quality"
  },
});

// Poll and download...
```

### REST Example

```bash
#!/bin/bash
BASE_URL="https://generativelanguage.googleapis.com/v1beta"

operation_name=$(curl -s "${BASE_URL}/models/veo-3.1-generate-preview:predictLongRunning" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X "POST" \
  -d '{
    "instances": [{
        "prompt": "A cinematic shot of a majestic lion in the savannah."
      }
    ],
    "parameters": {
      "aspectRatio": "16:9",
      "negativePrompt": "cartoon, drawing, low quality"
    }
  }' | jq -r .name)

# Poll and download...
```

## Prompt Engineering Guide

### Fundamental Prompt Structure

An effective prompt should contain:

- **Subject**: Objects, people, animals, or scenes (e.g., "cityscape," "nature," "vehicles")
- **Action**: What the subject is doing (e.g., "walking," "running," "turning head")
- **Style**: Specific cinematic keywords (e.g., "sci-fi," "noir," "horror") or animation styles
- **Camera Position and Movement** (optional): "aerial shot," "eye-level," "overhead," "orbital shot," "low-angle"
- **Composition** (optional): "wide shot," "close-up," "single shot," "two-shot"
- **Focus and Lens Effects** (optional): "shallow depth of field," "soft focus," "macro," "wide-angle"
- **Atmosphere** (optional): "blue tones," "nighttime," "warm tones"

### Prompt Writing Tips

- **Use descriptive language**: Employ adjectives and adverbs to paint a clear picture
- **Enhance facial details**: Specify facial details as a focus point, using words like "portrait"

### Audio Prompting (Veo 3+)

- **Dialogue**: Use quotation marks for specific spoken words (e.g., "This must be the key," he whispered)
- **Sound Effects (SFX)**: Explicitly describe sounds (e.g., tires screeching, engine roaring)
- **Ambient Noise**: Describe environmental soundscape (e.g., faint eerie buzzing echoing in background)

### Negative Prompts

- Don't use directive language like "no" or "without" (e.g., "no walls")
- Do describe what you don't want to see (e.g., "walls, frames")

## Prompt Examples

### Subject and Background

```
A white concrete apartment building with flowing organic shapes, seamlessly integrated
with lush green plants and futuristic elements.
```

```
A satellite floating in space with the moon and stars in the background.
```

### Action

```
Wide shot: A woman walking on a beach facing the horizon at sunset,
appearing satisfied and relaxed.
```

### Style

```
Film noir style, a man and woman walking down a street, mysterious, cinematic, black and white.
```

### Camera Movement and Composition

```
First-person perspective shot: A vintage car driving in the rain, nighttime cityscape,
cinematic style.
```

```
Extreme close-up of an eye with a city reflected in it.
```

### Atmosphere

```
Close-up shot of a girl holding an adorable golden retriever puppy in a sunny park.
```

```
Cinematic close-up: A sad woman on a bus in the rain, cool blue tones creating a melancholic mood.
```

## Limitations and Constraints

- **Request Latency**: Minimum 11 seconds; Maximum 6 minutes during peak hours
- **Regional Restrictions**: In EU, UK, Switzerland, Middle East, and North Africa, `personGeneration` values are restricted by model version
- **Video Retention**: Generated videos stored for 2 days, then deleted. Download locally within this period
- **Watermarking**: Videos include SynthID watermark for AI-generated content identification
- **Safety**: Videos processed through safety filtering and memory checks
- **Audio Issues**: Occasionally, Veo 3.1 may block video generation due to safety filters or audio processing problems

### Input Video Restrictions for Extension

- Maximum duration: 141 seconds from Veo
- Aspect ratios: 9:16 or 16:9
- Resolution: 720p
- Maximum extension length: 7 seconds per operation, up to 20 extensions allowed
- Output: Original video plus generated extension, maximum 148 seconds total

## Key Takeaways

1. **Veo 3.1** is the most advanced model with support for reference images, video extension, and frame interpolation
2. **Video generation is asynchronous** - use polling to check operation status
3. **Rich prompts yield better results** - include details about subject, action, style, camera, and atmosphere
4. **Audio can be prompted explicitly** - specify dialogue, sound effects, and ambient noise
5. **Multiple input modalities** - generate from text, images, or existing videos
6. **2-day retention policy** - download generated videos before they expire
7. **Regional restrictions apply** - particularly for person generation in certain areas
