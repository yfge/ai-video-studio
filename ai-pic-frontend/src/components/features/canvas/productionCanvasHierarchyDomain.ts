import type {
  Episode,
  Story,
  TimelineResponse,
  VirtualIP,
  VirtualIPEnvironmentLink,
} from "@/utils/api/types";
import type {
  HierarchyEdge,
  HierarchyEntityType,
  HierarchyGraph,
  HierarchyNode,
} from "./productionCanvasHierarchyTypes";
import {
  episodeHierarchyDetail,
  episodeHierarchyTypeLabel,
  storyHierarchyDetail,
  storyHierarchyTypeLabel,
} from "./productionCanvasSingleVideoHierarchy";
const nodeId = (type: HierarchyEntityType, id: number | string) =>
  `${type}:${id}`;
const edge = (
  from: string,
  to: string,
  relationType: HierarchyEdge["relationType"],
  label: string,
  contextId?: string,
): HierarchyEdge => ({
  id: `${relationType}:${from}->${to}${contextId ? `@${contextId}` : ""}`,
  from,
  to,
  relationType,
  label,
  contextId,
});
export function buildHierarchyRoots(ips: VirtualIP[]): HierarchyGraph {
  return {
    nodes: ips.map((ip, laneOrder) => ({
      id: nodeId("ip", ip.id),
      entityType: "ip",
      entityId: ip.id,
      businessId: ip.business_id,
      title: ip.name,
      detail: ip.description || ip.tags.join(" · ") || "IP 资产",
      status: ip.is_active ? "ready" : "missing",
      parentIds: [],
      expandable: true,
      laneOrder,
    })),
    edges: [],
  };
}

export function buildIpHierarchyBranch(
  ipId: number,
  links: VirtualIPEnvironmentLink[],
  stories: Story[],
): HierarchyGraph {
  const parent = nodeId("ip", ipId);
  const environments = uniqueBy(
    [...links]
      .sort((a, b) => a.sort_order - b.sort_order)
      .map((link) => link.environment),
  );
  const participatingStories = uniqueBy(
    stories.filter((story) =>
      [...(story.story_characters || []), ...(story.characters || [])].some(
        (character) => character.virtual_ip_id === ipId,
      ),
    ),
  );
  const envNodes = environments.map((environment, laneOrder) =>
    domainNode(
      "environment",
      environment.id,
      environment.name,
      environment.description || "可复用环境",
      parent,
      laneOrder,
      false,
      environment.business_id,
    ),
  );
  const storyNodes = participatingStories.map((story, laneOrder) =>
    domainNode(
      "story",
      story.id,
      story.title,
      storyHierarchyDetail(story),
      parent,
      laneOrder,
      true,
      story.business_id,
      storyHierarchyTypeLabel(story),
    ),
  );
  const envChildren = envNodes.length
    ? envNodes
    : [emptyNode(parent, "environment")];
  const storyChildren = storyNodes.length
    ? storyNodes
    : [emptyNode(parent, "story")];
  const nodes = [...envChildren, ...storyChildren];
  const edges = [
    ...envChildren.map((node) =>
      edge(
        parent,
        node.id,
        node.empty ? "empty" : "resource",
        node.empty ? "暂无数据" : "环境资源",
      ),
    ),
    ...storyChildren.map((node) =>
      edge(
        parent,
        node.id,
        node.empty ? "empty" : "participation",
        node.empty ? "暂无数据" : "参与故事",
      ),
    ),
  ];
  return { nodes, edges };
}

export function buildStoryHierarchyBranch(
  storyId: number,
  episodes: Episode[],
): HierarchyGraph {
  const parent = nodeId("story", storyId);
  const children = uniqueBy(
    episodes.filter((episode) => episode.story_id === storyId),
  ).map((episode, laneOrder) =>
    domainNode(
      "episode",
      episode.id,
      episode.title,
      episodeHierarchyDetail(episode),
      parent,
      laneOrder,
      true,
      episode.business_id,
      episodeHierarchyTypeLabel(episode),
    ),
  );
  if (!children.length) return emptyBranch(parent, "episode");
  return {
    nodes: children,
    edges: children.map((node) =>
      edge(parent, node.id, "containment", "包含剧集"),
    ),
  };
}

export function mergeHierarchyGraphs(
  ...graphs: HierarchyGraph[]
): HierarchyGraph {
  const nodes = new Map<string, HierarchyNode>();
  const edges = new Map<string, HierarchyEdge>();
  graphs.forEach((graph) => {
    graph.nodes.forEach((node) => {
      const current = nodes.get(node.id);
      nodes.set(
        node.id,
        current
          ? {
              ...node,
              laneOrder: Math.min(current.laneOrder, node.laneOrder),
              parentIds: [
                ...new Set([...current.parentIds, ...node.parentIds]),
              ],
            }
          : node,
      );
    });
    graph.edges.forEach((item) => edges.set(item.id, item));
  });
  return { nodes: [...nodes.values()], edges: [...edges.values()] };
}

export function selectLatestTimeline(timelines: TimelineResponse[]) {
  return (
    [...timelines].sort((a, b) => b.version - a.version || b.id - a.id)[0] ??
    null
  );
}

function domainNode(
  type: HierarchyEntityType,
  id: number | string,
  title: string,
  detail: string,
  parent: string,
  laneOrder: number,
  expandable: boolean,
  businessId?: string,
  displayTypeLabel?: string,
): HierarchyNode {
  return {
    id: nodeId(type, id),
    entityType: type,
    entityId: id,
    businessId,
    displayTypeLabel,
    title,
    detail,
    status: "ready",
    parentIds: [parent],
    expandable,
    laneOrder,
  };
}

function emptyNode(parent: string, type: HierarchyEntityType): HierarchyNode {
  return {
    ...domainNode(
      type,
      `empty:${parent}`,
      `暂无${typeLabel(type)}`,
      "展开后仍无数据",
      parent,
      Number.MAX_SAFE_INTEGER,
      false,
    ),
    empty: true,
    status: "missing",
  };
}

function emptyBranch(
  parent: string,
  type: HierarchyEntityType,
): HierarchyGraph {
  const node = emptyNode(parent, type);
  return { nodes: [node], edges: [edge(parent, node.id, "empty", "暂无数据")] };
}

function uniqueBy<T extends { id: number }>(items: T[]) {
  return [...new Map(items.map((item) => [item.id, item])).values()];
}

function typeLabel(type: HierarchyEntityType) {
  return {
    ip: "IP",
    environment: "环境",
    story: "故事",
    episode: "剧集",
    storyboard: "分镜",
    video: "视频",
  }[type];
}
