"use client";

import type { EpisodeCharacter } from "@/utils/api/types";

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
  const importanceColors = [
    "",
    "bg-gray-100 text-gray-700",
    "bg-blue-100 text-blue-700",
    "bg-indigo-100 text-indigo-700",
    "bg-purple-100 text-purple-700",
    "bg-pink-100 text-pink-700",
  ];

  return (
    <div className="p-4 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-medium text-gray-900">
              {character.character_name}
            </h3>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded ${
                importanceColors[character.importance] || importanceColors[1]
              }`}
            >
              {importanceLabels[character.importance] || "次要"}
            </span>
            {character.role_type && (
              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                {character.role_type}
              </span>
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
            onClick={onEdit}
            className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
          >
            编辑
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  );
}
