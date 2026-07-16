import type { ProductionCanvasNode } from "./productionCanvasModel";

function outputString(node: ProductionCanvasNode, key: string) {
  const value = node.outputs?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function outputNumber(node: ProductionCanvasNode, key: string) {
  const value = node.outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function mediaType(url: string, node: ProductionCanvasNode) {
  if (
    node.skill?.includes("image") ||
    /\.(avif|gif|jpe?g|png|webp)(?:[?#]|$)/i.test(url)
  ) {
    return "image" as const;
  }
  return "video" as const;
}

function progressPercent(node: ProductionCanvasNode, text?: string) {
  const explicit = outputNumber(node, "render_progress");
  if (explicit !== undefined) return Math.max(0, Math.min(100, explicit));
  const matched = text?.match(/(\d{1,3})(?:\.\d+)?\s*%/);
  if (!matched) return undefined;
  return Math.max(0, Math.min(100, Number(matched[1])));
}

export function productionCanvasNodePreview(node: ProductionCanvasNode) {
  const text =
    outputString(node, "task_progress_detail") ||
    outputString(node, "task_description") ||
    outputString(node, "task_prompt") ||
    outputString(node, "prompt") ||
    node.detail?.trim() ||
    undefined;
  const mediaUrl =
    node.selectedOutputUrl || outputString(node, "output_url") || undefined;
  return {
    mediaType: mediaUrl ? mediaType(mediaUrl, node) : undefined,
    mediaUrl,
    progress: progressPercent(node, text),
    text,
  };
}
