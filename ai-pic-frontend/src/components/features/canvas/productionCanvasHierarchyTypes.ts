export type HierarchyEntityType =
  | "ip"
  | "environment"
  | "story"
  | "episode"
  | "storyboard"
  | "video";

export type HierarchyNodeStatus = "ready" | "generating" | "missing";

export type HierarchyRelationType =
  | "resource"
  | "participation"
  | "containment"
  | "production"
  | "reference"
  | "empty";

export interface HierarchyNode {
  id: string;
  entityType: HierarchyEntityType;
  entityId: number | string;
  businessId?: string;
  title: string;
  detail: string;
  status: HierarchyNodeStatus;
  parentIds: string[];
  expandable: boolean;
  empty?: boolean;
  actionHref?: string;
  timelineId?: number;
  timelineVersion?: number;
  episodeId?: number;
  scriptId?: number;
  clipId?: string;
  assetLinkId?: number;
  videoUrl?: string;
  laneOrder: number;
}

export interface HierarchyEdge {
  id: string;
  from: string;
  to: string;
  relationType: HierarchyRelationType;
  label: string;
  contextId?: string;
}

export interface HierarchyGraph {
  nodes: HierarchyNode[];
  edges: HierarchyEdge[];
}

export interface PositionedHierarchyNode extends HierarchyNode {
  x: number;
  y: number;
  width: number;
  height: number;
  hiddenDescendantCount: number;
}

export interface HierarchyProjection {
  nodes: PositionedHierarchyNode[];
  edges: HierarchyEdge[];
}

export interface HierarchyContextPatch {
  virtual_ip_id?: number;
  environment_id?: number;
  story_id?: number;
  episode_id?: number;
  script_id?: number;
  timeline_id?: number;
  timeline_version?: number;
  clip_id?: string;
}

export const HIERARCHY_COLUMNS: ReadonlyArray<{
  entityType: HierarchyEntityType;
  label: string;
  x: number;
}> = [
  { entityType: "ip", label: "IP", x: 40 },
  { entityType: "environment", label: "环境", x: 320 },
  { entityType: "story", label: "故事", x: 600 },
  { entityType: "episode", label: "剧集", x: 880 },
  { entityType: "storyboard", label: "分镜", x: 1160 },
  { entityType: "video", label: "视频", x: 1440 },
];

export const HIERARCHY_COLUMN_X = Object.fromEntries(
  HIERARCHY_COLUMNS.map((column) => [column.entityType, column.x]),
) as Record<HierarchyEntityType, number>;
