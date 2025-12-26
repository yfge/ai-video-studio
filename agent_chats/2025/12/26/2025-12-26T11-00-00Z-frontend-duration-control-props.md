---
id: 2025-12-26T11-00-00Z-frontend-duration-control-props
date: 2025-12-26T11:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, duration-control, bugfix]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
summary: "Fixed TypeScript build error by adding useDurationControl props to AudioTimelineSection"
---

## User Prompt

Continue from previous session that was fixing frontend TypeScript build error. The `AudioTimelineSection` component requires `useDurationControl` and `setUseDurationControl` props that were not being passed.

## Goals

1. Add `useDurationControl` state to `useEpisodeDetail` hook
2. Destructure it in `page.tsx`
3. Pass the props to `AudioTimelineSection` component
4. Verify Docker build succeeds

## Changes

### 1. useEpisodeDetail.ts - Added useDurationControl state

**`ai-pic-frontend/src/hooks/useEpisodeDetail.ts` (line 90, 352-353)**:

```typescript
const [useDurationControl, setUseDurationControl] = useState(false);

// ... in return object:
useDurationControl,
setUseDurationControl,
```

### 2. page.tsx - Destructure and pass props

**`ai-pic-frontend/src/app/episodes/[id]/page.tsx` (lines 58-59, 278-279)**:

Added destructuring:
```typescript
useDurationControl,
setUseDurationControl,
```

Passed to AudioTimelineSection:
```typescript
<AudioTimelineSection
  ...
  useDurationControl={useDurationControl}
  setUseDurationControl={setUseDurationControl}
  ...
/>
```

## Validation

1. **Lint Check**: `npm run lint` passes with only warnings (no errors)
2. **Docker Build**: `./docker/build_prod_images.sh` completed successfully
   - Backend: `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:d0a5ee7`
   - Frontend: `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-frontend:d0a5ee7`

## Next Steps

1. User's major request: Refactor script generation agent with time as priority
   - Consider scene duration from scene planning stage
   - Calculate dialogue vs non-dialogue time budgets
   - Add REACT validation after dialogue generation
2. Deploy new Docker images and verify in browser

## Linked Commits

- (pending) fix(frontend): add useDurationControl props to AudioTimelineSection
