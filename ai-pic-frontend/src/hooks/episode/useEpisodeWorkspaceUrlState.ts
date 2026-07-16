"use client";

import { useMemo } from "react";
import { coerceWorkspaceTab } from "./workspaceTabUtils";

type SearchParamsLike = {
  get: (key: string) => string | null;
};

export function useEpisodeWorkspaceUrlState(searchParams: SearchParamsLike) {
  const initialTab = coerceWorkspaceTab(searchParams.get("tab"));
  const urlScriptId = useMemo(() => {
    const raw = searchParams.get("scriptId");
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }, [searchParams]);
  const initialSelectedClipId = searchParams.get("clipId")?.trim() || null;
  const initialScriptTaskId = useMemo(() => {
    const raw = searchParams.get("taskId");
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  }, [searchParams]);

  return {
    initialTab,
    urlScriptId,
    initialSelectedClipId,
    initialScriptTaskId,
  };
}
