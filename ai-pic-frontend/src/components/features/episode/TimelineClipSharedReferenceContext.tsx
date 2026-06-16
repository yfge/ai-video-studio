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
    return character ? episodeCharacterDisplayName(character) : `IP ${virtualIpId}`;
  });

  return (
    <section
      aria-label="片段共享参考上下文"
      className="mb-2 grid gap-2 rounded-md border border-slate-200 bg-white p-2 text-[11px] text-slate-700"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-slate-900">
          片段共享参考上下文
        </span>
        <span className="text-slate-500">会用于分镜、首尾帧和视频任务</span>
      </div>
      <div className="grid gap-1 min-[720px]:grid-cols-3">
        <span>角色 IP：{labels.length ? labels.join("、") : "未绑定"}</span>
        <span>IP 图：{selectedCharacterReferenceUrls.length} 张</span>
        <span>环境图：{selectedEnvironmentReferenceUrls.length} 张</span>
      </div>
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
    </section>
  );
}
