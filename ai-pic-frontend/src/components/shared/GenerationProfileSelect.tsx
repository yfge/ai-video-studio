"use client";

import { useEffect, useMemo } from "react";

import { useImageGenProfiles } from "@/hooks/useImageGenProfiles";
import type {
  ImageGenMode,
  ImageGenProfile,
} from "@/utils/api/types/image-gen.types";

interface GenerationProfileSelectProps {
  modelId?: string;
  mode: ImageGenMode;
  value?: string;
  onChange: (next?: string) => void;
  disabled?: boolean;
  label?: string;
  helperText?: string;
  className?: string;
}

const formatDefaults = (profile: ImageGenProfile) => {
  const parts: string[] = [];
  if (profile.defaults.steps !== undefined && profile.defaults.steps !== null) {
    parts.push(`steps=${profile.defaults.steps}`);
  }
  if (
    profile.defaults.cfg_scale !== undefined &&
    profile.defaults.cfg_scale !== null
  ) {
    parts.push(`cfg=${profile.defaults.cfg_scale}`);
  }
  if (
    profile.defaults.strength !== undefined &&
    profile.defaults.strength !== null
  ) {
    parts.push(`strength=${profile.defaults.strength}`);
  }
  if (profile.defaults.image_reference) {
    const trimmed = profile.defaults.image_reference.trim();
    if (trimmed) {
      parts.push(`ref=${trimmed}`);
    }
  }
  if (
    profile.defaults.image_fidelity !== undefined &&
    profile.defaults.image_fidelity !== null
  ) {
    parts.push(`image_fidelity=${profile.defaults.image_fidelity}`);
  }
  if (
    profile.defaults.human_fidelity !== undefined &&
    profile.defaults.human_fidelity !== null
  ) {
    parts.push(`human_fidelity=${profile.defaults.human_fidelity}`);
  }
  if (profile.defaults.negative_prompt) {
    const trimmed = profile.defaults.negative_prompt.trim();
    if (trimmed) {
      parts.push(
        `negative=${
          trimmed.length > 80 ? `${trimmed.slice(0, 80)}…` : trimmed
        }`,
      );
    }
  }
  return parts.join(" · ");
};

export function GenerationProfileSelect({
  modelId,
  mode,
  value,
  onChange,
  disabled = false,
  label = "质量档位",
  helperText,
  className,
}: GenerationProfileSelectProps) {
  const enabled = Boolean(modelId) && !disabled;
  const { profiles, defaultProfileId, loading, error, refresh } =
    useImageGenProfiles({
      model: modelId,
      mode,
      enabled,
    });

  const profileIds = useMemo(
    () => new Set(profiles.map((p) => p.id)),
    [profiles],
  );
  const selectedProfile = useMemo(
    () => profiles.find((p) => p.id === value),
    [profiles, value],
  );

  useEffect(() => {
    if (!modelId) {
      if (value) onChange(undefined);
      return;
    }
    if (loading) return;

    if (profiles.length === 0) {
      if (value) onChange(undefined);
      return;
    }
    if (!value || !profileIds.has(value)) {
      onChange(defaultProfileId || profiles[0]?.id);
    }
  }, [
    defaultProfileId,
    loading,
    modelId,
    onChange,
    profileIds,
    profiles,
    value,
  ]);

  const isUnsupported = Boolean(modelId) && !loading && profiles.length === 0;
  const selectDisabled = disabled || !modelId || loading || isUnsupported;
  const effectiveHelperText =
    helperText ??
    (mode === "image_to_image"
      ? "按模型默认参数收敛 strength/fidelity 等关键参数，提升质量一致性"
      : "按模型默认参数收敛 steps/cfg/negative 等关键参数，提升质量一致性");

  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      {effectiveHelperText ? (
        <p className="text-xs text-gray-500 mb-1">{effectiveHelperText}</p>
      ) : null}
      <div className="flex items-center gap-2">
        <select
          value={selectDisabled ? "" : value || ""}
          onChange={(e) => onChange(e.target.value || undefined)}
          disabled={selectDisabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
        >
          {!modelId ? <option value="">请先选择模型</option> : null}
          {loading ? <option value="">加载中...</option> : null}
          {isUnsupported ? (
            <option value="">该模型不支持 profile</option>
          ) : null}
          {!loading &&
            profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.label || profile.id}
              </option>
            ))}
        </select>
        {error ? (
          <button
            type="button"
            onClick={() => void refresh()}
            className="shrink-0 text-xs text-blue-600 hover:text-blue-800"
          >
            重试
          </button>
        ) : null}
      </div>
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
      {selectedProfile ? (
        <p
          className="mt-1 text-xs text-gray-500"
          title={selectedProfile.defaults.negative_prompt || ""}
        >
          默认参数：{formatDefaults(selectedProfile) || "（无）"}
        </p>
      ) : null}
    </div>
  );
}
