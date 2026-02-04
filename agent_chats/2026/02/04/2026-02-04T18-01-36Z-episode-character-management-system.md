---
id: 2026-02-04T18-01-36Z-episode-character-management-system
date: 2026-02-04T18:01:36Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, api, database, model, service, episode, character, P0]
related_paths:
  - ai-pic-backend/app/models/episode_character.py
  - ai-pic-backend/app/models/__init__.py
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/app/schemas/episode_character.py
  - ai-pic-backend/app/services/episode_character_service.py
  - ai-pic-backend/app/services/voice_binding_service.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/characters.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/__init__.py
  - ai-pic-backend/alembic/versions/3a9af7b70877_add_episode_characters_table.py
  - ai-pic-backend/tests/unit/test_episode_character_service.py
summary: "Implemented Episode temporary character management system (P0 core functionality)"
---

## User Prompt

Implement the Episode temporary character management system according to the implementation plan. Focus on P0 core functionality:

1. Data layer (model + migration)
2. Schema layer (Pydantic schemas)
3. Service layer (resource resolution logic)
4. API layer (endpoints: POST, GET list, GET detail, DELETE)
5. Integration (voice binding service)
6. Unit tests

## Goals

- [x] Create EpisodeCharacter model with SoftDeleteBusinessMixin
- [x] Create Alembic migration for episode_characters table
- [x] Update Episode model to add episode_characters relationship
- [x] Create Pydantic schemas for Episode characters (Create, Update, Response, WithResources, List)
- [x] Implement episode_character_service with resource resolution logic
- [x] Create API endpoints for Episode character management
- [x] Integrate with voice_binding_service (add get_episode_character_map, get_combined_character_map)
- [x] Write comprehensive unit tests for service layer
- [x] Register character routes in episodes router

## Changes

### Data Layer (Model + Migration)

**Created `app/models/episode_character.py`** (~90 lines)
- Defined `EpisodeCharacter` model inheriting from `SoftDeleteBusinessMixin`
- Foreign keys: episode_id (CASCADE), virtual_ip_id (RESTRICT)
- Character metadata: character_name, role_type, importance
- Override fields: personality, background, appearance_override, voice_config_override
- Scene tracking: scene_appearances, first_appearance_scene, last_appearance_scene
- Relationships: episode, virtual_ip

**Updated `app/models/__init__.py`**
- Added EpisodeCharacter import and __all__ export

**Updated `app/models/script.py`**
- Added episode_characters relationship to Episode model

**Created Alembic migration `3a9af7b70877_add_episode_characters_table.py`**
- Creates episode_characters table with all fields
- Adds indexes: episode_id, virtual_ip_id, business_id (unique), is_deleted
- Foreign key constraints: episodes (CASCADE), virtual_ips (RESTRICT)
- Includes upgrade() and downgrade() functions

### Schema Layer

**Created `app/schemas/episode_character.py`** (~90 lines)
- `EpisodeCharacterBase`: Base schema with all optional fields
- `EpisodeCharacterCreate`: Requires virtual_ip_id
- `EpisodeCharacterUpdate`: All fields optional
- `EpisodeCharacterResponse`: Full model response
- `EpisodeCharacterWithResources`: Extended with resolved_voice_config, resolved_images, resolved_appearance_prompt, display_name
- `EpisodeCharacterListResponse`: Paginated list response

### Service Layer

**Created `app/services/episode_character_service.py`** (~120 lines)

Core functions:
- `resolve_character_resources(character, db)`: Resolves voice_config (override or VirtualIP default), images (sorted by is_default), appearance_prompt (merged), display_name
- `get_character_display_name(character, db)`: Priority order - character_name > VirtualIP.name > "临时角色{id}"
- `get_episode_characters(db, episode_id, page, page_size, include_deleted)`: Paginated list with sorting by importance and created_at

**Updated `app/services/voice_binding_service.py`** (+80 lines)
- Added EpisodeCharacter import
- `get_episode_character_map(db, episode_id)`: Maps normalized character names to VirtualIP for Episode characters, applies voice_config_override
- `get_combined_character_map(db, story_id, episode_id)`: Merges Story + Episode mappings with Episode priority

### API Layer

**Created `app/api/v1/endpoints/episodes/characters.py`** (~280 lines)

Endpoints:
- `POST /{episode_id}/characters`: Create episode character (validates VirtualIP access)
- `GET /{episode_id}/characters`: List characters (paginated, sorted by importance)
- `GET /{episode_id}/characters/{character_id}`: Get character details
- `GET /{episode_id}/characters/{character_id}/resources`: Get with resolved resources
- `PUT /{episode_id}/characters/{character_id}`: Update character (virtual_ip_id immutable)
- `DELETE /{episode_id}/characters/{character_id}`: Soft delete

All endpoints:
- Verify episode access via get_episode_by_identifier
- Support both integer ID and business_id lookup
- Enforce non-admin users can only use their own VirtualIPs
- Include proper error handling (404 for not found, 403 for permission denied)

