"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";
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

export function TasksPage({
  targetTaskId = null,
}: {
  targetTaskId?: number | null;
}) {
  const { showAlert } = useAlertModal();
  const {
    tasks,
    loading,
    fetchError,
    poll,
    setPoll,
    isStartingId,
    deletingTaskId,
    cancellingTaskId,
    page,
    setPage,
    size,
    total,
    totalPages,
    taskTypeFilter,
    setTaskTypeFilter,
    refresh,
    startTask,
    cancelTask,
    deleteTask,
  } = useTasks({ taskId: targetTaskId });

  const { expanded, toggleExpanded, persistedStyle, persistedLoading } =
    useTaskPersistedStyle();
  const targetTask = targetTaskId
    ? tasks.find((task) => task.id === targetTaskId)
    : null;

  useEffect(() => {
    if (targetTaskId && targetTask && !expanded[targetTaskId]) {
      toggleExpanded(targetTask);
    }
  }, [expanded, targetTask, targetTaskId, toggleExpanded]);

  const handleCancel = (id: APITask["id"]) => {
    const taskId = toTaskId(id);
    if (!taskId) {
      showAlert({ message: "任务编号无效，无法取消任务", variant: "warning" });
      return;
    }
    showAlert({
      title: "取消任务",
      message: `确认取消任务 #${taskId}？已在执行的任务会尽力终止。`,
      variant: "warning",
      confirmText: "确认取消",
      onConfirm: () => {
        void cancelTask(taskId).then((res) => {
          if (!res.success) {
            showAlert({
              message: res.message || "取消任务失败",
              variant: "error",
            });
          }
        });
      },
    });
  };

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
    <OperatorShell
      title="任务"
      subtitle="生成队列、失败重试和审计信息"
      breadcrumb={["IP 中心", "任务"]}
    >
      <div className="space-y-4">
        {targetTaskId ? (
          <OperatorPanel className="flex flex-wrap items-center justify-between gap-3 p-3">
            <div className="text-sm font-medium text-gray-800">
              正在查看任务 #{targetTaskId}
            </div>
            <Link href="/tasks" className={operatorButtonClass("secondary")}>
              查看全部任务
            </Link>
          </OperatorPanel>
        ) : null}
        <OperatorPanel>
          <OperatorSectionHeader
            title="任务队列"
            subtitle={`共 ${total} 个任务，当前第 ${page} / ${
              totalPages || 1
            } 页`}
            action={
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
            }
          />
          {fetchError ? (
            <div className="p-4">
              <OperatorState title={fetchError} tone="red" />
            </div>
          ) : null}
          {loading ? (
            <div className="p-4">
              <OperatorState title="加载任务列表..." />
            </div>
          ) : null}
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
            cancellingTaskId={cancellingTaskId}
            onStart={(taskId) => void handleStart(taskId)}
            onCancel={handleCancel}
            onDelete={handleDelete}
            focusedTaskId={targetTaskId}
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
        </OperatorPanel>
      </div>
    </OperatorShell>
  );
}
