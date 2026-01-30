---
id: 2025-12-20T01-00-00Z-frontend-endpoints-split
date: 2025-12-20T01:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, refactor, typescript, phase2]
related_paths:
  - ai-pic-frontend/src/utils/api/endpoints/index.ts
  - ai-pic-frontend/src/utils/api/endpoints/auth.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/admin.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/task.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/image.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/voice.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/episode.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/ai.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/style.endpoints.ts
  - ai-pic-frontend/src/utils/api/index.ts
  - ai-pic-frontend/src/utils/api/types/image.types.ts
summary: "Split frontend API endpoints into domain-specific modules [phase2.3.2]"
---

## User Prompt

Continue executing refactoring plan Phase 2.3.2 - Split Frontend API Endpoints.

## Goals

1. Extract API endpoint functions from monolithic api.ts ApiClient class into domain-specific modules
2. Use the new httpClient function from client.ts instead of class-based approach
3. Organize endpoints by domain: auth, admin, task, image, voice, virtual-ip, story, episode, script, etc.
4. Create barrel export index.ts for clean imports
5. Maintain backward compatibility with legacy apiClient

## Changes

### New Endpoint Files (14 files created)

1. **auth.endpoints.ts** (~70 lines)

   - `login`, `register`, `logout`, `getCurrentUser`
   - `authAPI` namespace

2. **admin.endpoints.ts** (~180 lines)

   - User management: `getUsers`, `getUser`, `approveUser`, `updateUserRole`
   - User actions: `suspendUser`, `reactivateUser`, `deleteUser`
   - Stats and logs: `getUserStats`, `getUserAuditLogs`
   - `adminAPI` namespace

3. **task.endpoints.ts** (~75 lines)

   - `getTasks`, `createTask`, `getTask`, `deleteTask`, `startTask`
   - `taskAPI` namespace

4. **image.endpoints.ts** (~60 lines)

   - `getImages`, `getImage`, `deleteImage`, `uploadImage`
   - `imageAPI` namespace

5. **voice.endpoints.ts** (~65 lines)

   - `getVoiceEnums`, `getVoices`, `previewVoice`
   - `voiceAPI` namespace

6. **virtual-ip.endpoints.ts** (~120 lines)

   - CRUD: `getVirtualIPs`, `getVirtualIP`, `createVirtualIP`, `updateVirtualIP`, `deleteVirtualIP`
   - AI generation: `generateAIContent`, `generateAIContentDetailed`, `createVirtualIPWithAI`
   - `virtualIPAPI` namespace

7. **virtual-ip-image.endpoints.ts** (~220 lines)

   - Image management: `getVirtualIPImages`, `getVirtualIPImage`, `uploadVirtualIPImage`, `deleteVirtualIPImage`
   - AI generation: `generateVirtualIPImage`, `generateVirtualIPImageAsync`
   - Variants: `generateVariantFromImage`, `generateVariantAndSave`, `generateVariantAndSaveAsync`
   - `virtualIPImageAPI` namespace

8. **story.endpoints.ts** (~115 lines)

   - `getStories`, `getStory`, `generateStory`, `generateStoryAsync`
   - `updateStory`, `deleteStory`, `getStoryCharacters`, `getStoryGenres`
   - `storyAPI` namespace

9. **episode.endpoints.ts** (~120 lines)

   - `getEpisodes`, `getEpisode`, `generateEpisodes`, `generateEpisodesAsync`
   - `updateEpisode`, `deleteEpisode`, `getStoryEpisodes`, `regenerateEpisode`
   - `episodeAPI` namespace

10. **script.endpoints.ts** (~300 lines)

    - Script CRUD: `getScripts`, `getScript`, `generateScript`, `updateScript`, `deleteScript`
    - Audio: `generateSceneDialogueAudioAsync`, `generateAudioTimelineAsync`
    - Storyboard: `getStoryboard`, `generateStoryboard`, `generateStoryboardAsync`, `generateStoryboardVideo`, `generateStoryboardImages`, `updateStoryboard`
    - `scriptAPI` namespace

11. **story-structure.endpoints.ts** (~320 lines)

    - Scenes: `getNormalizedScenes`, `createScene`, `updateScene`, `deleteScene`
    - Beats: `getNormalizedSceneBeats`, `createSceneBeat`, `updateSceneBeat`, `deleteSceneBeat`
    - Shots: `getNormalizedSceneShots`, `createSceneShot`, `updateSceneShot`, `deleteSceneShot`
    - Environments: `listEnvironments`, `getEnvironment`, `createEnvironment`, `updateEnvironment`, `deleteEnvironment`
    - Environment images: `listEnvironmentImages`, `uploadEnvironmentImage`, `generateEnvironmentImages`, etc.
    - `storyStructureAPI` namespace

12. **ai.endpoints.ts** (~25 lines)

    - `getAvailableModels`
    - `aiAPI` namespace

13. **style.endpoints.ts** (~45 lines)

    - `getStyleSchema`, `listStylePresets`, `getStylePreset`
    - `styleAPI` namespace

14. **index.ts** - Barrel export for all endpoint modules

### Updated Files

- **api/index.ts**: Updated to export from endpoints and only re-export `apiClient` from legacy api.ts
- **types/image.types.ts**: Fixed `AIImageGenerationRequest` and `ImageToImageRequestPayload` to match original api.ts

## Validation

1. **TypeScript Compilation**: `npm run lint` passed with no errors
2. **Production Build**: `./docker/build_prod_images.sh` succeeded
3. **Type Fixes**: Corrected `model` field (was `model_id`) in AIImageGenerationRequest

## Next Steps

1. Gradually migrate existing components to use new endpoint imports
2. Consider deprecating legacy apiClient once migration is complete
3. Add unit tests for new endpoint modules

## Linked Commits

- To be linked after commit
