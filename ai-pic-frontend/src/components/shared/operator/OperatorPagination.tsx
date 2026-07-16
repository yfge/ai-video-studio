"use client";

import { operatorButtonClass } from "./OperatorPrimitives";

export interface OperatorPaginationModel {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function OperatorPagination({
  page,
  pageSize,
  total,
  totalPages,
  onPageChange,
  itemLabel = "项",
}: OperatorPaginationModel & { itemLabel?: string }) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex flex-col gap-3 border-t border-gray-200 px-4 py-3 text-xs text-gray-500 sm:flex-row sm:items-center sm:justify-between">
      <span>
        共 {total} 个{itemLabel} · 每页 {pageSize} 个 · 第 {page} / {totalPages}{" "}
        页
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className={operatorButtonClass("secondary")}
        >
          上一页
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className={operatorButtonClass("secondary")}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
