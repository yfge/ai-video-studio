import { useCallback, useEffect, useMemo, useState } from "react";

import { styleAPI } from "@/utils/api/endpoints";
import type { ApiResponse, StylePreset } from "@/utils/api/types";

interface UseStylePresetsOptions {
  enabled?: boolean;
  cacheKey?: string;
  fetcher?: () => Promise<ApiResponse<StylePreset[]>>;
}

interface UseStylePresetsState {
  presets: StylePreset[];
  loading: boolean;
  error: string | null;
}

const presetCache = new Map<string, StylePreset[]>();

export function useStylePresets(options: UseStylePresetsOptions = {}) {
  const { enabled = true, cacheKey = "global", fetcher } = options;

  const effectiveKey = useMemo(() => {
    if (fetcher) return `custom:${cacheKey}`;
    return cacheKey;
  }, [cacheKey, fetcher]);

  const cached = useMemo(() => presetCache.get(effectiveKey), [effectiveKey]);

  const [state, setState] = useState<UseStylePresetsState>(() => ({
    presets: cached ?? [],
    loading: !cached && enabled,
    error: null,
  }));

  const load = useCallback(async () => {
    if (!enabled) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = fetcher ? await fetcher() : await styleAPI.listPresets();
      if (!response.success || !response.data) {
        throw new Error(response.error || "获取风格预设失败");
      }
      presetCache.set(effectiveKey, response.data);
      setState({ presets: response.data, loading: false, error: null });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "获取风格预设失败";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, [effectiveKey, enabled, fetcher]);

  useEffect(() => {
    if (!enabled) return;
    if (presetCache.has(effectiveKey)) {
      setState({
        presets: presetCache.get(effectiveKey) ?? [],
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
