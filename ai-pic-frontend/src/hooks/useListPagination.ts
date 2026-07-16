"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

export const DEFAULT_LIST_PAGE_SIZE = 12;

export function paginateItems<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

export function useListPagination<T>(
  items: T[],
  pageSize = DEFAULT_LIST_PAGE_SIZE,
) {
  const [requestedPage, setRequestedPage] = useState(1);
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const page = Math.min(requestedPage, totalPages);

  useEffect(() => {
    if (requestedPage !== page) {
      setRequestedPage(page);
    }
  }, [page, requestedPage]);

  const onPageChange = useCallback(
    (nextPage: number) => {
      setRequestedPage(Math.min(totalPages, Math.max(1, nextPage)));
    },
    [totalPages],
  );
  const resetPage = useCallback(() => setRequestedPage(1), []);
  const pageItems = useMemo(
    () => paginateItems(items, page, pageSize),
    [items, page, pageSize],
  );

  return {
    items: pageItems,
    page,
    pageSize,
    total,
    totalPages,
    onPageChange,
    resetPage,
  };
}
