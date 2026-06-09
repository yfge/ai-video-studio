"use client";

import type { EpisodeCharacter } from "@/utils/api/types";
import { StatusPill, operatorButtonClass } from "@/components/shared";
import { episodeCharacterDisplayName } from "./episodeCharacterDisplay";

interface CharacterRowProps {
  character: EpisodeCharacter;
  onEdit: () => void;
  onDelete: () => void;
}

export function CharacterRow({
  character,
  onEdit,
  onDelete,
}: CharacterRowProps) {
  const importanceLabels = ["", "次要", "重要", "主要", "核心", "关键"];
  const displayName = episodeCharacterDisplayName(character);

  return (
    <div className="p-4 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-gray-900">{displayName}</h3>
            <StatusPill tone={character.importance >= 4 ? "blue" : "gray"}>
              {importanceLabels[character.importance] || "次要"}
            </StatusPill>
            {character.role_type && (
              <StatusPill tone="gray">{character.role_type}</StatusPill>
            )}
          </div>

          <div className="mt-2 space-y-1 text-sm">
            {character.personality && (
              <div>
                <span className="font-medium text-gray-700">性格：</span>
                <span className="text-gray-600">{character.personality}</span>
              </div>
            )}
            {character.background && (
              <div>
                <span className="font-medium text-gray-700">背景：</span>
                <span className="text-gray-600">{character.background}</span>
              </div>
            )}
            {character.appearance_override && (
              <div>
                <span className="font-medium text-gray-700">外观：</span>
                <span className="text-gray-600">
                  {character.appearance_override}
                </span>
              </div>
            )}
            {character.voice_config_override && (
              <div>
                <span className="font-medium text-gray-700">声音：</span>
                <span className="text-gray-600">
                  {character.voice_config_override.provider} /{" "}
                  {character.voice_config_override.voice_id}
                </span>
              </div>
            )}
            {character.scene_appearances &&
              character.scene_appearances.length > 0 && (
                <div>
                  <span className="font-medium text-gray-700">出场场景：</span>
                  <span className="text-gray-600">
                    场景 {character.scene_appearances.join(", ")}
                  </span>
                </div>
              )}
          </div>

          <div className="mt-2 text-xs text-gray-500">
            绑定VirtualIP: {character.virtual_ip_business_id} · 创建于{" "}
            {new Date(character.created_at).toLocaleDateString()}
          </div>
        </div>

        <div className="flex items-center gap-2 ml-4">
          <button
            type="button"
            onClick={onEdit}
            className={operatorButtonClass("secondary")}
          >
            编辑
          </button>
          <button
            type="button"
            onClick={onDelete}
            className={operatorButtonClass("ghost", "text-red-700")}
          >
            删除
          </button>
        </div>
      </div>
    </div>
  );
}
