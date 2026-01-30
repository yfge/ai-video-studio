import { useCallback, useEffect, useMemo, useState } from "react";

import {
  aiAPI,
  type ApiResponse,
  type AvailableModelsResponse,
} from "@/utils/api";

interface UseAvailableModelsOptions {
  modelType?: string;
  fetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>;
  enabled?: boolean;
  cacheKey?: string;
}

interface UseAvailableModelsState {
  models: AvailableModelsResponse["models"];
  defaultModel: string;
  loading: boolean;
  error: string | null;
}

const modelCache = new Map<string, AvailableModelsResponse>();

const buildCacheKey = (baseKey: string, modelType?: string) => {
  return modelType ? `${baseKey}:${modelType} ` : baseKey;
};

export function useAvailableModels(options: UseAvailableModelsOptions = {}) {
  const { modelType = "text", fetcher, enabled = true, cacheKey } = options;

  const effectiveKey = useMemo(() => {
    if (cacheKey) {
      return cacheKey;
    }
    if (fetcher) {
      return buildCacheKey("custom", modelType);
    }
    return buildCacheKey("global", modelType);
  }, [cacheKey, fetcher, modelType]);

  const cached = useMemo(() => modelCache.get(effectiveKey), [effectiveKey]);

  const [state, setState] = useState<UseAvailableModelsState>(() => ({
    models: cached?.models ?? [],
    defaultModel: cached?.default ?? "",
    loading: !cached && enabled,
    error: null,
  }));

  const load = useCallback(async () => {
    if (!enabled) {
      return;
    }
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = fetcher
        ? await fetcher()
        : await aiAPI.getAvailableModels({ type: modelType });

      if (!response.success || !response.data) {
        throw new Error(response.error || "获取模型列表失败");
      }

      // Deduplicate models by model_id or id to prevent duplicates in dropdown
      const rawModels = response.data.models ?? [];
      const seen = new Set<string>();
      const deduplicatedModels = rawModels.filter((model) => {
        const key = model.model_id || model.id || "";
        if (!key || seen.has(key)) {
          return false;
        }
        seen.add(key);
        return true;
      });

      const deduplicatedData = { ...response.data, models: deduplicatedModels };
      modelCache.set(effectiveKey, deduplicatedData);
      setState({
        models: deduplicatedModels,
        defaultModel: response.data.default ?? "",
        loading: false,
        error: null,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "获取模型列表失败";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, [effectiveKey, enabled, fetcher, modelType]);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    if (modelCache.has(effectiveKey)) {
      const payload = modelCache.get(effectiveKey)!;
      setState({
        models: payload.models ?? [],
        defaultModel: payload.default ?? "",
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

export function clearAvailableModelsCache(prefix?: string) {
  if (!prefix) {
    modelCache.clear();
    return;
  }
  Array.from(modelCache.keys()).forEach((key) => {
    if (key.startsWith(prefix)) {
      modelCache.delete(key);
    }
  });
}
