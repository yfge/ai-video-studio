"use client";

import { operatorButtonClass } from "@/components/shared";
import type { EpisodeCharacter } from "@/utils/api/types";
import { episodeCharacterDisplayName } from "./episodeCharacterDisplay";

export function StoryboardCharacterIpSelector({
  characters,
  loading,
  error,
  onNavigateToCharacters,
  selectedVirtualIpIds,
  onToggle,
}: {
  characters: EpisodeCharacter[];
  loading: boolean;
  error: string | null;
  onNavigateToCharacters?: () => void;
  selectedVirtualIpIds: number[];
  onToggle: (virtualIpId: number, checked: boolean) => void;
}) {
  const options = uniqueCharactersByVirtualIp(characters);
  return (
    <fieldset className="mt-3 grid gap-2" aria-label="绑定角色 IP">
      <legend className="text-[11px] font-medium text-gray-700">
        绑定角色 IP
      </legend>
      {loading ? (
        <div className="text-[11px] text-gray-500">角色加载中...</div>
      ) : error ? (
        <div className="text-[11px] text-red-600">角色加载失败：{error}</div>
      ) : options.length ? (
        <div className="grid gap-1.5">
          {options.map((character) => {
            const label = episodeCharacterDisplayName(character);
            const virtualIpId = character.virtual_ip_id;
            return (
              <label
                key={virtualIpId}
                className="flex min-w-0 items-center gap-2 rounded-md border border-gray-100 px-2 py-1.5 text-xs text-gray-700"
              >
                <input
                  type="checkbox"
                  checked={selectedVirtualIpIds.includes(virtualIpId)}
                  onChange={(event) =>
                    onToggle(virtualIpId, event.currentTarget.checked)
                  }
                  aria-label={`绑定角色 IP ${label}`}
                  className="h-3.5 w-3.5 flex-none rounded border-gray-300"
                />
                <span className="min-w-0 flex-1 truncate">{label}</span>
                <span className="flex-none text-[11px] text-gray-400">
                  IP {virtualIpId}
                </span>
              </label>
            );
          })}
        </div>
      ) : (
        <div className="grid gap-2">
          <div className="text-[11px] text-gray-500">
            暂无角色 IP，请先在临时角色绑定 VirtualIP。
          </div>
          {onNavigateToCharacters ? (
            <button
              type="button"
              onClick={onNavigateToCharacters}
              className={operatorButtonClass("secondary", "w-fit text-xs")}
            >
              去临时角色绑定 IP
            </button>
          ) : null}
        </div>
      )}
    </fieldset>
  );
}

function uniqueCharactersByVirtualIp(characters: EpisodeCharacter[]) {
  const seen = new Set<number>();
  const options: EpisodeCharacter[] = [];
  for (const character of characters) {
    if (!character.virtual_ip_id || seen.has(character.virtual_ip_id)) continue;
    seen.add(character.virtual_ip_id);
    options.push(character);
  }
  return options;
}
