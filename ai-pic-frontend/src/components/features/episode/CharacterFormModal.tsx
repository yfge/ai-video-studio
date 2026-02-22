"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import type {
  EpisodeCharacter,
  EpisodeCharacterCreate,
  EpisodeCharacterUpdate,
} from "@/utils/api/types";
import { CharacterCommonFields } from "./CharacterCommonFields";

type BaseProps = {
  isOpen: boolean;
  onClose: () => void;
  title: string;
};

type CreateProps = BaseProps & {
  mode: "create";
  onSubmit: (data: EpisodeCharacterCreate) => void | Promise<void>;
};

type EditProps = BaseProps & {
  mode: "edit";
  initialData: EpisodeCharacter;
  onSubmit: (data: EpisodeCharacterUpdate) => void | Promise<void>;
};

export type CharacterFormModalProps = CreateProps | EditProps;

export function CharacterFormModal(props: CharacterFormModalProps) {
  if (props.mode === "create") {
    return <CreateCharacterFormModal {...props} />;
  }
  return <EditCharacterFormModal {...props} />;
}

function CreateCharacterFormModal({
  isOpen,
  onClose,
  onSubmit,
  title,
}: CreateProps) {
  const [formData, setFormData] = useState<EpisodeCharacterCreate>({
    virtual_ip_id: 0,
    character_name: "",
    role_type: "temporary",
    importance: 1,
    personality: "",
    background: "",
    appearance_override: "",
  });

  const handleSubmit = (e: FormEvent) => {
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

        <CharacterCommonFields formData={formData} setFormData={setFormData} />
      </form>
    </Modal>
  );
}

function EditCharacterFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  title,
}: EditProps) {
  const [formData, setFormData] = useState<EpisodeCharacterUpdate>({
    character_name: initialData.character_name || "",
    role_type: initialData.role_type || "temporary",
    importance: initialData.importance || 1,
    personality: initialData.personality || "",
    background: initialData.background || "",
    appearance_override: initialData.appearance_override || "",
    voice_config_override: initialData.voice_config_override,
  });

  const handleSubmit = (e: FormEvent) => {
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
        <CharacterCommonFields formData={formData} setFormData={setFormData} />
      </form>
    </Modal>
  );
}
