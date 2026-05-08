"use client";

import { useState } from "react";
import { useEpisodeCharacters } from "@/hooks/useEpisodeCharacters";
import type {
  AutoCreatedCharacter,
  EpisodeCharacter,
  EpisodeCharacterCreate,
  EpisodeCharacterUpdate,
} from "@/utils/api/types";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";
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
    autoCreatedCharacters.length > 0,
  );

  const handleCreate = async (data: EpisodeCharacterCreate) => {
    const result = await createCharacter(data);
    if (result) setIsCreateModalOpen(false);
  };

  const handleUpdate = async (
    characterId: number | string,
    data: EpisodeCharacterUpdate,
  ) => {
    const result = await updateCharacter(characterId, data);
    if (result) setEditingCharacter(null);
  };

  const handleDelete = async (characterId: number | string) => {
    if (confirm("确定要删除此临时角色吗？")) {
      await deleteCharacter(characterId, "用户手动删除");
    }
  };

  if (loading && characters.length === 0) {
    return <OperatorState title="加载临时角色..." />;
  }

  return (
    <div className="space-y-4">
      {showAutoCreated && autoCreatedCharacters.length > 0 ? (
        <OperatorState
          title={`自动创建了 ${autoCreatedCharacters.length} 个临时角色`}
          detail="这些角色从剧本对白中识别，可继续完善图片和声音资源。"
          tone="blue"
          action={
            <button
              type="button"
              onClick={() => setShowAutoCreated(false)}
              className={operatorButtonClass("ghost")}
            >
              关闭
            </button>
          }
        />
      ) : null}

      <OperatorPanel>
        <OperatorSectionHeader
          title="临时角色管理"
          subtitle="管理本集出现的快递员、路人等临时角色"
          action={
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(true)}
              className={operatorButtonClass("primary")}
            >
              添加角色
            </button>
          }
        />
        {error ? (
          <div className="p-4">
            <OperatorState title={error} tone="red" />
          </div>
        ) : null}
        {characters.length === 0 ? (
          <div className="p-4">
            <OperatorState title="暂无临时角色" detail="点击添加角色创建。" />
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {characters.map((character) => (
              <CharacterRow
                key={character.id}
                character={character}
                onEdit={() => setEditingCharacter(character)}
                onDelete={() => handleDelete(character.id)}
              />
            ))}
          </div>
        )}
        {total > 0 ? (
          <div className="border-t border-gray-200 px-4 py-3 text-center text-xs text-gray-500">
            共 {total} 个临时角色
          </div>
        ) : null}
      </OperatorPanel>

      {isCreateModalOpen ? (
        <CharacterFormModal
          mode="create"
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreate}
          title="添加临时角色"
        />
      ) : null}
      {editingCharacter ? (
        <CharacterFormModal
          mode="edit"
          isOpen
          onClose={() => setEditingCharacter(null)}
          onSubmit={(data) => handleUpdate(editingCharacter.id, data)}
          initialData={editingCharacter}
          title="编辑临时角色"
        />
      ) : null}
    </div>
  );
}
