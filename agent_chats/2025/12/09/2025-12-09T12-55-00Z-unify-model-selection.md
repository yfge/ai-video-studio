---
id: 2025-12-09T12-55-00Z-unify-model-selection
date: 2025-12-09T12:55:00Z
participants: [human, antigravity]
models: [gemini-2.0-flash-exp]
tags: [frontend, model-selection, cleanup]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/components/MultiModelSelector.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/hooks/useAvailableModels.ts
summary: "Unified frontend model selection logic to strictly differentiate between text and image generation models using `AIModelType` constants."
---

## User Prompt
"Unify Model Selection" / "Unify all model selection parts... Ensure correct differentiation between text generation models and image generation models."

## Goals
1.  Eliminate ambiguity in model selection (e.g., prevent "text" matching "text_to_image").
2.  Ensure `/stories` page only displays text generation models.
3.  Ensure `/tasks` page only displays image generation models.
4.  Standardize `modelType` usage across the frontend using strict constants.

## Changes
-   **`ai-pic-frontend/src/utils/api.ts`**: Introduced `AIModelType` constant object to mirror backend `AIModelType` enum values (e.g., `Text: 'text_generation'`, `Image: 'text_to_image'`).
-   **`ai-pic-frontend/src/components/MultiModelSelector.tsx`**:
    -   Refactored filtering logic to use strict equality (`===`) when filtering by type.
    -   Added support for `AIModelType` constants while maintaining backward compatibility for string literals via mapping.
    -   Fixed missing `providers` logic and unused imports.
-   **`ai-pic-frontend/src/app/stories/page.tsx`**: Updated to pass `modelType={AIModelType.Text}` to `MultiModelSelector`.
-   **`ai-pic-frontend/src/app/tasks/page.tsx`**: Updated to pass `modelType={AIModelType.Image}` to `MultiModelSelector`.
-   **`ai-pic-frontend/src/hooks/useAvailableModels.ts`**: Updated default `modelType` to `AIModelType.Text`.

## Validation
-   **Analysis**: Verified backend `list_models` supports exact type filtering.
-   **Browser Verification**:
    -   Logged into `http://localhost:8089/stories`, opened "AI Story Generation", and verified ONLY text models (like `gpt-4o`) were visible.
    -   Logged into `http://localhost:8089/tasks`, opened "Create Task", and verified ONLY image models (like `dall-e-3`) were visible.
-   **Results**: Confirmed correct isolation of model types.

## Next Steps
-   Consider enforcing strict `AIModelType` on the backend API input schema (currently accepts string alias).
