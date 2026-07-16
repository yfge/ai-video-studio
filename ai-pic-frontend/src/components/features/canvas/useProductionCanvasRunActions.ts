import { useEffect, useRef, useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasRunActionRequest } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

export type ProductionCanvasRetryDefinition = "current" | "original";

const actionLabels = {
  run_ready: "已运行就绪节点",
  resume: "已继续未完成节点",
  cancel: "已取消活动任务",
  retry: "已重新提交节点",
} as const;

export function useProductionCanvasRunActions({
  captureStateIdentity,
  onStateUpdated,
  runId,
  saveCanvas,
}: {
  captureStateIdentity: () => ProductionCanvasStateIdentity;
  onStateUpdated: (
    state: ProductionCanvasState,
    identity: ProductionCanvasStateIdentity,
  ) => boolean;
  runId: string;
  saveCanvas: () => Promise<boolean>;
}) {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const requestEpoch = useRef(0);

  useEffect(() => {
    requestEpoch.current += 1;
    setBusyAction(null);
    setStatus(null);
  }, [runId]);

  const invoke = async (
    request: ProductionCanvasRunActionRequest,
    busyKey: string = request.action,
  ) => {
    const targetRunId = runId.trim();
    if (!targetRunId || busyAction) return false;
    const initialIdentity = captureStateIdentity();
    if (initialIdentity.runId !== targetRunId) return false;
    const requestEpochValue = ++requestEpoch.current;
    setBusyAction(busyKey);
    setStatus(null);
    let stateIdentity = initialIdentity;
    try {
      if (request.action !== "cancel" && !(await saveCanvas())) {
        if (
          requestEpochValue === requestEpoch.current &&
          captureStateIdentity().runId === targetRunId
        ) {
          setStatus("保存当前图定义失败，未执行 Run 操作");
        }
        return false;
      }
      stateIdentity = captureStateIdentity();
      if (stateIdentity.runId !== targetRunId) return false;
      const response = await productionCanvasAPI.controlRun(
        targetRunId,
        request,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "Run 操作失败");
      }
      if (
        !onStateUpdated(
          productionCanvasStateFromRun(response.data.run),
          stateIdentity,
        )
      ) {
        return false;
      }
      if (requestEpochValue !== requestEpoch.current) return false;
      const count = response.data.executions.length;
      setStatus(
        `${actionLabels[request.action]}${count ? ` · ${count} 个节点` : ""}`,
      );
      return true;
    } catch (cause) {
      const currentIdentity = captureStateIdentity();
      if (
        requestEpochValue === requestEpoch.current &&
        currentIdentity.runId === stateIdentity.runId &&
        currentIdentity.epoch === stateIdentity.epoch
      ) {
        setStatus(cause instanceof Error ? cause.message : String(cause));
      }
      return false;
    } finally {
      if (requestEpochValue === requestEpoch.current) setBusyAction(null);
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
