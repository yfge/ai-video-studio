import { useCallback, useEffect, useMemo, useState } from "react";

import { imageGenAPI } from "@/utils/api/endpoints/image-gen.endpoints";
import type {
  ImageGenMode,
  ImageGenProfile,
  ImageGenProfilesResponse,
} from "@/utils/api/types/image-gen.types";

interface UseImageGenProfilesOptions {
  model?: string | null;
  mode: ImageGenMode;
  enabled?: boolean;
  cacheKey?: string;
}

interface UseImageGenProfilesState {
  profiles: ImageGenProfile[];
  defaultProfileId: string | null;
  provider: string | null;
  modelId: string | null;
  loading: boolean;
  error: string | null;
}

const profileCache = new Map<string, ImageGenProfilesResponse>();

const buildCacheKey = (mode: ImageGenMode, model: string) => `${mode}:${model}`;

export function useImageGenProfiles(options: UseImageGenProfilesOptions) {
  const { model, mode, enabled = true, cacheKey } = options;

  const effectiveKey = useMemo(() => {
    if (cacheKey) return cacheKey;
    if (!model) return `${mode}:<unset>`;
    return buildCacheKey(mode, model);
  }, [cacheKey, mode, model]);

  const cached = useMemo(() => {
    if (!model) return undefined;
    return profileCache.get(effectiveKey);
  }, [effectiveKey, model]);

  const [state, setState] = useState<UseImageGenProfilesState>(() => ({
    profiles: cached?.profiles ?? [],
    defaultProfileId: cached?.default_profile_id ?? null,
    provider: cached?.provider ?? null,
    modelId: cached?.model_id ?? null,
    loading: Boolean(enabled && model && !cached),
    error: null,
  }));

  const load = useCallback(async () => {
    if (!enabled) return;
    if (!model) {
      setState({
        profiles: [],
        defaultProfileId: null,
        provider: null,
        modelId: null,
        loading: false,
        error: null,
      });
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await imageGenAPI.getProfiles(model, mode);
      if (!response.success || !response.data) {
        throw new Error(response.error || "获取 profiles 失败");
      }
      profileCache.set(effectiveKey, response.data);
      setState({
        profiles: response.data.profiles ?? [],
        defaultProfileId: response.data.default_profile_id ?? null,
        provider: response.data.provider ?? null,
        modelId: response.data.model_id ?? null,
        loading: false,
        error: null,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "获取 profiles 失败";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, [effectiveKey, enabled, model, mode]);

  useEffect(() => {
    if (!enabled) return;
    if (!model) {
      setState({
        profiles: [],
        defaultProfileId: null,
        provider: null,
        modelId: null,
        loading: false,
        error: null,
      });
      return;
    }
    if (profileCache.has(effectiveKey)) {
      const payload = profileCache.get(effectiveKey)!;
      setState({
        profiles: payload.profiles ?? [],
        defaultProfileId: payload.default_profile_id ?? null,
        provider: payload.provider ?? null,
        modelId: payload.model_id ?? null,
        loading: false,
        error: null,
      });
      return;
    }
    void load();
  }, [effectiveKey, enabled, load, model]);

  return {
    ...state,
    refresh: load,
  };
}

export function clearImageGenProfilesCache(prefix?: string) {
  if (!prefix) {
    profileCache.clear();
    return;
  }
  Array.from(profileCache.keys()).forEach((key) => {
    if (key.startsWith(prefix)) {
      profileCache.delete(key);
    }
  });
}
