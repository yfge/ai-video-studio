"use client";

import { TASK_TYPE_OPTIONS } from "./taskTypeOptions";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";

type TasksToolbarProps = {
  poll: boolean;
  onPollChange: (next: boolean) => void;
  onRefresh: () => void;
  taskTypeFilter: string;
  onTaskTypeFilterChange: (next: string) => void;
};

export function TasksToolbar({
  poll,
  onPollChange,
  onRefresh,
  taskTypeFilter,
  onTaskTypeFilterChange,
}: TasksToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="flex items-center gap-2 text-xs text-gray-600">
        类型
        <select
          value={taskTypeFilter}
          onChange={(event) => onTaskTypeFilterChange(event.target.value)}
          className={operatorSelectClass()}
        >
          {TASK_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value || "all"} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-2 text-xs text-gray-600">
        <input
          type="checkbox"
          checked={poll}
          onChange={(e) => onPollChange(e.target.checked)}
        />
        自动刷新
      </label>
      <button
        type="button"
        onClick={onRefresh}
        className={operatorButtonClass("secondary")}
      >
        刷新
      </button>
    </div>
  );
}
