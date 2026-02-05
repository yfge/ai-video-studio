"use client";

import { useState } from "react";
import { useEpisodeCharacters } from "@/hooks/useEpisodeCharacters";
import {
  type EpisodeCharacter,
  type EpisodeCharacterCreate,
  type EpisodeCharacterUpdate,
  type AutoCreatedCharacter,
} from "@/utils/api/episodeCharacters";
import { Modal } from "@/components/ui/Modal";

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
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreate}
          title="添加临时角色"
        />
      )}

      {/* Edit Modal */}
      {editingCharacter && (
        <CharacterFormModal
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

interface CharacterRowProps {
  character: EpisodeCharacter;
  onEdit: () => void;
  onDelete: () => void;
}

function CharacterRow({ character, onEdit, onDelete }: CharacterRowProps) {
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
              className={`px-2 py-0.5 text-xs font-medium rounded ${importanceColors[character.importance] || importanceColors[1]}`}
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

interface CharacterFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: EpisodeCharacterCreate | EpisodeCharacterUpdate) => void;
  initialData?: EpisodeCharacter;
  title: string;
}

function CharacterFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  title,
}: CharacterFormModalProps) {
  const [formData, setFormData] = useState<
    EpisodeCharacterCreate | EpisodeCharacterUpdate
  >({
    virtual_ip_id: initialData?.virtual_ip_id || 0,
    character_name: initialData?.character_name || "",
    role_type: initialData?.role_type || "temporary",
    importance: initialData?.importance || 1,
    personality: initialData?.personality || "",
    background: initialData?.background || "",
    appearance_override: initialData?.appearance_override || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      maxWidth="max-w-2xl"
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            取消
          </button>
          <button
            type="submit"
            form="character-form"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            保存
          </button>
        </>
      }
    >
      <form id="character-form" onSubmit={handleSubmit} className="space-y-4">
        {!initialData && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              VirtualIP ID <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              required
              value={formData.virtual_ip_id || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  virtual_ip_id: Number(e.target.value),
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="输入VirtualIP的ID"
            />
            <p className="text-xs text-gray-500 mt-1">
              必须绑定一个VirtualIP以提供图片和声音资源
            </p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            角色名称 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={formData.character_name || ""}
            onChange={(e) =>
              setFormData({ ...formData, character_name: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="例如：快递员、医生、路人甲"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              角色类型
            </label>
            <select
              value={formData.role_type || "temporary"}
              onChange={(e) =>
                setFormData({ ...formData, role_type: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="temporary">临时角色</option>
              <option value="guest">客串</option>
              <option value="extra">群众演员</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              重要度 (1-5)
            </label>
            <input
              type="number"
              min="1"
              max="5"
              value={formData.importance || 1}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  importance: Number(e.target.value),
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            性格描述
          </label>
          <textarea
            value={formData.personality || ""}
            onChange={(e) =>
              setFormData({ ...formData, personality: e.target.value })
            }
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="例如：热情、乐观、工作认真"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            背景故事
          </label>
          <textarea
            value={formData.background || ""}
            onChange={(e) =>
              setFormData({ ...formData, background: e.target.value })
            }
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="例如：快递公司员工，负责本小区配送"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            外观补充描述
          </label>
          <textarea
            value={formData.appearance_override || ""}
            onChange={(e) =>
              setFormData({ ...formData, appearance_override: e.target.value })
            }
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="例如：穿着统一制服，背着快递包"
          />
        </div>
      </form>
    </Modal>
  );
}
