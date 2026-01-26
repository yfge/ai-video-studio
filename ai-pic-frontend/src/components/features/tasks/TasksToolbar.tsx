'use client'

import { TASK_TYPE_OPTIONS } from './taskTypeOptions'

type TasksToolbarProps = {
  poll: boolean
  onPollChange: (next: boolean) => void
  onRefresh: () => void
  taskTypeFilter: string
  onTaskTypeFilterChange: (next: string) => void
}

export function TasksToolbar({
  poll,
  onPollChange,
  onRefresh,
  taskTypeFilter,
  onTaskTypeFilterChange,
}: TasksToolbarProps) {
  return (
    <div className="flex items-center space-x-4">
      <label className="text-sm text-gray-600 flex items-center gap-2">
        类型
        <select
          value={taskTypeFilter}
          onChange={(event) => onTaskTypeFilterChange(event.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm text-gray-700"
        >
          {TASK_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value || 'all'} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>
      <label className="text-sm text-gray-600 flex items-center gap-2">
        <input
          type="checkbox"
          checked={poll}
          onChange={(e) => onPollChange(e.target.checked)}
        />
        自动刷新
      </label>
      <button onClick={onRefresh} className="text-sm text-blue-600 hover:text-blue-800">
        刷新
      </button>
    </div>
  )
}

