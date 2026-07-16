import { buildStoryboardClipManagementItems } from "@/components/features/episode/WorkspaceStoryboardClipManagementModel";
import type {
  TimelineClipAssetResponse,
  TimelineClipTaskItem,
  TimelineResponse,
} from "@/utils/api/types";
import {
  selectLatestTimeline,
  type HierarchyEdge,
  type HierarchyGraph,
  type HierarchyNode,
} from "./productionCanvasHierarchyModel";

function productionEdge(
  from: string,
  to: string,
  label: string,
): HierarchyEdge {
  return {
    id: `production:${from}->${to}`,
    from,
    to,
    relationType: "production",
    label,
  };
}

function emptyNode(
  parent: HierarchyNode | { id: string },
  entityType: "storyboard" | "video",
  title: string,
  status: "generating" | "missing" = "missing",
): HierarchyNode {
  return {
    id: `${entityType}:empty:${parent.id}`,
    entityType,
    entityId: `empty:${parent.id}`,
    title,
    detail:
      status === "generating" ? "已有生成任务正在执行" : "当前版本没有绑定资产",
    status,
    parentIds: [parent.id],
    expandable: false,
    empty: true,
    laneOrder: Number.MAX_SAFE_INTEGER,
  };
}

export function buildEpisodeHierarchyBranch(
  episodeId: number,
  timelines: TimelineResponse[],
): HierarchyGraph {
  const parent = `episode:${episodeId}`;
  const timeline = selectLatestTimeline(
    timelines.filter((item) => item.episode_id === episodeId),
  );
  if (!timeline) {
    const node = emptyNode({ id: parent }, "storyboard", "暂无 Timeline 分镜");
    return {
      nodes: [node],
      edges: [productionEdge(parent, node.id, "暂无数据")],
    };
  }
  const items = buildStoryboardClipManagementItems(timeline, null, []);
  if (!items.length) {
    const node = emptyNode({ id: parent }, "storyboard", "暂无视频分镜");
    return {
      nodes: [node],
      edges: [productionEdge(parent, node.id, "暂无数据")],
    };
  }
  const nodes = items.map<HierarchyNode>((item, laneOrder) => ({
    id: `storyboard:${episodeId}:${item.clipId}`,
    entityType: "storyboard",
    entityId: `${episodeId}:${item.clipId}`,
    title: item.label,
    detail: [item.sceneLabel, item.timeLabel].filter(Boolean).join(" · "),
    status: "ready",
    parentIds: [parent],
    expandable: true,
    timelineId: timeline.id,
    timelineVersion: timeline.version,
    episodeId,
    scriptId: timeline.script_id,
    clipId: item.clipId,
    laneOrder,
  }));
  return {
    nodes,
    edges: nodes.map((node) =>
      productionEdge(parent, node.id, "Timeline 分镜"),
    ),
  };
}

function currentVideoAssets(
  node: HierarchyNode,
  assets: TimelineClipAssetResponse[],
) {
  const matching = assets.filter(
    (asset) =>
      asset.timeline_id === node.timelineId &&
      asset.timeline_version === node.timelineVersion &&
      asset.clip_id === node.clipId &&
      (asset.media_asset?.asset_type === "video" ||
        asset.asset_role.includes("video") ||
        asset.asset_role === "render_output"),
  );
  return [
    ...new Map(matching.map((asset) => [asset.media_asset_id, asset])).values(),
  ];
}

function assetVideoUrl(asset: TimelineClipAssetResponse) {
  return (
    asset.media_asset?.file_url || asset.media_asset?.file_path || undefined
  );
}

export function buildStoryboardVideoBranch(
  storyboard: HierarchyNode,
  assets: TimelineClipAssetResponse[],
  tasks: TimelineClipTaskItem[] = [],
): HierarchyGraph {
  const matching = currentVideoAssets(storyboard, assets);
  if (!matching.length) {
    const generating = tasks.some((task) => task.clip_id === storyboard.clipId);
    const node = emptyNode(
      storyboard,
      "video",
      generating ? "视频生成中" : "暂无当前版本视频",
      generating ? "generating" : "missing",
    );
    return {
      nodes: [node],
      edges: [productionEdge(storyboard.id, node.id, "当前版本无资产")],
    };
  }
  const nodes = matching.map<HierarchyNode>((asset, laneOrder) => {
    const url = assetVideoUrl(asset);
    return {
      id: `video:${asset.id}`,
      entityType: "video",
      entityId: asset.media_asset_id,
      businessId: asset.media_asset?.business_id,
      title: `视频资产 #${asset.media_asset_id}`,
      detail: [asset.asset_role, asset.source].filter(Boolean).join(" · "),
      status: url ? "ready" : "missing",
      parentIds: [storyboard.id],
      expandable: false,
      timelineId: storyboard.timelineId,
      timelineVersion: storyboard.timelineVersion,
      episodeId: storyboard.episodeId,
      scriptId: storyboard.scriptId,
      clipId: storyboard.clipId,
      assetLinkId: asset.id,
      videoUrl: url,
      laneOrder,
    };
  });
  return {
    nodes,
    edges: nodes.map((node) =>
      productionEdge(storyboard.id, node.id, "绑定视频资产"),
    ),
  };
}
