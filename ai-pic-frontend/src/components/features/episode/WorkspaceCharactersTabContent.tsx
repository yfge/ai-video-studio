"use client";

import { useState } from "react";
import { useEpisodeCharacters } from "@/hooks/useEpisodeCharacters";
import {
  type EpisodeCharacter,
  type EpisodeCharacterCreate,
  type EpisodeCharacterUpdate,
  type AutoCreatedCharacter,
} from "@/utils/api/episodeCharacters";
import { CharacterFormModal } from "./CharacterFormModal";
import { CharacterRow } from "./CharacterRow";

interface WorkspaceCharactersTabContentProps {
  episodeId: number | string;
  autoCreatedCharacters?: AutoCreatedCharacter[];
}

export function WorkspaceCharactersTabContent({
  episodeId,
  autoCreatedCharacters = [],
}: WorkspaceCharactersTabContentProps) {
  const {
    characters,
    loading,
    error,
    total,
    createCharacter,
    updateCharacter,
    deleteCharacter,
  } = useEpisodeCharacters({ episodeId, autoLoad: true });

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCharacter, setEditingCharacter] =
    useState<EpisodeCharacter | null>(null);
  const [showAutoCreated, setShowAutoCreated] = useState(
    autoCreatedCharacters.length > 0
  );

  const handleCreate = async (data: EpisodeCharacterCreate) => {
    const result = await createCharacter(data);
    if (result) {
      setIsCreateModalOpen(false);
    }
  };

  const handleUpdate = async (
    characterId: number | string,
    data: EpisodeCharacterUpdate
  ) => {
    const result = await updateCharacter(characterId, data);
    if (result) {
      setEditingCharacter(null);
    }
  };

  const handleDelete = async (characterId: number | string) => {
    if (confirm("确定要删除此临时角色吗？")) {
      await deleteCharacter(characterId, "用户手动删除");
    }
  };

  if (loading && characters.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Auto-created Characters Notification */}
      {showAutoCreated && autoCreatedCharacters.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-blue-900">
                自动创建了 {autoCreatedCharacters.length} 个临时角色
              </h3>
              <p className="text-sm text-blue-700 mt-1">
                这些角色是从剧本对白中自动识别并创建的，您可以进一步完善它们的信息。
              </p>
              <div className="mt-2 space-y-1">
                {autoCreatedCharacters.map((char) => (
                  <div key={char.episode_character_id} className="text-sm">
                    <span className="font-medium text-blue-900">
                      {char.character_name}
                    </span>
                    <span className="text-blue-600 ml-2">
                      (重要度: {char.importance}, 对白数:{" "}
                      {char.generated_info.dialogue_count})
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <button
              onClick={() => setShowAutoCreated(false)}
              className="text-blue-400 hover:text-blue-600"
              aria-label="关闭提示"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">临时角色管理</h2>
          <p className="text-sm text-gray-600 mt-1">
            管理本集出现的临时角色（快递员、路人等），配置图片和声音资源
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + 添加角色
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Characters List */}
      {characters.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-gray-500">
            暂无临时角色。点击&ldquo;添加角色&rdquo;按钮创建。
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow">
          <div className="divide-y divide-gray-200">
            {characters.map((character) => (
              <CharacterRow
                key={character.id}
                character={character}
                onEdit={() => setEditingCharacter(character)}
                onDelete={() => handleDelete(character.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Total Count */}
      {total > 0 && (
        <div className="text-sm text-gray-600 text-center">
          共 {total} 个临时角色
        </div>
      )}

      {/* Create Modal */}
      {isCreateModalOpen && (
        <CharacterFormModal
          mode="create"
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreate}
          title="添加临时角色"
        />
      )}

      {/* Edit Modal */}
      {editingCharacter && (
        <CharacterFormModal
          mode="edit"
          isOpen={true}
          onClose={() => setEditingCharacter(null)}
          onSubmit={(data) => handleUpdate(editingCharacter.id, data)}
          initialData={editingCharacter}
          title="编辑临时角色"
        />
      )}
    </div>
  );
}
