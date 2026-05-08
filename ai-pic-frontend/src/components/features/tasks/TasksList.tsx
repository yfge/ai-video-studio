"use client";

import type { Task as APITask } from "@/utils/api/types";
import {
  StatusPill,
  operatorButtonClass,
  taskStatusTone,
} from "@/components/shared";

import { TASK_TYPE_LABELS } from "./taskTypeOptions";
import { TaskDetails } from "./TaskDetails";
import type { PersistedStyleInfo } from "./utils";

type TasksListProps = {
  tasks: APITask[];
  loading: boolean;
  fetchError: string | null;
  expanded: Record<number, boolean>;
  onToggleExpanded: (task: APITask) => void;
  persistedStyle: Record<number, PersistedStyleInfo>;
  persistedLoading: Record<number, boolean>;
  isStartingId: number | null;
  deletingTaskId: number | null;
  onStart: (taskId: number) => void;
  onDelete: (taskId: number) => void;
};

const getStatusText = (status: APITask["status"]) => {
  switch (status) {
    case "pending":
      return "等待中";
    case "processing":
      return "生成中";
    case "completed":
      return "已完成";
    case "failed":
      return "失败";
    default:
      return "未知";
  }
};

const formatTaskType = (taskType?: string) => {
  if (!taskType) return "—";
  return TASK_TYPE_LABELS[taskType]
    ? `${TASK_TYPE_LABELS[taskType]}（${taskType}）`
    : taskType;
};

export function TasksList({
  tasks,
  loading,
  fetchError,
  expanded,
  onToggleExpanded,
  persistedStyle,
  persistedLoading,
  isStartingId,
  deletingTaskId,
  onStart,
  onDelete,
}: TasksListProps) {
  if (!loading && !fetchError && tasks.length === 0) {
    return <div className="p-6 text-sm text-gray-500">暂无任务。</div>;
  }

  return (
    <div className="divide-y divide-gray-100">
      {tasks.map((task) => (
        <div key={task.id} className="px-4 py-3">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex items-center gap-2">
                <h3 className="truncate text-sm font-medium text-gray-950">
                  {task.title}
                </h3>
                <StatusPill tone={taskStatusTone(task.status)}>
                  {getStatusText(task.status)}
                </StatusPill>
              </div>
              {task.progress_detail && (
                <p className="mb-2 text-xs text-gray-700">
                  进度：
                  <span className="text-gray-800">{task.progress_detail}</span>
                </p>
              )}
              {task.prompt && (
                <p className="mb-3 line-clamp-2 text-xs text-gray-600">
                  {task.prompt}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                <span>
                  创建时间：
                  {task.created_at
                    ? new Date(task.created_at).toLocaleString()
                    : "未知"}
                </span>
                {task.updated_at && (
                  <span>
                    更新时间：{new Date(task.updated_at).toLocaleString()}
                  </span>
                )}
                {task.description && <span>描述：{task.description}</span>}
                {task.task_type && (
                  <span>类型：{formatTaskType(task.task_type)}</span>
                )}
              </div>
              {expanded[task.id] ? (
                <TaskDetails
                  task={task}
                  persistedStyle={persistedStyle[task.id]}
                  persistedLoading={persistedLoading[task.id]}
                />
              ) : null}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {task.status === "processing" && (
                <span className="text-xs text-blue-700">生成中...</span>
              )}
              {task.status === "pending" && (
                <button
                  onClick={() => onStart(task.id)}
                  disabled={isStartingId === task.id}
                  className={operatorButtonClass("primary")}
                >
                  {isStartingId === task.id ? "启动中..." : "开始"}
                </button>
              )}
              <button
                onClick={() => onDelete(task.id)}
                disabled={deletingTaskId === task.id}
                className={operatorButtonClass("ghost", "text-red-700")}
              >
                {deletingTaskId === task.id ? "删除中..." : "删除"}
              </button>
              <button
                onClick={() => onToggleExpanded(task)}
                className={operatorButtonClass("secondary")}
              >
                {expanded[task.id] ? "收起详情" : "详情"}
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
