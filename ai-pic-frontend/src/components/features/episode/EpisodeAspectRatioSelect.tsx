"use client";

import { useMemo, useState } from "react";

import { episodeAPI } from "@/utils/api/endpoints";
import type { Episode, Story } from "@/utils/api/types";

type AspectRatioValue = "9:16" | "16:9" | null;

type Props = {
  episodeId: number;
  episodeAspectRatio?: AspectRatioValue;
  storyDefaultAspectRatio?: Story["default_aspect_ratio"];
  disabled?: boolean;
  onUpdated?: (episode: Episode) => void;
};

export function EpisodeAspectRatioSelect({
  episodeId,
  episodeAspectRatio,
  storyDefaultAspectRatio,
  disabled = false,
  onUpdated,
}: Props) {
  const inheritedLabel = useMemo(() => {
    const fallback = storyDefaultAspectRatio ?? "9:16";
    return `跟随故事（${fallback}）`;
  }, [storyDefaultAspectRatio]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const current = episodeAspectRatio ?? null;

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-600">画幅</span>
      <select
        className="text-sm border border-gray-300 rounded px-2 py-1 bg-white disabled:opacity-60"
        disabled={disabled || saving}
        value={current ?? ""}
        onChange={async (e) => {
          const raw = e.target.value;
          const next: AspectRatioValue =
            raw === "" ? null : (raw as AspectRatioValue);

          setSaving(true);
          setError("");
          try {
            const res = await episodeAPI.updateEpisode(episodeId, {
              aspect_ratio: next,
            });
            if (!res?.success || !res.data) {
              setError(res?.message || "更新失败");
              return;
            }
            onUpdated?.(res.data);
          } catch (err) {
            setError(String(err));
          } finally {
            setSaving(false);
          }
        }}
      >
        <option value="">{inheritedLabel}</option>
        <option value="9:16">9:16（竖屏）</option>
        <option value="16:9">16:9（横屏）</option>
      </select>
      {saving ? (
        <span className="text-xs text-gray-400">保存中...</span>
      ) : error ? (
        <span className="text-xs text-red-600">{error}</span>
      ) : null}
    </div>
  );
}
