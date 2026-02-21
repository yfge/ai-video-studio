"use client";

import { useCallback, useState, type FormEvent } from "react";
import { virtualIPAPI } from "@/utils/api/endpoints";
import type { VirtualIP } from "@/utils/api/types";
import type { AlertOptions } from "@/components/shared/modals/AlertModalProvider";
import {
  createEmptyForm,
  normalizeArray,
  normalizeOptionalText,
  normalizeText,
  normalizeVoiceConfig,
} from "@/utils/virtual-ip/createFormUtils";
import type { VirtualIPCreateFormState } from "@/utils/virtual-ip/types";
import { saveVirtualIPVoiceSample } from "@/utils/virtual-ip/voiceSampleApi";

interface UseVirtualIPCreateFormOptions {
  showAlert: (options: AlertOptions) => void;
  onCreated: (virtualIP: VirtualIP) => void;
}

export function useVirtualIPCreateForm({
  showAlert,
  onCreated,
}: UseVirtualIPCreateFormOptions) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiBrief, setAiBrief] = useState("");
  const [formState, setFormState] =
    useState<VirtualIPCreateFormState>(createEmptyForm);

  const resetForm = useCallback(() => {
    setFormState(createEmptyForm());
    setAiBrief("");
  }, []);

  const handleCloseCreateForm = useCallback(() => {
    setShowCreateForm(false);
    resetForm();
  }, [resetForm]);

  const addTag = useCallback((tag: string) => {
    const cleaned = normalizeText(tag);
    if (!cleaned) {
      return;
    }

    setFormState((prev) =>
      prev.tags.includes(cleaned)
        ? prev
        : { ...prev, tags: [...prev.tags, cleaned] },
    );
  }, []);

  const removeTag = useCallback((tagToRemove: string) => {
    setFormState((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  }, []);

  const handleCreateIP = useCallback(
    async (e: FormEvent, previewSourceUrl?: string, previewText?: string) => {
      e.preventDefault();

      if (!formState.name.trim()) {
        showAlert({ message: "请填写虚拟IP名称", variant: "warning" });
        return;
      }

      const payload = {
        name: normalizeText(formState.name),
        description: normalizeOptionalText(formState.description),
        tags: normalizeArray(formState.tags),
        background_story: normalizeOptionalText(formState.background_story),
        biography: normalizeOptionalText(formState.biography),
        style_prompt: normalizeOptionalText(formState.style_prompt),
        voice_config: normalizeVoiceConfig(formState.voice_config),
        is_active: formState.is_active,
        is_public: formState.is_public,
      };

      try {
        const response = await virtualIPAPI.createVirtualIP(payload);
        if (response.success && response.data) {
          onCreated(response.data);
          setShowCreateForm(false);
          resetForm();
          if (previewSourceUrl) {
            const normalizedPreviewText = previewText
              ? normalizeOptionalText(previewText)
              : undefined;
            try {
              const previewResponse = await saveVirtualIPVoiceSample({
                businessId: response.data.business_id,
                sourceUrl: previewSourceUrl,
                previewText: normalizedPreviewText,
              });
              if (!previewResponse.success) {
                showAlert({
                  message: `试听保存失败：${
                    previewResponse.error || "未知错误"
                  }`,
                  variant: "warning",
                });
              }
            } catch (previewError) {
              console.error("试听保存失败:", previewError);
              showAlert({
                message: "试听保存失败，请稍后重试",
                variant: "warning",
              });
            }
          }
        } else {
          showAlert({
            message: `创建失败: ${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      } catch (error) {
        console.error("创建虚拟IP出错:", error);
        showAlert({ message: "创建失败，请重试", variant: "error" });
      }
    },
    [formState, onCreated, resetForm, showAlert],
  );

  const runGenerateAllAI = useCallback(async () => {
    if (!formState.name.trim()) {
      showAlert({ message: "请先填写名称", variant: "warning" });
      return;
    }

    if (
      !aiBrief.trim() &&
      !formState.description.trim() &&
      !formState.background_story.trim() &&
      !formState.biography.trim()
    ) {
      showAlert({
        message: "请在名称下方补充“整体介绍”（或先手动写一些内容）",
        variant: "warning",
      });
      return;
    }

    const hasExisting =
      Boolean(formState.description.trim()) ||
      Boolean(formState.background_story.trim()) ||
      Boolean(formState.biography.trim()) ||
      Boolean(formState.style_prompt.trim()) ||
      formState.tags.length > 0;

    const doGenerate = async () => {
      setAiGenerating(true);
      try {
        const basicParts: string[] = [];
        if (aiBrief.trim()) basicParts.push(`整体介绍：${aiBrief.trim()}`);
        if (formState.description.trim())
          basicParts.push(`角色描述：${formState.description.trim()}`);
        if (formState.background_story.trim())
          basicParts.push(`背景故事：${formState.background_story.trim()}`);
        if (formState.biography.trim())
          basicParts.push(`人物小传：${formState.biography.trim()}`);
        if (formState.tags.length > 0)
          basicParts.push(`标签：${formState.tags.join("、")}`);
        const basicInfo = basicParts.join("\n").trim() || undefined;

        const resp = await virtualIPAPI.generateAIContent({
          name: formState.name.trim(),
          basic_info: basicInfo,
          style_preference: undefined,
          image_category: "portrait",
        });
        if (!resp.success || !resp.data) {
          showAlert({
            message: `AI生成失败: ${resp.error || "未知错误"}`,
            variant: "error",
          });
          return;
        }
        const data = resp.data;
        const nextTags = Array.isArray(data.tags)
          ? normalizeArray(data.tags)
          : [];
        setFormState((prev) => ({
          ...prev,
          description: data.description || "",
          background_story: data.background_story || "",
          biography: data.biography || "",
          style_prompt: data.style_prompt || "",
          tags: nextTags.length > 0 ? nextTags : prev.tags,
        }));
      } catch (err) {
        console.error("AI一键生成失败:", err);
        showAlert({ message: "AI生成失败，请重试", variant: "error" });
      } finally {
        setAiGenerating(false);
      }
    };

    if (!hasExisting) {
      await doGenerate();
      return;
    }

    showAlert({
      title: "确认覆盖已填写内容",
      message:
        "AI一键生成将覆盖当前已填写的描述/背景故事/小传/风格提示词/标签，是否继续？",
      variant: "warning",
      confirmText: "继续生成",
      onConfirm: () => {
        void doGenerate();
      },
    });
  }, [aiBrief, formState, showAlert]);

  return {
    showCreateForm,
    setShowCreateForm,
    aiGenerating,
    aiBrief,
    setAiBrief,
    formState,
    setFormState,
    handleCreateIP,
    addTag,
    removeTag,
    runGenerateAllAI,
    handleCloseCreateForm,
  };
}
