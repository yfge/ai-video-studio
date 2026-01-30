"use client";

type TasksPaginationProps = {
  total: number;
  size: number;
  page: number;
  totalPages: number;
  onPrev: () => void;
  onNext: () => void;
};

export function TasksPagination({
  total,
  size,
  page,
  totalPages,
  onPrev,
  onNext,
}: TasksPaginationProps) {
  return (
    <div className="px-6 py-4 flex items-center justify-between text-sm text-gray-600 border-t border-gray-200">
      <div>
        共 {total} 个任务，每页 {size} 个，当前第 {page} / {totalPages} 页
      </div>
      <div className="space-x-2">
        <button
          onClick={onPrev}
          disabled={page <= 1}
          className="px-3 py-1 rounded border text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          上一页
        </button>
        <button
          onClick={onNext}
          disabled={page >= totalPages}
          className="px-3 py-1 rounded border text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一页
        </button>
      </div>
    </div>
  );
}
