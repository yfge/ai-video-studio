export type EpisodeWorkspaceTab =
  | "overview"
  | "script"
  | "timeline"
  | "storyboard"
  | "characters";

type EpisodeWorkspaceHrefOptions = {
  tab?: EpisodeWorkspaceTab;
  scriptId?: string | number | null;
  autoTimelinePipeline?: string | number | boolean | null;
  action?: string | null;
  extraParams?: Record<string, string | number | boolean | null | undefined>;
};

export function episodeWorkspaceHref(
  episodeKey: string | number,
  options: EpisodeWorkspaceHrefOptions = {},
): string {
  const params = new URLSearchParams();
  params.set("tab", options.tab ?? "timeline");

  if (options.scriptId !== undefined && options.scriptId !== null) {
    params.set("scriptId", String(options.scriptId));
  }

  if (
    options.autoTimelinePipeline !== undefined &&
    options.autoTimelinePipeline !== null &&
    options.autoTimelinePipeline !== false
  ) {
    params.set(
      "autoTimelinePipeline",
      options.autoTimelinePipeline === true
        ? String(Date.now())
        : String(options.autoTimelinePipeline),
    );
  }

  if (options.action) {
    params.set("action", options.action);
  }

  if (options.extraParams) {
    Object.entries(options.extraParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.set(key, String(value));
      }
    });
  }

  return `/episodes/${episodeKey}/workspace?${params.toString()}`;
}
