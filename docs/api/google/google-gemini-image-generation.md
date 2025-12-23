# Google Gemini Image Generation API

> Source: https://ai.google.dev/gemini-api/docs/image-generation?hl=zh-cn

## Overview

Google's Gemini API offers native image generation and editing capabilities through two models:

- **Gemini 2.5 Flash Image** (Nano Banana): Optimized for speed and efficiency
- **Gemini 3 Pro Image Preview** (Nano Banana Pro): Professional-grade output with advanced features

## Core Features

### Text-to-Image Generation
Generate images from text descriptions with control over composition, lighting, and style.

### Image Editing
Modify existing images through text prompts, adding/removing elements while maintaining original context and lighting.

### Multi-Turn Iteration
Refine images conversationally across multiple rounds until achieving desired results.

### High-Fidelity Text Rendering
Accurate text generation suitable for logos, charts, and marketing materials.

## Model Comparison

| Feature | Gemini 2.5 Flash | Gemini 3 Pro Preview |
|---------|------------------|----------------------|
| Max Resolution | 1024px | 4K |
| Input Images | Up to 3 | Up to 14 |
| Google Search Integration | No | Yes |
| Thinking Process | No | Yes (default) |
| Speed | Optimized | Professional |

## API Parameters

### Image Configuration

```
aspect_ratio: "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
image_size: "1K", "2K", "4K" (Gemini 3 Pro only)
response_modalities: ["TEXT", "IMAGE"] or ["IMAGE"]
```

### Aspect Ratios & Resolutions
- **Gemini 2.5 Flash**: All aspect ratios generate 1290 tokens
- **Gemini 3 Pro**: 1K (1120 tokens), 2K (1120 tokens), 4K (2000 tokens)

## Code Examples

### Python - Text to Image

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=["Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
```

### JavaScript - Text to Image

```javascript
import { GoogleGenAI } from "@google/genai";
import * as fs from "node:fs";

const ai = new GoogleGenAI({});

const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-image",
    contents: "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme",
});

for (const part of response.candidates[0].content.parts) {
    if (part.text) {
        console.log(part.text);
    } else if (part.inlineData) {
        const imageData = part.inlineData.data;
        const buffer = Buffer.from(imageData, "base64");
        fs.writeFileSync("gemini-native-image.png", buffer);
    }
}
```

### REST API

```bash
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"}
      ]
    }]
  }'
```

### Image Editing Example (Python)

```python
from google import genai
from PIL import Image

client = genai.Client()

image = Image.open("/path/to/cat_image.png")
prompt = "Add a small, knitted wizard hat on the cat's head, sitting comfortably"

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt, image],
)

for part in response.parts:
    if part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
```

### Multi-Turn Chat (Python)

```python
from google import genai
from google.genai import types

client = genai.Client()

chat = client.chats.create(
    model="gemini-3-pro-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        tools=[{"google_search": {}}]
    )
)

message = "Create a vibrant infographic explaining photosynthesis as a recipe"
response = chat.send_message(message)

# Update with second message
message2 = "Update this infographic to be in Spanish"
response2 = chat.send_message(message2)
```

### Advanced Composition (Multiple Images)

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        "An office group photo of these people, they are making funny faces.",
        Image.open('person1.png'),
        Image.open('person2.png'),
        Image.open('person3.png'),
        Image.open('person4.png'),
        Image.open('person5.png'),
    ],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="5:4",
            image_size="2K"
        ),
    )
)
```

### Using Google Search Grounding

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="Visualize the current weather forecast for the next 5 days in San Francisco",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(aspect_ratio="16:9"),
        tools=[{"google_search": {}}]
    )
)
```

### Output Configuration - Image Only

```python
config=types.GenerateContentConfig(
    response_modalities=['Image']  # Image only, no text
)
```

## Prompting Strategies

### Effective Techniques

1. **Narrative Description**: Favor detailed paragraphs over keyword lists
2. **Context & Intent**: Explain the image's purpose (e.g., "for luxury skincare branding")
3. **Iterative Refinement**: Use follow-up prompts for adjustments
4. **Step-by-Step Instructions**: Break complex scenes into sequential steps
5. **Semantic Negatives**: Describe desired scenes positively rather than listing restrictions
6. **Photography Language**: Use terms like "wide-angle," "macro," "low-angle perspective"

### Prompt Templates

#### Photorealistic

```
A photorealistic [shot type] of [subject], [action], set in [environment].
Illuminated by [lighting], creating a [mood] atmosphere.
Captured with [camera/lens], emphasizing [details]. [Aspect ratio].
```

#### Stylized Illustration

```
A [style] sticker of [subject], featuring [characteristics] and [color palette].
Design should have [line style] and [shading]. Background: [specification].
```

#### Text in Images

```
Create a [image type] for [brand] with text "[text]" in a [font style].
Design should be [style], with [color scheme].
```

## Primary Use Cases

1. **Photorealistic scenes** using photography terminology
2. **Stylized illustrations and stickers** with transparent backgrounds
3. **Text-accurate designs** for logos, menus, and marketing materials
4. **Product photography** for e-commerce applications
5. **Minimalist compositions** with negative space for overlays
6. **Sequential art** (comic panels/storyboards)
7. **Real-time imagery** using Google Search grounding

## Editing Capabilities

- Adding/removing elements
- Inpainting (semantic masking)
- Style transfer
- Multi-image composition
- Detail preservation
- Sketch refinement
- Character consistency across angles

## Safety & Policies

- Generated images include **SynthID watermarks** for identification
- All uploads require necessary usage rights
- Prohibited: content deceiving, harassing, or injuring others
- Adhere to "Use Limitations Policy" for generative AI services

### Supported Languages

English, Arabic, German, Spanish, French, Hindi, Indonesian, Italian, Japanese, Korean, Portuguese, Russian, Ukrainian, Vietnamese, Chinese (13+ languages)

## Limitations

- Image generation doesn't accept audio/video input
- Exact output quantities may vary from requests
- `gemini-2.5-flash-image`: max 3 input images
- `gemini-3-pro-image-preview`: max 5 high-fidelity + 14 total images
- Text generation works better when requested before image creation

## Thought Signatures

For Gemini 3 Pro's reasoning process: thought signatures preserve inference context across multi-turn conversations. The SDK automatically handles these when using chat functions.

## Batch Processing

For large-scale generation, use the Batch API for higher rate limits (accepts 24-hour delays).

## Additional Resources

- [Cookbook](https://ai.google.dev/gemini-api/docs/cookbook): Example implementations and walkthroughs
- [Veo Guide](https://ai.google.dev/gemini-api/docs/veo): Video generation capabilities
- [Imagen](https://ai.google.dev/gemini-api/docs/imagen): Specialized image generation model alternative
- [Batch API](https://ai.google.dev/gemini-api/docs/batch): High-volume processing documentation