**Updated `app/api/v1/endpoints/episodes/__init__.py`**
- Imported characters_router
- Added characters_router to combined router

### Testing

**Created `tests/unit/test_episode_character_service.py`** (~170 lines)

Test classes:
- `TestResolveCharacterResources`:
  - test_resolve_with_no_overrides
  - test_resolve_with_voice_override
  - test_resolve_with_appearance_override
  - test_resolve_with_images (tests sorting by is_default)
  - test_resolve_with_missing_virtual_ip
- `TestGetCharacterDisplayName`:
  - test_display_name_from_character_name
  - test_display_name_from_virtual_ip
  - test_display_name_fallback

All 8 tests pass ✓

## Validation

### Unit Tests
```bash
pytest tests/unit/test_episode_character_service.py -v
# Result: 8 passed, 33 warnings in 0.07s
```

**Tested scenarios:**
- Resource resolution with no overrides (uses VirtualIP defaults)
- Voice config override replaces VirtualIP default
- Appearance override merges with VirtualIP style_prompt
- Image sorting (is_default=True first, then by created_at)
- Fallback when VirtualIP is missing
- Display name priority: character_name > VirtualIP.name > "临时角色{id}"

### Database Migration

Migration file created: `3a9af7b70877_add_episode_characters_table.py`

**Note**: Migration was not executed during implementation because database is not running. User needs to run:
```bash
cd ai-pic-backend
alembic upgrade head
```

**Migration validation checklist** (for user to verify after running migration):
```bash
# Verify table structure
mysql -e "DESCRIBE episode_characters;"

# Check indexes
mysql -e "SHOW INDEX FROM episode_characters;"

# Verify foreign keys
mysql -e "SELECT * FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME='episode_characters';"
```

### API Endpoint Validation

**Manual testing steps** (requires running backend + database):
```bash
# 1. Create episode character
curl -X POST http://localhost:8000/api/v1/episodes/1/characters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "virtual_ip_id": 5,
    "character_name": "快递员",
    "role_type": "temporary",
    "importance": 2,
    "scene_appearances": [{"scene_number": 1, "role_in_scene": "配送包裹"}]
  }'

# 2. List characters
curl http://localhost:8000/api/v1/episodes/1/characters \
  -H "Authorization: Bearer $TOKEN"

# 3. Get character details
curl http://localhost:8000/api/v1/episodes/1/characters/1 \
  -H "Authorization: Bearer $TOKEN"

# 4. Get resolved resources
curl http://localhost:8000/api/v1/episodes/1/characters/1/resources \
  -H "Authorization: Bearer $TOKEN"

# 5. Update character
curl -X PUT http://localhost:8000/api/v1/episodes/1/characters/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"importance": 3}'

# 6. Soft delete
curl -X DELETE http://localhost:8000/api/v1/episodes/1/characters/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Code Review Checklist

Size compliance:
- [x] No Python file exceeds 300 lines
  - episode_character.py: ~90 lines
  - episode_character.py (schemas): ~90 lines
  - episode_character_service.py: ~120 lines
  - characters.py (API): ~280 lines
  - voice_binding_service.py additions: +80 lines
  - Migration: ~80 lines

Structure compliance:
- [x] Single responsibility: Each file has one clear purpose
- [x] No code duplication: Reused existing patterns (SoftDeleteBusinessMixin, get_episode_by_identifier)
- [x] Proper layering: API → Service → Model
- [x] No circular dependencies

Testing compliance:
- [x] Unit tests for service layer (8 tests, all passing)
- [x] Mock-based tests for isolation
- [x] Tests cover edge cases (missing VirtualIP, overrides, sorting)

Documentation compliance:
- [x] Docstrings added for all public functions
- [x] Type hints throughout
- [x] Implementation plan document preserved as reference

## Next Steps

### Immediate (User Action Required)

1. **Run database migration**:
   ```bash
   cd ai-pic-backend
   alembic upgrade head
   ```

2. **Verify migration**:
   ```bash
   mysql -e "DESCRIBE episode_characters;"
   mysql -e "SHOW INDEX FROM episode_characters;"
   ```

3. **Start backend and test API endpoints** (manual or via Chrome MCP):
   - Create episode character with valid VirtualIP
   - List characters (verify pagination)
   - Get character resources (verify voice_config_override works)
   - Update character
   - Soft delete character

### P1 Features (Next Implementation Phase)

1. **Script Agent Integration** (~50 lines)
   - Update `_validate_script_characters()` to include Episode characters
   - File: `app/services/script_agent.py`

2. **Script Character Policy Integration** (~50 lines)
   - Add `build_episode_alias_map()` function
   - Update `enforce_script_character_policy()`
   - File: `app/services/script/script_character_policy.py`

3. **Context Pack Integration** (~80 lines)
   - Add `build_episode_context_pack()` function
   - Implement budget allocation (50% Story main, 50% Episode temp)
   - File: `app/services/context_pack/story_context_pack_builder.py`

4. **Integration Tests** (~200 lines)
   - End-to-end API tests
   - Voice binding integration tests
   - Script generation with Episode characters
   - File: `tests/integration/api/test_episode_characters_api.py`

### P1.5 Features (Auto-Generation)

1. **Temporary Character Extraction** (~150 lines)
   - Extract character names from script dialogues
   - Parse stage directions for appearance
   - Track scene appearances
   - File: `app/services/script/temporary_character_extractor.py`

2. **AI Character Background Generator** (~120 lines)
   - Generate personality from dialogues
   - Generate background from context
   - Suggest appearance descriptions
   - File: `app/services/script/character_background_generator.py`

3. **Auto Character Creator** (~200 lines)
   - Detect unknown_names in script generation
   - Auto-create EpisodeCharacter records
   - Assign default VirtualIP
   - Return list of auto-created characters
   - File: `app/services/script/auto_character_creator.py`

4. **Script Agent Integration**
   - Hook into script generation flow
   - Add `auto_created_characters` to response
   - Notify user to review/customize

### Monitoring & Optimization

- Monitor query performance on episode_characters table (add EXPLAIN ANALYZE)
- Consider caching get_combined_character_map() results
- Add structured logging for character resolution failures
- Track usage metrics (most common temporary roles)

## Architectural Notes

### Design Decisions Recap

1. **VirtualIP Strong Binding**: All temporary characters must bind to VirtualIP for resource access. This ensures video generation has required assets (images, voice).

2. **Override Mechanism**: voice_config_override and appearance_override allow Episode-specific customization without duplicating VirtualIP resources.

3. **Priority Resolution**:
   - Voice: override > VirtualIP.voice_config
   - Appearance: merged (VirtualIP.style_prompt + appearance_override)
   - Display name: character_name > VirtualIP.name > fallback

4. **Conflict Handling**: Episode character names override Story character names in get_combined_character_map() (Episode context is more specific).

5. **Soft Delete**: Uses inherited SoftDeleteBusinessMixin for data retention and audit trail.

### Integration Points

1. **Voice Binding Service**: get_combined_character_map() provides unified character lookup for dialogue audio generation.

2. **Script Agent** (P1): _validate_script_characters() will check both Story and Episode characters.

3. **Context Pack** (P1): Budget allocation will balance Story main characters with Episode temporary roles.

4. **Script Generation** (P1.5): Auto-detection of unknown_names triggers automatic EpisodeCharacter creation.

### Future Considerations

- **Character Promotion**: Detect frequently-used Episode characters and suggest promoting to Story-level.
- **Cross-Episode Analysis**: Identify temporary characters appearing in multiple episodes.
- **Resource Optimization**: Share VirtualIPs across similar temporary roles (e.g., "快递员" template).
- **Bulk Operations**: Add bulk create/update endpoints for batch character management.

## Linked Commits

This work will be committed after user review and testing. Suggested commit message:

```
feat(backend): implement Episode temporary character management system

