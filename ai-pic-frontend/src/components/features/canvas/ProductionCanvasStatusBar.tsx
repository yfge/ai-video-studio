import type { ProductionCanvasNode } from "./productionCanvasModel";

const finishedStatuses = new Set(["ready", "review", "approved"]);

export function ProductionCanvasStatusBar({
  executingNodeId,
  nodes,
  status,
}: {
  executingNodeId?: string | null;
  nodes: ProductionCanvasNode[];
  status?: string | null;
}) {
  const productionNodes = nodes.filter((node) => node.kind !== "note");
  const hasError = /失败|错误|阻塞/.test(status || "");
  const finished = productionNodes.filter((node) =>
    finishedStatuses.has(node.status),
  ).length;
  return (
    <div className="flex min-h-10 flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-1 pt-3 text-[13px] text-slate-500">
      <span className="inline-flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${
            hasError
              ? "bg-red-500"
              : executingNodeId
              ? "animate-pulse bg-blue-500"
              : "bg-emerald-500"
          }`}
          aria-hidden="true"
        />
        {executingNodeId ? "运行中" : "画布就绪"} · {finished}/
        {productionNodes.length}
      </span>
      <span aria-live="polite">
        {status ? `状态：${status}` : "自动保存已开启"}
      </span>
    </div>
  );
}
