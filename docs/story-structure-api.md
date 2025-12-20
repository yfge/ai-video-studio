# Story Structure (Normalized) API

This document describes the normalized story-structure endpoints. Legacy JSON fields still exist for compatibility; these routes are the current structured API surface.

Base prefix: `/api/v1/story-structure`

## Scenes
- GET `/scripts/{script_id}/scenes`
- GET `/scripts/{script_id}/structure` (scenes with beats + shots)
- POST `/scripts/{script_id}/scenes`
- PUT `/scenes/{scene_id}`
- DELETE `/scenes/{scene_id}`
- POST `/scripts/{script_id}/seed-from-json?dry_run=false`

## Beats
- GET `/scenes/{scene_id}/beats`
- POST `/scenes/{scene_id}/beats`
- PUT `/scene-beats/{beat_id}`
- DELETE `/scene-beats/{beat_id}`

## Shots
- GET `/scenes/{scene_id}/shots`
- POST `/scenes/{scene_id}/shots`
- PUT `/shots/{shot_id}`
- DELETE `/shots/{shot_id}`

## Treatments + Step Outlines
- GET `/stories/{story_id}/treatments?latest_only=true|false`
- POST `/stories/{story_id}/treatments`
- GET `/treatments/{treatment_id}/step-outlines`
- POST `/treatments/{treatment_id}/step-outlines`

## Environments
- GET `/environments`
- GET `/environments/{env_id}`
- POST `/environments`
- PUT `/environments/{env_id}`
- DELETE `/environments/{env_id}`

## Environment Images
- GET `/environments/{env_id}/images`
- POST `/environments/{env_id}/images/upload`
- DELETE `/environments/{env_id}/images?image_url=...`

## Environment Generation
- POST `/environments/{env_id}/images/generate`
- POST `/environments/{env_id}/images/generate-async`

## Environment Variants
- POST `/environments/{env_id}/images/variants`
- POST `/environments/{env_id}/images/variants-async`

Notes
- `env_id` accepts a numeric id or `business_id` (see `resolve_environment` in `app/services/story_structure_service.py`).
- Schemas live in `ai-pic-backend/app/schemas/story_structure.py`.
- Routers live in `ai-pic-backend/app/api/v1/endpoints/story_structure/`.
- Frontend client helpers: `ai-pic-frontend/src/utils/api.ts` (`storyStructureAPI`).
