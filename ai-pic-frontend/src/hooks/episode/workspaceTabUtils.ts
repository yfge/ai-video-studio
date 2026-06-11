import type { TabKey } from "./useEpisodeWorkspaceController";

const WORKSPACE_TABS = [
  "overview",
  "script",
  "timeline",
  "storyboard",
  "characters",
] as const;

export function coerceWorkspaceTab(value: string | null): TabKey {
  return WORKSPACE_TABS.includes(value as TabKey)
    ? (value as TabKey)
    : "timeline";
}
