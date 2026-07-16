import {
  episodeAPI,
  scriptAPI,
  storyAPI,
  timelineAPI,
  virtualIPAPI,
} from "@/utils/api/endpoints";
import type { Story } from "@/utils/api/types";
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
