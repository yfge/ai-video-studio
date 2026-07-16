import type { ProductionCanvasNode } from "./productionCanvasModel";

export function isProductionCanvasReviewNode(node?: ProductionCanvasNode) {
  return [
    "image.candidates",
    "storyboard.candidates",
    "video.candidates",
  ].includes(node?.skill || "");
}

export function canBranchProductionCanvasCandidate(
  node: ProductionCanvasNode,
  allowed: boolean,
) {
  return (
    allowed &&
    node.skill !== "storyboard.candidates" &&
    node.outputs?.candidate_branching !== "disabled"
  );
}

export function canDirectlyPlaceProductionCanvasVideo(
  node: ProductionCanvasNode,
) {
  return (
    node.skill === "video.candidates" &&
    node.outputs?.placement_mode !== "explicit_node"
  );
}
