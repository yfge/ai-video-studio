---
id: 2025-12-26T13-00-00Z-script-selection-url-persistence
date: 2025-12-26T13:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [frontend, episode-workspace, url-state]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
summary: "Fix script selection persistence across tab switches via URL params"
---

## User Prompt

User reported: "分镜 还是不对 http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=storyboard"

Translation: "The storyboard is still not correct"

## Goals

1. Persist selected script ID in URL when switching tabs
2. Restore script selection from URL on page load
3. Ensure storyboard tab shows data for the selected script version

## Changes

### workspace/page.tsx

**Root Cause**: When switching tabs, the URL only contained the `tab` parameter. The `selectedScriptId` state was managed by `useEpisodeDetail` hook which defaults to the first script, causing selection to reset.

**Fix**: Added URL-based state persistence for script selection.

1. Read initial scriptId from URL query params:

```tsx
const urlScriptId = searchParams.get("scriptId");
const initialScriptId = urlScriptId ? Number(urlScriptId) : null;
```

2. Sync URL scriptId to hook state when scripts load:

```tsx
useEffect(() => {
  if (!scripts || scripts.length === 0) return;
  if (initialScriptId && scripts.some((s) => s.id === initialScriptId)) {
    if (selectedScriptId !== initialScriptId) {
      setSelectedScriptId(initialScriptId);
    }
  }
}, [scripts, initialScriptId, selectedScriptId, setSelectedScriptId]);
```

3. Build URL with both tab and scriptId params:

```tsx
const buildUrl = useCallback(
  (tab: TabKey, scriptId: number | null) => {
    const params = new URLSearchParams();
    params.set("tab", tab);
    if (scriptId) {
      params.set("scriptId", String(scriptId));
    }
    return `/episodes/${episodeKey}/workspace?${params.toString()}`;
  },
  [episodeKey],
);
```

4. Update handleTabChange to preserve scriptId:

```tsx
const handleTabChange = useCallback(
  (tab: TabKey) => {
    setActiveTab(tab);
    router.replace(buildUrl(tab, selectedScriptId), { scroll: false });
  },
  [router, buildUrl, selectedScriptId],
);
```

5. Add handleScriptChange to update both state and URL:

```tsx
const handleScriptChange = useCallback(
  (scriptId: number | null) => {
    setSelectedScriptId(scriptId);
    router.replace(buildUrl(activeTab, scriptId), { scroll: false });
  },
  [setSelectedScriptId, router, buildUrl, activeTab],
);
```

## Validation

1. Browser test at `/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=storyboard`
2. Selected v1.1 script (ID 45) - URL updated to `?tab=storyboard&scriptId=45`
3. Switched to timeline tab - URL preserved as `?tab=timeline&scriptId=45`
4. Script v1.1 remained selected across tab switches
5. Storyboard showed correct data: 29 frames (v1.1) vs 21 frames (v1.0)
6. Timeline showed correct data: 41 beats, 4/4 scene audio for v1.1

## Next Steps

1. Test page refresh to confirm URL state restoration works
2. Consider adding script version indicator to tab headers

## Linked Commits

- c8ab257 fix(frontend): persist script selection in URL across tab switches
