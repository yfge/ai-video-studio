import type { Story } from "@/utils/api/types";
import {
  loadHierarchyBranch,
  loadHierarchyContextIpBranch,
  loadHierarchyContextStoryBranch,
  loadHierarchyEpisode,
  loadHierarchyRoot,
  loadHierarchyStory,
} from "./productionCanvasHierarchyLoader";
import {
  mergeHierarchyGraphs,
  type HierarchyGraph,
  type HierarchyNode,
} from "./productionCanvasHierarchyModel";

export interface ProductionCanvasHierarchySyncContext {
  virtual_ip_id?: number;
  environment_id?: number;
  story_id?: number;
  episode_id?: number;
  script_id?: number;
  timeline_id?: number;
  timeline_version?: number;
  clip_id?: string;
  task_id?: number;
}

export interface ProductionCanvasHierarchySyncRequest {
  revision: number;
  context: ProductionCanvasHierarchySyncContext;
}

export interface ProductionCanvasHierarchyRevealResult {
  expandedIds: Set<string>;
  graph: HierarchyGraph;
  loadedIds: Set<string>;
  targetNodeId: string | null;
  warning: string | null;
}

function storyVirtualIpIds(story: Story | undefined) {
  if (!story) return [];
  return [
    ...new Set(
      [...(story.story_characters || []), ...(story.characters || [])]
        .map((character) => character.virtual_ip_id)
        .filter((id): id is number => typeof id === "number"),
    ),
  ];
}

function nodeById(graph: HierarchyGraph, id: string | undefined) {
  return id ? graph.nodes.find((node) => node.id === id) : undefined;
}

function firstNode(
  graph: HierarchyGraph,
  predicate: (node: HierarchyNode) => boolean,
) {
  return graph.nodes
    .filter(predicate)
    .sort((left, right) => left.laneOrder - right.laneOrder)[0];
}

/** Reload the truthful entity projection and reveal the deepest known result. */
export async function revealProductionCanvasHierarchy(
  context: ProductionCanvasHierarchySyncContext,
): Promise<ProductionCanvasHierarchyRevealResult> {
  const hasDomainContext = Object.entries(context).some(
    ([key, value]) => key !== "task_id" && value !== undefined,
  );
  if (!hasDomainContext) {
    return {
      expandedIds: new Set(),
      graph: { edges: [], nodes: [] },
      loadedIds: new Set(),
      targetNodeId: null,
      warning: null,
    };
  }
  const story = context.story_id
    ? await loadHierarchyStory(context.story_id)
    : undefined;
  const storyIpIds = storyVirtualIpIds(story);
  const virtualIpId =
    context.virtual_ip_id ||
    (storyIpIds.length === 1 ? storyIpIds[0] : undefined);
  let graph: HierarchyGraph;
  let rootWarning: string | null = null;
  if (virtualIpId) {
    const rootResult = await loadHierarchyRoot(virtualIpId);
    graph = rootResult.graph;
    rootWarning = rootResult.warning;
  } else {
    return {
      expandedIds: new Set(),
      graph: { edges: [], nodes: [] },
      loadedIds: new Set(),
      targetNodeId: null,
      warning: "Prompt 尚未解析到唯一 IP，因此未展开资产仓库。",
    };
  }
  const loadStories = async () => (story ? [story] : []);
  const expandedIds = new Set<string>();
  const loadedIds = new Set<string>();
  let targetNodeId: string | null = null;

  const ipNode = virtualIpId ? nodeById(graph, `ip:${virtualIpId}`) : undefined;
  if (ipNode) targetNodeId = ipNode.id;
  const needsIpBranch = Boolean(
    context.environment_id ||
      context.story_id ||
      context.episode_id ||
      context.script_id ||
      context.timeline_id ||
      context.clip_id,
  );
  if (ipNode && needsIpBranch) {
    const branch = await loadHierarchyContextIpBranch(
      ipNode,
      story,
      context.environment_id,
    );
    graph = mergeHierarchyGraphs(graph, branch);
    expandedIds.add(ipNode.id);
    loadedIds.add(ipNode.id);
  }

  const environmentNode = nodeById(
    graph,
    context.environment_id
      ? `environment:${context.environment_id}`
      : undefined,
  );
  if (environmentNode) targetNodeId = environmentNode.id;

  const storyNode = nodeById(
    graph,
    context.story_id ? `story:${context.story_id}` : undefined,
  );
  if (storyNode) {
    targetNodeId = storyNode.id;
    if (
      context.episode_id ||
      context.script_id ||
      context.timeline_id ||
      context.clip_id
    ) {
      const episode = context.episode_id
        ? await loadHierarchyEpisode(context.episode_id)
        : null;
      if (episode) {
        graph = mergeHierarchyGraphs(
          graph,
          loadHierarchyContextStoryBranch(Number(storyNode.entityId), episode),
        );
      }
      expandedIds.add(storyNode.id);
      loadedIds.add(storyNode.id);
    }
  }

  const episodeNode = nodeById(
    graph,
    context.episode_id ? `episode:${context.episode_id}` : undefined,
  );
  if (episodeNode) {
    targetNodeId = episodeNode.id;
    if (context.script_id || context.timeline_id || context.clip_id) {
      const result = await loadHierarchyBranch(episodeNode, loadStories, {
        script_id: context.script_id,
        timeline_id: context.timeline_id,
        timeline_version: context.timeline_version,
      });
      graph = mergeHierarchyGraphs(graph, result.branch);
      expandedIds.add(episodeNode.id);
      loadedIds.add(episodeNode.id);
    }
  }

  const storyboardNode = context.clip_id
    ? nodeById(
        graph,
        context.episode_id
          ? `storyboard:${context.episode_id}:${context.clip_id}`
          : undefined,
      )
    : firstNode(
        graph,
        (node) =>
          node.entityType === "storyboard" &&
          !node.empty &&
          (!context.timeline_id || node.timelineId === context.timeline_id) &&
          (!context.timeline_version ||
            node.timelineVersion === context.timeline_version) &&
          (!context.script_id || node.scriptId === context.script_id),
      );
  if (storyboardNode) {
    targetNodeId = storyboardNode.id;
    if (context.clip_id) {
      const result = await loadHierarchyBranch(storyboardNode, loadStories);
      graph = mergeHierarchyGraphs(graph, result.branch);
      expandedIds.add(storyboardNode.id);
      loadedIds.add(storyboardNode.id);
      const videoNode = firstNode(
        graph,
        (node) =>
          node.entityType === "video" &&
          node.parentIds.includes(storyboardNode.id),
      );
      if (videoNode) targetNodeId = videoNode.id;
    }
  }

  return {
    expandedIds,
    graph,
    loadedIds,
    targetNodeId,
    warning: rootWarning,
  };
}
