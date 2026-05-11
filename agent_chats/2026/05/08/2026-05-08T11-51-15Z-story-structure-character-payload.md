## User Prompt

生成的剧本 场景是为空的

## Goals

- Diagnose why the generated script appeared to have empty scenes in the operator UI.
- Fix the smallest backend issue blocking normalized scene structure loading.
- Verify the existing generated script `131` returns scenes and beats correctly.

## Changes

- Updated `SceneBeatCreate`, `SceneBeatResponse`, and `SceneBeatUpdate` to accept `characters_involved` as either an object or a list.
- Added a focused regression test that creates a scene beat with `characters_involved: ["林"]` and verifies `/story-structure/scripts/{script_id}/structure` returns it successfully.

## Validation

- Confirmed `/api/v1/scripts/131` returned 4 raw script scenes.
- Confirmed `/api/v1/story-structure/scripts/131/scenes` returned 4 normalized scenes.
- Reproduced `/api/v1/story-structure/scripts/131/structure` returning 500 before the fix because `SceneBeatResponse.characters_involved` rejected list values.
- Confirmed after the fix:
  - `/api/v1/story-structure/scripts/131/structure` returns 200.
  - `/api/v1/story-structure/scenes/572/beats` returns 200 with `characters_involved: ["林"]`.
- Ran `cd ai-pic-backend && pytest tests/test_story_structure_character_payloads.py -q --no-cov`.
- Ran `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/schemas/story_structure.py ai-pic-backend/tests/test_story_structure_character_payloads.py`.
- Ran `git diff --check`.
- Did not run `pre-commit run --all-files` or `./docker/build_prod_images.sh`; this was a focused backend schema/test regression commit and the repo has known broad pre-commit/build cost for narrow fixes.

## Next Steps

- If the current browser tab still shows an empty scene area, refresh the episode/script page so the frontend refetches the now-working structure endpoint.

## Linked Commits

- This commit.
