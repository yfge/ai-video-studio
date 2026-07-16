type FetchInput = Parameters<typeof fetch>[0];

import {
  assetsByClip,
  clipTasks,
  environmentLinks,
  episodes,
  scripts,
  stories,
  timelines,
  virtualIPs,
} from "./productionCanvasHierarchyFixtureData";

export const hierarchyPaths = {
  roots: "/api/v1/virtual-ips/?limit=100",
  environments: "/api/v1/virtual-ips/1/environments",
  secondEnvironments: "/api/v1/virtual-ips/2/environments",
  stories: "/api/v1/stories?limit=100",
  episodes: "/api/v1/episodes/story/10",
  scripts: "/api/v1/scripts/episode/100",
  timelines: "/api/v1/episodes/100/timelines",
  clipAssets: (clipId: string) =>
    `/api/v1/timelines/501/clip-assets?timeline_version=7&clip_id=${clipId}`,
  clipTasks: "/api/v1/timelines/501/clip-tasks",
} as const;

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function requestPath(input: FetchInput) {
  const value =
    typeof input === "string" || input instanceof URL
      ? String(input)
      : input.url;
  const url = new URL(value, "http://localhost");
  return `${url.pathname}${url.search}`;
}

export function installHierarchyFetch(
  options: { deferFirstEnvironments?: boolean } = {},
) {
  const originalFetch = globalThis.fetch;
  const requests: string[] = [];
  const responses = new Map<string, unknown>([
    [hierarchyPaths.roots, virtualIPs],
    [hierarchyPaths.environments, environmentLinks],
    [hierarchyPaths.secondEnvironments, []],
    [hierarchyPaths.stories, stories],
    [hierarchyPaths.episodes, episodes],
    [hierarchyPaths.scripts, scripts],
    [hierarchyPaths.timelines, { items: timelines }],
    [hierarchyPaths.clipTasks, clipTasks],
    ...Object.entries(assetsByClip).map(
      ([clipId, items]) =>
        [hierarchyPaths.clipAssets(clipId), { items }] as const,
    ),
  ]);
  let deferredEnvironmentResolve: ((response: Response) => void) | null = null;
  let environmentsDeferred = false;
  globalThis.fetch = ((input: FetchInput) => {
    const path = requestPath(input);
    requests.push(path);
    if (
      options.deferFirstEnvironments &&
      path === hierarchyPaths.environments &&
      !environmentsDeferred
    ) {
      environmentsDeferred = true;
      return new Promise<Response>((resolve) => {
        deferredEnvironmentResolve = resolve;
      });
    }
    return Promise.resolve(
      responses.has(path)
        ? json(responses.get(path))
        : json({ detail: `unexpected request: ${path}` }, 404),
    );
  }) as typeof fetch;
  const resolveDeferredEnvironments = () => {
    if (!deferredEnvironmentResolve) {
      throw new Error("environment request is not pending");
    }
    deferredEnvironmentResolve(json(environmentLinks));
    deferredEnvironmentResolve = null;
  };
  return {
    count: (path: string) => requests.filter((item) => item === path).length,
    requests,
    resolveDeferredEnvironments,
    restore: () => {
      if (deferredEnvironmentResolve) {
        deferredEnvironmentResolve(json(environmentLinks));
      }
      globalThis.fetch = originalFetch;
    },
  };
}
