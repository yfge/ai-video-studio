"use client";

import type { Story } from "@/utils/api";

type CharacterEntry = {
  name?: string;
  character_name?: string;
  role?: string;
  description?: string;
  traits?: string[];
  arc?: string;
};

interface CharactersSectionProps {
  story: Story;
}

export function CharactersSection({ story }: CharactersSectionProps) {
  const mainCharacters = Array.isArray(story.main_characters)
    ? (story.main_characters as CharacterEntry[])
    : [];

  const characterRelationships =
    story.character_relationships && typeof story.character_relationships === "object"
      ? story.character_relationships
      : null;

  if (mainCharacters.length === 0 && !characterRelationships) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">角色与关系</h2>
      {mainCharacters.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-medium text-gray-800 mb-2">主要角色</h3>
          <div className="space-y-2">
            {mainCharacters.map((ch, idx) => (
              <div key={idx} className="border border-gray-100 rounded p-3 bg-gray-50">
                <div className="font-medium text-gray-900">
                  {ch.name || ch.character_name || `角色 ${idx + 1}`}
                </div>
                {ch.role && (
                  <div className="text-sm text-gray-700">角色：{ch.role}</div>
                )}
                {ch.description && (
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    描述：{ch.description}
                  </div>
                )}
                {ch.traits && Array.isArray(ch.traits) && (
                  <div className="text-sm text-gray-700 mt-1">
                    特质：{ch.traits.join("，")}
                  </div>
                )}
                {ch.arc && (
                  <div className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">
                    成长弧光：{ch.arc}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {characterRelationships && (
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">角色关系</h3>
          <div className="space-y-2">
            {Object.entries(characterRelationships as Record<string, unknown>).map(
              ([key, value]) => (
                <div key={key} className="text-sm text-gray-700 whitespace-pre-wrap">
                  <span className="font-medium text-gray-900">{key}：</span>
                  {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
