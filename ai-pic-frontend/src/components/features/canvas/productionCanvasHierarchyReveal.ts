import type { Story } from "@/utils/api/types";
import {
  loadHierarchyBranch,
  loadHierarchyRoots,
  loadHierarchyStories,
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
  return [...(story.story_characters || []), ...(story.characters || [])]
    .map((character) => character.virtual_ip_id)
    .filter((id): id is number => typeof id === "number");
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
  const rootResult = await loadHierarchyRoots();
  let graph = rootResult.graph;
  let stories: Story[] | null = null;
  let storiesWarning: string | null = null;
  const loadStories = async () => {
    if (stories) return stories;
    const result = await loadHierarchyStories();
    stories = result.items;
    storiesWarning = result.warning;
    return stories;
  };
  const expandedIds = new Set<string>();
  const loadedIds = new Set<string>();
  let targetNodeId: string | null = null;

  let virtualIpId = context.virtual_ip_id;
  if (!virtualIpId && context.story_id) {
    const story = (await loadStories()).find(
      (item) => item.id === context.story_id,
    );
    const visibleRootIds = new Set(
      graph.nodes
        .filter((node) => node.entityType === "ip")
        .map((node) => Number(node.entityId)),
    );
    virtualIpId = storyVirtualIpIds(story).find((id) => visibleRootIds.has(id));
  }

  const ipNode = nodeById(graph, virtualIpId ? `ip:${virtualIpId}` : undefined);
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
    const result = await loadHierarchyBranch(ipNode, loadStories);
    graph = mergeHierarchyGraphs(graph, result.branch);
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
      const result = await loadHierarchyBranch(storyNode, loadStories);
      graph = mergeHierarchyGraphs(graph, result.branch);
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
    warning:
      [rootResult.warning, storiesWarning].filter(Boolean).join("；") || null,
  };
}