- Add EpisodeCharacter model with soft delete and business_id support
- Create Alembic migration for episode_characters table
- Add Pydantic schemas for character CRUD operations
- Implement resource resolution service (voice, images, appearance)
- Add API endpoints: POST, GET list, GET detail, PUT, DELETE
- Integrate with voice_binding_service for combined character maps
- Add comprehensive unit tests (8 tests, all passing)

Supports P0 core functionality for temporary character management
in episodes (delivery person, passerby, doctor, etc.).

Related: Episode临时角色管理系统设计方案
```

## Dependencies

- Requires database migration before API endpoints can be used
- VirtualIP records must exist before creating EpisodeCharacter
- Episodes must exist and be accessible by current user

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing flows | All integrations are optional (episode_id parameter defaults to None) |
| VirtualIP deletion orphans characters | RESTRICT foreign key prevents deletion; soft delete recommended |
| Performance impact | Indexes on episode_id, virtual_ip_id; joinedload for eager loading |
| Name conflict confusion | API returns clear source indicators (Story vs Episode) |

## Success Metrics

P0 Implementation:
- [x] Model and migration created
- [x] All schemas defined
- [x] Service layer functional
- [x] API endpoints implemented
- [x] Voice binding integration complete
- [x] Unit tests pass (8/8)
- [ ] Database migration executed (pending user)
- [ ] Manual API testing completed (pending user)
- [ ] Integration tests written (P1)

Code Quality:
- [x] All files under size limits
- [x] Single responsibility maintained
- [x] No code duplication
- [x] Proper type hints and docstrings
- [x] Test coverage for service layer

## References

- Implementation plan: Request message (Episode临时角色管理系统 - 实现方案)
- CLAUDE.md: Code Architecture & Quality Standards section
- Related design: docs/soft-delete-business-id.md
- Voice binding: app/services/voice_binding_service.py
- Context Pack: app/services/context_pack/
