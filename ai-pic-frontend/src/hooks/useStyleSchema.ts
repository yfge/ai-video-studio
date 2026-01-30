import { useCallback, useEffect, useMemo, useState } from "react";

import {
  styleAPI,
  type ApiResponse,
  type StyleSchemaResponse,
} from "@/utils/api";

interface UseStyleSchemaOptions {
  enabled?: boolean;
  cacheKey?: string;
  fetcher?: () => Promise<ApiResponse<StyleSchemaResponse>>;
}

interface UseStyleSchemaState {
  schema: StyleSchemaResponse | null;
  loading: boolean;
  error: string | null;
}

const schemaCache = new Map<string, StyleSchemaResponse>();

export function useStyleSchema(options: UseStyleSchemaOptions = {}) {
  const { enabled = true, cacheKey = "global", fetcher } = options;

  const effectiveKey = useMemo(() => {
    if (fetcher) return `custom:${cacheKey}`;
    return cacheKey;
  }, [cacheKey, fetcher]);

  const cached = useMemo(
    () => schemaCache.get(effectiveKey) ?? null,
    [effectiveKey],
  );

  const [state, setState] = useState<UseStyleSchemaState>(() => ({
    schema: cached,
    loading: !cached && enabled,
    error: null,
  }));

  const load = useCallback(async () => {
    if (!enabled) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = fetcher ? await fetcher() : await styleAPI.getSchema();
      if (!response.success || !response.data) {
        throw new Error(response.error || "获取风格 schema 失败");
      }
      schemaCache.set(effectiveKey, response.data);
      setState({ schema: response.data, loading: false, error: null });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "获取风格 schema 失败";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, [effectiveKey, enabled, fetcher]);

  useEffect(() => {
    if (!enabled) return;
    if (schemaCache.has(effectiveKey)) {
      setState({
        schema: schemaCache.get(effectiveKey) ?? null,
        loading: false,
        error: null,
      });
      return;
    }
    void load();
  }, [effectiveKey, enabled, load]);

  return {
    ...state,
    refresh: load,
  };
}

export function clearStyleSchemaCache(prefix?: string) {
  if (!prefix) {
    schemaCache.clear();
    return;
  }
  Array.from(schemaCache.keys()).forEach((key) => {
    if (key.startsWith(prefix)) {
      schemaCache.delete(key);
    }
  });
}
