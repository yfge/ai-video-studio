import {
  episodeAPI,
  scriptAPI,
  storyAPI,
  timelineAPI,
  virtualIPAPI,
} from "@/utils/api/endpoints";
import type { Episode, Story } from "@/utils/api/types";
import {
  buildHierarchyRoots,
  buildIpHierarchyBranch,
  buildStoryHierarchyBranch,
  type HierarchyGraph,
  type HierarchyNode,
} from "./productionCanvasHierarchyModel";
import {
  currentHierarchyTimelines,
  type HierarchyTimelineSelection,
} from "./productionCanvasHierarchyData";
import {
  buildEpisodeHierarchyBranch,
  buildStoryboardVideoBranch,
} from "./productionCanvasHierarchyTimeline";

function responseData<T>(
  response: { success: boolean; data?: T; error?: string },
  fallback: string,
) {
  if (!response.success || response.data === undefined) {
    throw new Error(response.error || fallback);
  }
  return response.data;
}

export async function loadHierarchyRoots() {
  const response = await virtualIPAPI.getVirtualIPs({ limit: 100 });
  const items = responseData(response, "IP 列表加载失败");
  return {
    graph: buildHierarchyRoots(items),
    warning:
      items.length >= 100
        ? "当前仅加载前 100 个 IP；更大账号需要服务端游标。"
        : null,
  };
}

export async function loadHierarchyRoot(virtualIpId: number) {
  const response = await virtualIPAPI.getVirtualIP(virtualIpId);
  return {
    graph: buildHierarchyRoots([responseData(response, "IP 加载失败")]),
    warning: null,
  };
}

export async function loadHierarchyStories() {
  const response = await storyAPI.getStories({ limit: 100 });
  const items = responseData(response, "故事列表加载失败");
  return {
    items,
    warning:
      items.length >= 100
        ? "故事按前 100 条匹配 IP；大账号可能存在未展示故事。"
        : null,
  };
}

export async function loadHierarchyStory(storyId: number) {
  return responseData(await storyAPI.getStory(storyId), "故事加载失败");
}

export async function loadHierarchyEpisode(episodeId: number) {
  return responseData(await episodeAPI.getEpisode(episodeId), "剧集加载失败");
}

export async function loadHierarchyContextIpBranch(
  node: HierarchyNode,
  story?: Story,
  environmentId?: number,
) {
  const environmentResponse = environmentId
    ? await virtualIPAPI.listVirtualIPEnvironments(Number(node.entityId))
    : null;
  const links = environmentResponse
    ? responseData(environmentResponse, "IP 环境加载失败").filter(
        (link) => link.environment.id === environmentId,
      )
    : [];
  const branch = buildIpHierarchyBranch(
    Number(node.entityId),
    links,
    story ? [story] : [],
  );
  const requestedTypes = new Set([
    ...(environmentId ? ["environment"] : []),
    ...(story ? ["story"] : []),
  ]);
  const nodes = branch.nodes.filter(
    (item) => !item.empty || requestedTypes.has(item.entityType),
  );
  const nodeIds = new Set(nodes.map((item) => item.id));
  return {
    nodes,
    edges: branch.edges.filter((item) => nodeIds.has(item.to)),
  };
}

export function loadHierarchyContextStoryBranch(
  storyId: number,
  episode: Episode,
) {
  return buildStoryHierarchyBranch(storyId, [episode]);
}

async function loadIpBranch(
  node: HierarchyNode,
  loadStories: () => Promise<Story[]>,
) {
  const ipId = Number(node.entityId);
  const [environmentResponse, stories] = await Promise.all([
    virtualIPAPI.listVirtualIPEnvironments(ipId),
    loadStories(),
  ]);
  return buildIpHierarchyBranch(
    ipId,
    responseData(environmentResponse, "IP 环境加载失败"),
    stories,
  );
}

async function loadStoryBranch(node: HierarchyNode) {
  const storyId = Number(node.entityId);
  const response = await episodeAPI.getStoryEpisodes(storyId);
  return buildStoryHierarchyBranch(
    storyId,
    responseData(response, "故事剧集加载失败"),
  );
}

async function loadEpisodeBranch(
  node: HierarchyNode,
  selection?: HierarchyTimelineSelection,
) {
  const episodeId = Number(node.entityId);
  const [timelineResponse, scriptResponse] = await Promise.all([
    timelineAPI.listEpisodeTimelines(episodeId),
    scriptAPI.getEpisodeScripts(episodeId),
  ]);
  return buildEpisodeHierarchyBranch(
    episodeId,
    currentHierarchyTimelines(
      responseData(timelineResponse, "剧集 Timeline 加载失败").items,
      responseData(scriptResponse, "剧本版本加载失败"),
      selection,
    ),
  );
}

async function loadStoryboardBranch(node: HierarchyNode) {
  if (!node.timelineId || !node.timelineVersion || !node.clipId) {
    throw new Error("分镜缺少稳定 Timeline 标识");
  }
  const [assetResponse, taskResponse] = await Promise.all([
    timelineAPI.listTimelineClipAssets(node.timelineId, {
      timelineVersion: node.timelineVersion,
      clipId: node.clipId,
    }),
    timelineAPI.listTimelineClipTasks(node.timelineId),
  ]);
  return {
    branch: buildStoryboardVideoBranch(
      node,
      responseData(assetResponse, "分镜视频资产加载失败").items,
      taskResponse.success && taskResponse.data ? taskResponse.data.items : [],
    ),
    warning:
      taskResponse.success || !taskResponse.error
        ? null
        : `生成状态未加载：${taskResponse.error}`,
  };
}

export async function loadHierarchyBranch(
  node: HierarchyNode,
  loadStories: () => Promise<Story[]>,
  timelineSelection?: HierarchyTimelineSelection,
): Promise<{ branch: HierarchyGraph; warning: string | null }> {
  if (node.entityType === "ip") {
    return { branch: await loadIpBranch(node, loadStories), warning: null };
  }
  if (node.entityType === "story") {
    return { branch: await loadStoryBranch(node), warning: null };
  }
  if (node.entityType === "episode") {
    return {
      branch: await loadEpisodeBranch(node, timelineSelection),
      warning: null,
    };
  }
  if (node.entityType === "storyboard") {
    return loadStoryboardBranch(node);
  }
  return { branch: { edges: [], nodes: [] }, warning: null };
}
