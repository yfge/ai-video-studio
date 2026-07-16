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
  root: (id: number) => `/api/v1/virtual-ips/${id}`,
  environments: "/api/v1/virtual-ips/1/environments",
  secondEnvironments: "/api/v1/virtual-ips/2/environments",
  stories: "/api/v1/stories?limit=100",
  story: (id: number) => `/api/v1/stories/${id}`,
  episodes: "/api/v1/episodes/story/10",
  episode: (id: number) => `/api/v1/episodes/${id}`,
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
    [hierarchyPaths.root(1), { success: true, data: virtualIPs[0] }],
    [hierarchyPaths.root(2), { success: true, data: virtualIPs[1] }],
    [hierarchyPaths.environments, environmentLinks],
    [hierarchyPaths.secondEnvironments, []],
    [hierarchyPaths.stories, stories],
    [hierarchyPaths.story(10), { success: true, data: stories[0] }],
    [
      hierarchyPaths.story(30),
      {
        success: true,
        data: {
          id: 30,
          business_id: "story-30",
          title: "三分钟产品视频",
          genre: "single_video",
          duration_minutes: 3,
          default_aspect_ratio: "16:9",
          status: "draft",
          is_public: false,
          story_characters: [],
          extra_metadata: { creation_mode: "single_video" },
          created_at: "2026-07-16T00:00:00Z",
          updated_at: "2026-07-16T00:00:00Z",
        },
      },
    ],
    [hierarchyPaths.episodes, episodes],
    [hierarchyPaths.episode(100), { success: true, data: episodes[0] }],
    [
      hierarchyPaths.episode(300),
      {
        success: true,
        data: {
          id: 300,
          business_id: "episode-300",
          story_id: 30,
          episode_number: 1,
          title: "三分钟产品视频",
          duration_minutes: 3,
          aspect_ratio: "16:9",
          status: "draft",
          extra_metadata: { creation_mode: "single_video" },
          created_at: "2026-07-16T00:00:00Z",
          updated_at: "2026-07-16T00:00:00Z",
        },
      },
    ],
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
