import { useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasRunActionRequest } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";

export type ProductionCanvasRetryDefinition = "current" | "original";

const actionLabels = {
  run_ready: "已运行就绪节点",
  resume: "已继续未完成节点",
  cancel: "已取消活动任务",
  retry: "已重新提交节点",
} as const;

export function useProductionCanvasRunActions({
  onStateUpdated,
  runId,
  saveCanvas,
}: {
  onStateUpdated: (state: ProductionCanvasState) => void;
  runId: string;
  saveCanvas: () => Promise<boolean>;
}) {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const invoke = async (
    request: ProductionCanvasRunActionRequest,
    busyKey: string = request.action,
  ) => {
    const targetRunId = runId.trim();
    if (!targetRunId || busyAction) return false;
    setBusyAction(busyKey);
    setStatus(null);
    try {
      if (request.action !== "cancel" && !(await saveCanvas())) {
        setStatus("保存当前图定义失败，未执行 Run 操作");
        return false;
      }
      const response = await productionCanvasAPI.controlRun(
        targetRunId,
        request,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "Run 操作失败");
      }
      onStateUpdated(productionCanvasStateFromRun(response.data.run));
      const count = response.data.executions.length;
      setStatus(
        `${actionLabels[request.action]}${count ? ` · ${count} 个节点` : ""}`,
      );
      return true;
    } catch (cause) {
      setStatus(cause instanceof Error ? cause.message : String(cause));
      return false;
    } finally {
      setBusyAction(null);
    }
  };

  return {
    busyAction,
    cancel: () => invoke({ action: "cancel" }),
    resume: () => invoke({ action: "resume" }),
    retry: (
      node: ProductionCanvasNode,
      mode: ProductionCanvasRetryDefinition,
    ) =>
      invoke(
        { action: "retry", node_id: node.id, definition_mode: mode },
        `retry:${node.id}`,
      ),
    runReady: () => invoke({ action: "run_ready" }),
    status,
  };
}
