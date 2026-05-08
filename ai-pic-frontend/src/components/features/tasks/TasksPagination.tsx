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
    <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 text-xs text-gray-500">
      <div>
        共 {total} 个任务，每页 {size} 个，当前第 {page} / {totalPages} 页
      </div>
      <div className="flex gap-2">
        <button
          onClick={onPrev}
          disabled={page <= 1}
          className={operatorButtonClass("secondary")}
        >
          上一页
        </button>
        <button
          onClick={onNext}
          disabled={page >= totalPages}
          className={operatorButtonClass("secondary")}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
import { operatorButtonClass } from "@/components/shared";
