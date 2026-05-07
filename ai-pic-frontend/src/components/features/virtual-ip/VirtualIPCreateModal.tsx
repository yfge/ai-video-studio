"use client";

import {
  useCallback,
  useEffect,
  type Dispatch,
  type FormEvent,
  type SetStateAction,
} from "react";
import type { VoiceConfig } from "@/utils/api/types";
import { CreationOverlay, SmartInputField } from "@/components/shared";
import type { AlertOptions } from "@/components/shared/modals/AlertModalProvider";
import { useVoiceConfigOptions } from "@/hooks/useVoiceConfigOptions";
import { useVoicePreview } from "@/hooks/useVoicePreview";
import type { VirtualIPCreateFormState } from "@/utils/virtual-ip/types";
import { VirtualIPAIIntroSection } from "./VirtualIPAIIntroSection";
import {
  VirtualIPCreateFooter,
  VirtualIPStatusSettings,
} from "./VirtualIPCreateModalParts";
import { VirtualIPTagsField } from "./VirtualIPTagsField";
import { VirtualIPVoicePreviewSection } from "./VirtualIPVoicePreviewSection";
import { VirtualIPVoiceSettingsForm } from "./VirtualIPVoiceSettingsForm";

interface VirtualIPCreateModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (
    event: FormEvent,
    previewSourceUrl?: string,
    previewText?: string,
  ) => void;
  showAlert: (options: AlertOptions) => void;
  aiBrief: string;
  setAiBrief: (value: string) => void;
  aiGenerating: boolean;
  onGenerateAI: () => void;
  formState: VirtualIPCreateFormState;
  setFormState: Dispatch<SetStateAction<VirtualIPCreateFormState>>;
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
}

export function VirtualIPCreateModal({
  open,
  onClose,
  onSubmit,
  showAlert,
  aiBrief,
  setAiBrief,
  aiGenerating,
  onGenerateAI,
  formState,
  setFormState,
  addTag,
  removeTag,
}: VirtualIPCreateModalProps) {
  const updateField = <K extends keyof VirtualIPCreateFormState>(
    key: K,
    value: VirtualIPCreateFormState[K],
  ) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
  };

  const setVoiceConfig = useCallback(
    (next: SetStateAction<VoiceConfig>) => {
      setFormState((prev) => ({
        ...prev,
        voice_config:
          typeof next === "function" ? next(prev.voice_config) : next,
      }));
    },
    [setFormState],
  );

  const {
    voiceEnums,
    voiceOptions,
    voiceLoading,
    voiceTypeFilter,
    setVoiceTypeFilter,
  } = useVoiceConfigOptions({
    voiceConfig: formState.voice_config,
    setVoiceConfig,
  });

  const defaultPreviewText = formState.name
    ? `你好，我是${formState.name}，很高兴认识你。`
    : "你好，我是你的虚拟角色，很高兴认识你。";
  const {
    previewText,
    setPreviewText,
    previewLoading,
    previewAudioUrl,
    previewSourceUrl,
    handlePreviewVoice,
    resetPreview,
  } = useVoicePreview({
    voiceConfig: formState.voice_config,
    setVoiceConfig,
    voiceEnums,
    voiceOptions,
    defaultText: defaultPreviewText,
    showAlert,
  });

  useEffect(() => {
    if (!open) {
      resetPreview();
    }
  }, [open, resetPreview]);

  const canPreview = Boolean(
    formState.voice_config.provider || voiceEnums?.providers?.length,
  );

  const handleSubmit = (event: FormEvent) => {
    onSubmit(event, previewSourceUrl || undefined, previewText);
  };

  return (
    <CreationOverlay
      open={open}
      title="创建 IP"
      subtitle="从角色资产开始组织故事和剧集"
      onClose={onClose}
      widthClassName="max-w-5xl"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700">
          IP 资产迁移中，新建 IP 将作为故事生产入口。
        </div>

        <SmartInputField
          label="名称 *"
          value={formState.name}
          onChange={(value) => updateField("name", value)}
          placeholder="输入虚拟IP名称，如：小雅、李教授、小明等"
          type="input"
          showAIAssist={false}
        />

        <VirtualIPAIIntroSection
          name={formState.name}
          aiBrief={aiBrief}
          setAiBrief={setAiBrief}
          aiGenerating={aiGenerating}
          onGenerateAI={onGenerateAI}
        />

        <SmartInputField
          label="角色描述"
          value={formState.description}
          onChange={(value) => updateField("description", value)}
          placeholder="描述这个角色的基本特征、性格、外貌等"
          type="textarea"
          rows={3}
          aiSuggestType="description"
          contextData={{ name: formState.name }}
          showAIAssist={false}
        />

        <SmartInputField
          label="背景故事"
          value={formState.background_story}
          onChange={(value) => updateField("background_story", value)}
          placeholder="描述角色的成长经历、重要事件、生活背景等"
          type="textarea"
          rows={4}
          aiSuggestType="background_story"
          contextData={{
            name: formState.name,
            description: formState.description,
          }}
          showAIAssist={false}
        />

        <SmartInputField
          label="人物小传"
          value={formState.biography}
          onChange={(value) => updateField("biography", value)}
          placeholder="详细介绍角色的生平、成就、重要关系等"
          type="textarea"
          rows={4}
          aiSuggestType="biography"
          contextData={{
            name: formState.name,
            description: formState.description,
            basicInfo: formState.background_story,
          }}
          showAIAssist={false}
        />

        <SmartInputField
          label="风格提示词"
          value={formState.style_prompt}
          onChange={(value) => updateField("style_prompt", value)}
          placeholder="用于图像生成的风格提示词（可在生成后微调）"
          type="textarea"
          rows={4}
          showAIAssist={false}
        />

        <VirtualIPVoiceSettingsForm
          voiceEnums={voiceEnums}
          voiceTypeFilter={voiceTypeFilter}
          setVoiceTypeFilter={setVoiceTypeFilter}
          voiceSettings={formState.voice_config}
          setVoiceSettings={setVoiceConfig}
          voiceLoading={voiceLoading}
          voiceOptions={voiceOptions}
        />

        <VirtualIPVoicePreviewSection
          previewText={previewText}
          setPreviewText={setPreviewText}
          previewLoading={previewLoading}
          previewAudioUrl={previewAudioUrl}
          onPreview={handlePreviewVoice}
          canPreview={canPreview}
        />

        <VirtualIPStatusSettings
          isActive={formState.is_active}
          isPublic={formState.is_public}
          onActiveChange={(value) => updateField("is_active", value)}
          onPublicChange={(value) => updateField("is_public", value)}
        />

        <VirtualIPTagsField
          tags={formState.tags}
          addTag={addTag}
          removeTag={removeTag}
        />

        <VirtualIPCreateFooter onClose={onClose} />
      </form>
    </CreationOverlay>
  );
}
