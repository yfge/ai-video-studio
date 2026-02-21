"use client";

import type { Task as APITask } from "@/utils/api/types";

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

const getStatusColor = (status: APITask["status"]) => {
  switch (status) {
    case "pending":
      return "bg-yellow-100 text-yellow-800";
    case "processing":
      return "bg-blue-100 text-blue-800";
    case "completed":
      return "bg-green-100 text-green-800";
    case "failed":
      return "bg-red-100 text-red-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
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
    <div className="divide-y divide-gray-200">
      {tasks.map((task) => (
        <div key={task.id} className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h3 className="text-lg font-medium text-gray-900">
                  {task.title}
                </h3>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                    task.status,
                  )}`}
                >
                  {getStatusText(task.status)}
                </span>
              </div>
              {task.progress_detail && (
                <p className="text-sm text-gray-700 mb-2">
                  进度：
                  <span className="text-gray-800">{task.progress_detail}</span>
                </p>
              )}
              {task.prompt && (
                <p className="text-gray-600 mb-3">{task.prompt}</p>
              )}
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
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
            <div className="flex items-center space-x-3">
              {task.status === "processing" && (
                <div className="flex items-center space-x-2">
                  <svg
                    className="animate-spin h-5 w-5 text-blue-600"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span className="text-blue-600">生成中...</span>
                </div>
              )}
              {task.status === "pending" && (
                <button
                  onClick={() => onStart(task.id)}
                  disabled={isStartingId === task.id}
                  className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isStartingId === task.id ? "启动中..." : "开始"}
                </button>
              )}
              <button
                onClick={() => onDelete(task.id)}
                disabled={deletingTaskId === task.id}
                className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deletingTaskId === task.id ? "删除中..." : "删除"}
              </button>
              <button
                onClick={() => onToggleExpanded(task)}
                className="text-gray-600 hover:text-gray-800 text-sm"
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
