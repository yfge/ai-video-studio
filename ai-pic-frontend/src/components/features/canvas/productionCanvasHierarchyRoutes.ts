import { episodeWorkspaceHref } from "@/utils/routes";
import type { HierarchyNode } from "./productionCanvasHierarchyModel";

function episodeIdForNode(node: HierarchyNode) {
  if (node.episodeId) return node.episodeId;
  if (node.entityType === "episode") return node.entityId;
  if (node.entityType === "storyboard" || node.entityType === "video") {
    return String(node.entityId).split(":", 1)[0];
  }
  return null;
}

export function hierarchyNodeActionHref(node: HierarchyNode) {
  const key = node.businessId || node.entityId;
  if (node.entityType === "ip") return `/virtual-ip/${key}`;
  if (node.entityType === "environment") return `/environments/${key}`;
  if (node.entityType === "story") return `/stories/${key}`;
  const episodeId = episodeIdForNode(node);
  if (!episodeId) return node.actionHref;
  return episodeWorkspaceHref(episodeId, {
    tab: "timeline",
    scriptId: node.scriptId,
    extraParams: node.clipId ? { clipId: node.clipId } : undefined,
  });
}
