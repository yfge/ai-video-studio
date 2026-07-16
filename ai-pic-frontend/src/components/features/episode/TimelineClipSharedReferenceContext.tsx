"use client";

import type { EpisodeCharacter } from "@/utils/api/types";
import { episodeCharacterDisplayName } from "./episodeCharacterDisplay";

export function TimelineClipSharedReferenceContext({
  episodeCharacters,
  selectedCharacterVirtualIpIds,
  selectedCharacterReferenceUrls,
  selectedEnvironmentReferenceUrls,
  manualReferenceImages,
  onManualReferenceImagesChange,
}: {
  episodeCharacters: EpisodeCharacter[];
  selectedCharacterVirtualIpIds: number[];
  selectedCharacterReferenceUrls: string[];
  selectedEnvironmentReferenceUrls: string[];
  manualReferenceImages: string;
  onManualReferenceImagesChange: (value: string) => void;
}) {
  const labels = selectedCharacterVirtualIpIds.map((virtualIpId) => {
    const character = episodeCharacters.find(
      (item) => item.virtual_ip_id === virtualIpId,
    );
    return character
      ? episodeCharacterDisplayName(character)
      : `IP ${virtualIpId}`;
  });

  return (
    <details
      aria-label="片段共享参考上下文"
      data-clip-shared-reference-context="collapsed"
      className="group mb-2 overflow-hidden rounded-lg border border-slate-200 bg-white text-[11px] text-slate-700"
    >
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2 marker:hidden [&::-webkit-details-marker]:hidden">
        <span className="font-semibold text-slate-900">共享参考</span>
        <span className="min-w-0 flex-1 truncate text-slate-500">
          {labels.length ? labels.join("、") : "未绑定角色 IP"}
        </span>
        <span className="whitespace-nowrap text-slate-500">
          IP 图 {selectedCharacterReferenceUrls.length} · 环境图{" "}
          {selectedEnvironmentReferenceUrls.length}
        </span>
        <span className="text-slate-400 transition group-open:rotate-180">
          ▾
        </span>
      </summary>
      <div className="grid gap-2 border-t border-slate-100 px-3 py-2.5">
        <p className="text-slate-500">会用于分镜、首尾帧和视频任务。</p>
        <label className="grid gap-1 text-xs text-slate-700">
          <span>附加参考图 URL（可选，一行一个）</span>
          <textarea
            aria-label="附加参考图 URL"
            value={manualReferenceImages}
            onChange={(event) =>
              onManualReferenceImagesChange(event.currentTarget.value)
            }
            onInput={(event) =>
              onManualReferenceImagesChange(event.currentTarget.value)
            }
            rows={2}
            className="resize-none rounded-md border border-slate-200 px-2 py-1.5 text-xs outline-none focus:border-slate-400"
            placeholder="https://..."
          />
        </label>
      </div>
    </details>
  );
}
