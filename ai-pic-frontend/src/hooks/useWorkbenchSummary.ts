"use client";

import { useCallback, useEffect, useState } from "react";
import { workbenchAPI } from "@/utils/api/endpoints";
import type { WorkbenchSummary } from "@/utils/api/types";

export function useWorkbenchSummary() {
  const [summary, setSummary] = useState<WorkbenchSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await workbenchAPI.getSummary();
      if (response.success && response.data) {
        setSummary(response.data);
        setError(null);
      } else {
        setError(response.error || "加载工作台失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载工作台失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { summary, loading, error, refresh };
}
