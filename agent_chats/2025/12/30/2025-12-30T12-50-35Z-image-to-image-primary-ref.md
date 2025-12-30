---
id: 2025-12-30T12-50-35Z-image-to-image-primary-ref
date: 2025-12-30T12:50:35Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, storyboard, image-to-image]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Fix image-to-image modal to show clicked candidate image as primary reference"
---

## User Prompt

从首帧尾帧的图像选择弹出的图生图，应该：
1. 以选择的图片为首要参考图
2. 带入其他图片，可选可不选
3. 自定义提示词
4. 可以选择生成的是首帧还是尾帧

## Goals

1. Show the clicked candidate image as the primary reference at the top of the modal
2. Keep environment and character images as optional secondary references
3. Maintain existing functionality for custom prompts and frame type selection

## Changes

**ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx:**

1. Added new state for tracking primary reference image:
   ```typescript
   const [imageModalPrimaryRef, setImageModalPrimaryRef] = useState<string>("");
   ```

2. Modified `openImageModalForFrame` to set the primary reference when opening from a candidate image:
   ```typescript
   setImageModalPrimaryRef(normalizedPreset);
   ```

3. Updated `imageModalReferenceSections` useMemo to prepend the primary reference as a distinct section:
   ```typescript
   if (imageModalPrimaryRef) {
     return [
       { title: "首要参考图（点击的候选图）", images: [imageModalPrimaryRef] },
       ...sections,
     ];
   }
   ```

4. Added cleanup to reset primary ref state on modal close and successful submission

## Validation

1. Ran `npm run lint` in frontend - passed with only pre-existing warnings
2. Browser verification via Chrome DevTools MCP:
   - Navigated to storyboard page for script 62
   - Clicked "图生图" button on a candidate image
   - Modal opened showing "首要参考图（点击的候选图）" section at the top
   - Clicked candidate image displayed and pre-selected
   - Environment and character reference sections shown below
   - Prompt input and frame type checkboxes working correctly

## Next Steps

- None, feature is complete

## Linked Commits

- TBD (this commit)
