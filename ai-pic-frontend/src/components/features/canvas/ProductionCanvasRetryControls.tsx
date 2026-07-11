import { useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { outputString } from "./productionCanvasSkillNodes";
import type { ProductionCanvasRetryDefinition } from "./useProductionCanvasRunActions";

const failedStatuses = new Set(["cancelled", "failed", "stale"]);

export function ProductionCanvasRetryControls({
  node,
  onRetry,
  retrying,
  runId,
}: {
  node?: ProductionCanvasNode;
  onRetry?: (
    node: ProductionCanvasNode,
    mode: ProductionCanvasRetryDefinition,
  ) => void;
  retrying?: boolean;
  runId: string;
}) {
  const [mode, setMode] = useState<ProductionCanvasRetryDefinition>("current");
  const taskStatus = outputString(node?.outputs, "task_status");
  const retryable = Boolean(
    node &&
      (failedStatuses.has(node.status) ||
        (taskStatus && failedStatuses.has(taskStatus))),
  );
  if (!node || !runId || !onRetry || !retryable) return null;
  const label = node.skill === "video.candidates" ? "重试视频生成" : "重试节点";
  return (
    <section aria-label="节点恢复" className="border-t border-gray-100 pt-3">
      <label className="block text-[11px] font-semibold text-gray-600">
        重试定义
        <select
          aria-label="重试定义"
          className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800"
          value={mode}
          onChange={(event) =>
            setMode(
              event.currentTarget.value as ProductionCanvasRetryDefinition,
            )
          }
        >
          <option value="current">当前保存定义</option>
          <option value="original">失败时原始定义</option>
        </select>
      </label>
      <button
        type="button"
        aria-busy={retrying || undefined}
        className={operatorButtonClass("primary", "mt-2 w-full")}
        disabled={retrying}
        onClick={() => onRetry(node, mode)}
      >
        {retrying ? "重新提交中" : label}
      </button>
    </section>
  );
}
