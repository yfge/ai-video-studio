---
id: 2025-12-20T00-30-00Z-frontend-types-split
date: 2025-12-20T00:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, refactor, typescript, phase2]
related_paths:
  - ai-pic-frontend/src/utils/api/types/index.ts
  - ai-pic-frontend/src/utils/api/types/common.types.ts
  - ai-pic-frontend/src/utils/api/types/user.types.ts
  - ai-pic-frontend/src/utils/api/types/task.types.ts
  - ai-pic-frontend/src/utils/api/types/image.types.ts
  - ai-pic-frontend/src/utils/api/types/style.types.ts
  - ai-pic-frontend/src/utils/api/types/voice.types.ts
  - ai-pic-frontend/src/utils/api/types/ai-model.types.ts
  - ai-pic-frontend/src/utils/api/types/virtual-ip.types.ts
  - ai-pic-frontend/src/utils/api/types/story.types.ts
  - ai-pic-frontend/src/utils/api/types/script.types.ts
  - ai-pic-frontend/src/utils/api/types/video.types.ts
  - ai-pic-frontend/src/utils/api/types/environment.types.ts
summary: "Split frontend api.ts types into domain-specific modules [phase2.3.1]"
---

## User Prompt

Continue executing refactoring plan Phase 2.3.1 - Split Frontend api.ts Types.

## Goals

1. Extract type definitions from monolithic api.ts (2,627 lines) into domain-specific modules
2. Organize types by domain: user, task, image, style, voice, ai-model, virtual-ip, story, script, video, environment
3. Create barrel export index.ts for clean imports
4. Maintain backward compatibility during transition

## Changes

### New Type Definition Files (12 files created)

1. **common.types.ts** (~50 lines)

   - `API_BASE_URL` constant
   - `ApiResponse<T>` generic interface
   - `PaginatedResponse<T>` interface
   - `SortDirection`, `FilterOperator` types

2. **user.types.ts** (~90 lines)

   - `User`, `AdminUser` interfaces
   - `UserListResponse` for pagination
   - `LoginRequest`, `LoginResponse` for auth
   - `RegisterRequest`, `RegisterResponse` for registration
   - `PasswordResetRequest`, `UserUpdateRequest`

3. **task.types.ts** (~50 lines)

   - `Task` interface with all task fields
   - `CreateTaskRequest` for task creation
   - Task status and type enums

4. **image.types.ts** (~90 lines)

   - `ImageItem` for gallery images
   - `VirtualIPImage` for character images
   - `AIImageGenerationRequest` for generation params
   - `AIImageGenerationResponse` for results

5. **style.types.ts** (~100 lines)

   - `StyleOption` for style selections
   - `StyleSpec` for detailed specifications
   - `StylePreset` for preset configurations
   - `StylePresetGroup` for grouping

6. **voice.types.ts** (~80 lines)

   - `VoiceOption` for voice selections
   - `VoiceConfig` for TTS configuration
   - `VoiceEnums` with emotion/speed/format options

7. **ai-model.types.ts** (~60 lines)

   - `AIModel` interface
   - `AIModelType` constant (image/video categories)
   - Provider-specific configurations

8. **virtual-ip.types.ts** (~95 lines)

   - `VirtualIP` main entity interface
   - `CreateVirtualIPRequest`, `UpdateVirtualIPRequest`
   - `VirtualIPAICreateRequest`, `VirtualIPAIGenerationRequest`
   - `VirtualIPAIGenerationResponse`, `VirtualIPAIGenerationDetailedResponse`

9. **story.types.ts** (~105 lines)

   - `Story`, `Episode` entity interfaces
   - `StoryCharacter` for character references
   - `StoryGenerationRequest`, `EpisodeGenerationRequest`

10. **script.types.ts** (~90 lines)

    - `Script` entity interface
    - `ScriptGenerationRequest`
    - `NormalizedScene`, `SceneBeat`, `NormalizedShot`

11. **video.types.ts** (~110 lines)

    - `StoryboardVideoGenerationOptions`
    - `StoryboardVideoGenerationMeta`
    - `StoryboardFrame`, `StoryboardMeta`
    - `StoryboardPlan`, `StoryboardPlanScene`, `StoryboardPlanFrame`
    - `StoryboardPayload`

12. **environment.types.ts** (~35 lines)
    - `Environment` entity interface
    - `EnvironmentCreate` request
    - `EnvironmentImagesResponse`

### Updated Files

- **index.ts**: Updated from temporary re-export to proper barrel export of all domain type files

## Validation

1. **TypeScript Compilation**: `npm run lint` passed with no errors
2. **Production Build**: `./docker/build_prod_images.sh` succeeded
3. **Type Coverage**: All major type definitions from api.ts extracted and organized

## Next Steps

1. Phase 2.3.2: Split Frontend API Endpoints into domain-specific endpoint files
2. Phase 2.3.3: Create API Index with re-exports
3. Update existing imports to use new type paths (gradual migration)

## Linked Commits

- To be linked after commit
