import { StatusPill } from "@/components/shared";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  outputNumber,
  outputString,
  productionCanvasTaskStatusLabel,
} from "./productionCanvasSkillNodes";

const failedStatuses = new Set(["blocked", "cancelled", "failed"]);

function videoTaskId(node: ProductionCanvasNode) {
  return (
    outputNumber(node.outputs, "task_id") ??
    outputNumber(node.outputs, "dispatched_task_id")
  );
}

export function ProductionCanvasVideoTaskStatus({
  node,
}: {
  node?: ProductionCanvasNode;
}) {
  if (node?.skill !== "video.candidates") return null;
  const taskId = videoTaskId(node);
  const status = outputString(node.outputs, "task_status");
  if (!taskId || !status) return null;

  const failed = failedStatuses.has(status) || node.status === "blocked";
  const error = failed
    ? outputString(node.outputs, "task_error_message")
    : undefined;
  const progress = failed
    ? undefined
    : outputString(node.outputs, "task_progress_detail");

  return (
    <section
      aria-label="视频生成任务状态"
      className="border-t border-gray-100 pt-3"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold text-gray-700">
          视频任务 #{taskId}
        </div>
        <StatusPill
          tone={failed ? "red" : status === "completed" ? "green" : "amber"}
        >
          {productionCanvasTaskStatusLabel(status)}
        </StatusPill>
      </div>
      {error || progress ? (
        <p
          className={`mt-2 text-xs leading-5 ${
            error ? "text-red-600" : "text-gray-500"
          }`}
        >
          {error ? `错误：${error}` : `进度：${progress}`}
        </p>
      ) : null}
    </section>
  );
}
