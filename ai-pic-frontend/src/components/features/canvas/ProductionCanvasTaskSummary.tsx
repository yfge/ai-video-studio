import { useEffect, useState } from "react";
import { StatusPill } from "@/components/shared";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { taskOutputNumber } from "./productionCanvasSkillNodes";
import {
  COLLAPSED_TASK_LIMIT,
  EXPANDED_TASK_LIMIT,
  type TaskSummaryFilter,
  taskExtra,
  taskStatus,
  taskStatusLabel,
  taskTitle,
} from "./productionCanvasTaskSummaryModel";

export function ProductionCanvasTaskSummary({
  nodes,
  onReturnFocus,
  onRefreshTasks,
  onSelectNode,
  refreshError,
  refreshingTasks,
}: {
  nodes: ProductionCanvasNode[];
  onReturnFocus?: () => void;
  onRefreshTasks?: (nodes: ProductionCanvasNode[]) => void;
  onSelectNode?: (nodeId: string) => void;
  refreshError?: string | null;
  refreshingTasks?: boolean;
}) {
  const [showAllTasks, setShowAllTasks] = useState(false);
  const [taskFilter, setTaskFilter] = useState<TaskSummaryFilter>("all");
  const taskNodes = nodes.filter(
    (node) => node.kind === "note" && taskOutputNumber(node.outputs),
  );
  useEffect(() => {
    if (!taskNodes.length) {
      setShowAllTasks(false);
      setTaskFilter("all");
    }
  }, [taskNodes.length]);
  if (!taskNodes.length) return null;

  const completedNodes = taskNodes.filter(
    (node) => taskStatus(node) === "completed",
  );
  const failedNodes = taskNodes.filter((node) =>
    ["failed", "cancelled", "blocked"].includes(taskStatus(node)),
  );
  const runningNodes = taskNodes.filter(
    (node) => !completedNodes.includes(node) && !failedNodes.includes(node),
  );
  const filteredTaskNodes =
    taskFilter === "running"
      ? runningNodes
      : taskFilter === "completed"
      ? completedNodes
      : taskFilter === "failed"
      ? failedNodes
      : taskNodes;
  const visibleTaskLimit = showAllTasks
    ? Math.min(filteredTaskNodes.length, EXPANDED_TASK_LIMIT)
    : COLLAPSED_TASK_LIMIT;
  const visibleTaskNodes = filteredTaskNodes
    .slice(-visibleTaskLimit)
    .slice()
    .reverse();
  const isTaskListCapped = filteredTaskNodes.length > EXPANDED_TASK_LIMIT;
  const isRefreshListCapped = taskNodes.length > EXPANDED_TASK_LIMIT;
  const hiddenTaskCount = Math.max(
    0,
    filteredTaskNodes.length - visibleTaskNodes.length,
  );
  const expandLabel = isTaskListCapped
    ? `展开最近 ${EXPANDED_TASK_LIMIT} 条任务`
    : "展开全部任务";
  const expandText = isTaskListCapped
    ? `展开最近 ${EXPANDED_TASK_LIMIT} 条`
    : `${expandLabel}（还有 ${hiddenTaskCount} 条）`;
  const refreshTaskNodes = isRefreshListCapped
    ? taskNodes.slice(-EXPANDED_TASK_LIMIT)
    : taskNodes;
  const refreshLabel = isRefreshListCapped ? "刷新最近任务" : "刷新全部任务";
  const refreshText = isRefreshListCapped ? "刷新最近" : "刷新全部";
  const filterButtonClass = (filter: TaskSummaryFilter) =>
    `rounded-md focus:outline-none focus:ring-2 focus:ring-blue-100 ${
      taskFilter === filter ? "ring-2 ring-blue-300 ring-offset-1" : ""
    }`;

  const renderJump = (
    label: string,
    count: number,
    tone: "amber" | "green" | "red",
    filter: TaskSummaryFilter,
    target?: ProductionCanvasNode,
  ) => {
    const pill = (
      <StatusPill tone={tone}>
        {label} {count}
      </StatusPill>
    );
    return (
      <button
        type="button"
        aria-label={
          target && onSelectNode ? `定位并筛选${label}任务` : `筛选${label}任务`
        }
        aria-pressed={taskFilter === filter}
        className={filterButtonClass(filter)}
        onClick={() => {
          setTaskFilter(filter);
          if (target && onSelectNode) onSelectNode(target.id);
          onReturnFocus?.();
        }}
      >
        {pill}
      </button>
    );
  };

  return (
    <div
      className="border-b border-gray-100 pb-3"
      data-canvas-task-summary="true"
      data-completed-tasks={completedNodes.length}
      data-failed-tasks={failedNodes.length}
      data-running-tasks={runningNodes.length}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold text-gray-950">任务证据</div>
        <div className="flex items-center gap-2">
          {onRefreshTasks ? (
            <button
              type="button"
              aria-label={refreshLabel}
              aria-busy={refreshingTasks || undefined}
              className="rounded-md px-2 py-1 text-[11px] font-medium text-blue-600 hover:bg-blue-50 disabled:text-gray-400"
              disabled={refreshingTasks}
              onClick={() => onRefreshTasks(refreshTaskNodes)}
            >
              {refreshingTasks ? "刷新中" : refreshText}
            </button>
          ) : null}
          <div className="text-[11px] text-gray-500">共 {taskNodes.length}</div>
        </div>
      </div>
      {refreshError ? (
        <div className="mt-2 text-[11px] leading-4 text-red-600" role="alert">
          {refreshError}
        </div>
      ) : null}
      <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
        <button
          type="button"
          aria-label="筛选全部任务"
          aria-pressed={taskFilter === "all"}
          className={filterButtonClass("all")}
          onClick={() => {
            setTaskFilter("all");
            onReturnFocus?.();
          }}
        >
          <StatusPill>全部 {taskNodes.length}</StatusPill>
        </button>
        {renderJump(
          "生成中",
          runningNodes.length,
          "amber",
          "running",
          runningNodes[runningNodes.length - 1],
        )}
        {renderJump(
          "已完成",
          completedNodes.length,
          "green",
          "completed",
          completedNodes[completedNodes.length - 1],
        )}
        {renderJump(
          "异常",
          failedNodes.length,
          "red",
          "failed",
          failedNodes[failedNodes.length - 1],
        )}
      </div>
      <div className="mt-2 space-y-1">
        {visibleTaskNodes.length ? (
          visibleTaskNodes.map((node) => {
            const taskId = taskOutputNumber(node.outputs);
            if (!taskId) return null;
            const href = node.actionHref || `/tasks?task_id=${taskId}`;
            const extra = taskExtra(node);
            return (
              <div key={node.id} className="flex items-center gap-1">
                <button
                  type="button"
                  aria-label={`定位任务 ${taskId}`}
                  className="min-w-0 flex-1 rounded-md bg-gray-50 px-2 py-1 text-left text-[11px] text-gray-600 hover:bg-blue-50 hover:text-blue-700"
                  onClick={() => onSelectNode?.(node.id)}
                >
                  <span className="block truncate">
                    Task #{taskId} · {taskStatusLabel(node)} · {taskTitle(node)}
                  </span>
                  {extra ? (
                    <span
                      className={`block truncate ${
                        extra.tone === "red" ? "text-red-600" : "text-gray-500"
                      }`}
                    >
                      {extra.label}
                    </span>
                  ) : null}
                </button>
                <a
                  href={href}
                  aria-label={`打开任务 ${taskId}`}
                  className="rounded-md px-2 py-1 text-[11px] font-medium text-blue-600 hover:bg-blue-50"
                >
                  打开
                </a>
              </div>
            );
          })
        ) : (
          <div className="rounded-md bg-gray-50 px-2 py-1 text-[11px] text-gray-500">
            暂无匹配任务
          </div>
        )}
      </div>
      {filteredTaskNodes.length > COLLAPSED_TASK_LIMIT ? (
        <button
          type="button"
          aria-label={showAllTasks ? "收起任务列表" : expandLabel}
          aria-expanded={showAllTasks}
          className="mt-2 text-[11px] font-medium text-blue-600 hover:text-blue-700"
          onClick={() => {
            setShowAllTasks((value) => !value);
            onReturnFocus?.();
          }}
        >
          {showAllTasks ? "收起任务列表" : expandText}
        </button>
      ) : null}
    </div>
  );
}
