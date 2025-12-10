---
id: 2025-12-10T12-55-00Z-prompt-yaml-metadata
date: 2025-12-10T12:55:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, prompts]
related_paths:
  - ai-pic-backend/app/prompts/templates/environment_image.yaml
  - ai-pic-backend/app/prompts/templates/episode_list.yaml
  - ai-pic-backend/app/prompts/templates/script_dialogues.yaml
  - ai-pic-backend/app/prompts/templates/script_scenes.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_generation.yaml
  - ai-pic-backend/app/prompts/templates/system_prompt_json_strict.yaml
  - ai-pic-backend/app/prompts/templates/system_prompt_script.yaml
  - ai-pic-backend/app/prompts/templates/system_prompt_story.yaml
summary: "Add YAML metadata for remaining prompt templates to align with PromptManager expectations."
---

## User Prompt

- “ai-pic-backend/app/prompts/templates 很多提示词没有yaml 补齐”

## Goals

- Provide YAML metadata for prompt templates that currently only have `.txt` files.
- Keep naming and variable definitions consistent with existing prompt YAML conventions.

## Changes

- Added YAML descriptors for environment image, episode list, script dialogues/scenes, storyboard generation, and system prompts.
- Documented variables (types/defaults/enums) and basic metadata (category, version, author, timestamps) for each template.

## Validation

- Not run (metadata-only additions; no code execution paths affected).

## Next Steps

- Run prompt rendering flows in a live environment to ensure new YAML metadata is picked up correctly.

## Linked Commits

- pending
