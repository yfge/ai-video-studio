"use client";

import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { Navigation } from "@/components/layouts";
import type { Task as APITask } from "@/utils/api/types";

import { TasksList } from "./TasksList";
import { TasksPagination } from "./TasksPagination";
import { TasksToolbar } from "./TasksToolbar";
import { useTaskPersistedStyle } from "./useTaskPersistedStyle";
import { useTasks } from "./useTasks";

const toTaskId = (id: APITask["id"]): number | null => {
  const taskId = typeof id === "number" ? id : Number(id);
  return Number.isInteger(taskId) ? taskId : null;
};

export function TasksPage() {
  const { showAlert } = useAlertModal();
  const {
    tasks,
    loading,
    fetchError,
    poll,
    setPoll,
    isStartingId,
    deletingTaskId,
    page,
    setPage,
    size,
    total,
    totalPages,
    taskTypeFilter,
    setTaskTypeFilter,
    refresh,
    startTask,
    deleteTask,
  } = useTasks();

  const { expanded, toggleExpanded, persistedStyle, persistedLoading } =
    useTaskPersistedStyle();

  const handleStart = async (id: APITask["id"]) => {
    const taskId = toTaskId(id);
    if (!taskId) {
      showAlert({ message: "任务编号无效，无法启动任务", variant: "warning" });
      return;
    }
    const res = await startTask(taskId);
    if (res.success) {
      showAlert({
        message: res.message || "任务已开始执行",
        variant: "success",
      });
    } else {
      showAlert({ message: res.message || "启动任务失败", variant: "error" });
    }
  };

  const handleDelete = (id: APITask["id"]) => {
    const taskId = toTaskId(id);
    if (!taskId) {
      showAlert({ message: "任务编号无效，无法删除", variant: "warning" });
      return;
    }
    showAlert({
      title: "确认删除任务",
      message: "确定删除该任务吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: async () => {
        const res = await deleteTask(taskId);
        if (!res.success) {
          showAlert({
            message: res.message || "删除任务失败",
            variant: "error",
          });
        }
      },
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold text-gray-900">任务管理</h1>
          <TasksToolbar
            poll={poll}
            onPollChange={setPoll}
            onRefresh={() => void refresh()}
            taskTypeFilter={taskTypeFilter}
            onTaskTypeFilterChange={(next) => {
              setTaskTypeFilter(next);
              setPage(1);
            }}
          />
        </div>
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">任务列表</h2>
            {fetchError && (
              <p className="mt-2 text-sm text-red-600">{fetchError}</p>
            )}
            {loading && <p className="mt-2 text-sm text-gray-500">加载中...</p>}
          </div>
          <TasksList
            tasks={tasks}
            loading={loading}
            fetchError={fetchError}
            expanded={expanded}
            onToggleExpanded={toggleExpanded}
            persistedStyle={persistedStyle}
            persistedLoading={persistedLoading}
            isStartingId={isStartingId}
            deletingTaskId={deletingTaskId}
            onStart={(taskId) => void handleStart(taskId)}
            onDelete={handleDelete}
          />
          {!loading && !fetchError && tasks.length > 0 ? (
            <TasksPagination
              total={total}
              size={size}
              page={page}
              totalPages={totalPages}
              onPrev={() => setPage((p) => Math.max(1, p - 1))}
              onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
            />
          ) : null}
        </div>
      </main>
    </div>
  );
}
