"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  apiClient,
  virtualIPAPI,
  voiceAPI,
  type VirtualIP,
  type VoiceConfig,
  type VoiceEnums,
  type VoiceList,
  type VoiceItem,
} from "@/utils/api";

export interface UseVirtualIPDetailOptions {
  ipKey: string;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
    title?: string;
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
  router: { push: (path: string) => void };
}

export interface EditFormState {
  name: string;
  description: string;
  tags: string[];
  background_story: string;
}

const buildDefaultVoiceSettings = (enums: VoiceEnums): VoiceConfig => {
  const provider = enums.providers?.[0]?.value;
  const model = enums.defaults?.tts_model || enums.tts_models?.[0]?.value || undefined;
  const voice_id = enums.defaults?.voice_id || undefined;
  const voice_type = enums.voice_types?.[0]?.value || "system";
  return { provider, model, voice_type, voice_id };
};

const mergeVoiceSettings = (
  current: VoiceConfig,
  defaults: VoiceConfig,
  incoming?: VoiceConfig,
): VoiceConfig => ({
  provider: incoming?.provider ?? current.provider ?? defaults.provider,
  model: incoming?.model ?? current.model ?? defaults.model,
  voice_type: incoming?.voice_type ?? current.voice_type ?? defaults.voice_type ?? "system",
  voice_id: incoming?.voice_id ?? current.voice_id ?? defaults.voice_id,
  display_name: incoming?.display_name ?? current.display_name,
  sample_url: incoming?.sample_url ?? current.sample_url,
});

export const hexToAudioUrl = (hexString: string): string => {
  const bytes = new Uint8Array(hexString.match(/.{1,2}/g)?.map((byte) => parseInt(byte, 16)) || []);
  const blob = new Blob([bytes], { type: "audio/mpeg" });
  return URL.createObjectURL(blob);
};

export function useVirtualIPDetail({ ipKey, showAlert, router }: UseVirtualIPDetailOptions) {
  // Core state
  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<EditFormState>({
    name: "",
    description: "",
    tags: [],
    background_story: "",
  });

  // Voice state
  const [voiceEnums, setVoiceEnums] = useState<VoiceEnums | null>(null);
  const [voiceList, setVoiceList] = useState<VoiceList | null>(null);
  const [voiceTypeFilter, setVoiceTypeFilter] = useState("system");
  const [voiceSettings, setVoiceSettings] = useState<VoiceConfig>({
    provider: undefined,
    model: undefined,
    voice_type: "system",
    voice_id: undefined,
  });
  const [voicePreviewText, setVoicePreviewText] = useState("");
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);

  // Fetch voice enums
  const fetchVoiceEnums = useCallback(async () => {
    try {
      const res = await voiceAPI.getEnums();
      if (res.success && res.data) {
        setVoiceEnums(res.data);
        if (!voicePreviewText) {
          setVoicePreviewText("你好，我是你的虚拟角色，很高兴认识你。");
        }
        const defaults = buildDefaultVoiceSettings(res.data);
        setVoiceSettings((prev) => mergeVoiceSettings(prev, defaults));
      }
    } catch (error) {
      console.error("Failed to fetch voice enums", error);
    }
  }, [voicePreviewText]);

  // Fetch voice list
  const fetchVoiceList = useCallback(async (voiceType: string, provider?: string) => {
    if (!provider) return;
    try {
      setVoiceLoading(true);
      const res = await voiceAPI.getVoices({ voice_type: voiceType, provider });
      if (res.success && res.data) {
        setVoiceList(res.data);
      }
    } catch (error) {
      console.error("Failed to fetch voice list", error);
    } finally {
      setVoiceLoading(false);
    }
  }, []);

  // Fetch virtual IP
  const fetchVirtualIP = useCallback(async () => {
    try {
      setLoading(true);
      const response = await virtualIPAPI.getVirtualIP(ipKey);

      if (response.success && response.data) {
        setVirtualIP(response.data);
        setEditForm({
          name: response.data.name,
          description: response.data.description || "",
          tags: response.data.tags || [],
          background_story: response.data.background_story || "",
        });
        const incomingVoice = response.data.voice_config;
        setVoiceSettings((prev) => {
          const defaults = voiceEnums ? buildDefaultVoiceSettings(voiceEnums) : prev;
          return mergeVoiceSettings(prev, defaults, incomingVoice);
        });
        if (!voicePreviewText) {
          setVoicePreviewText(`你好，我是${response.data.name}，很高兴认识你。`);
        }
      } else {
        console.error("Failed to fetch virtual IP:", response.error);
        showAlert({ message: "获取虚拟IP失败", variant: "error" });
      }
    } catch (error) {
      console.error("Error fetching virtual IP:", error);
      showAlert({ message: "获取虚拟IP失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [ipKey, showAlert, voiceEnums, voicePreviewText]);

  // Update virtual IP
  const handleUpdateIP = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const identifier = virtualIP?.business_id || ipKey;
      const response = await virtualIPAPI.updateVirtualIP(identifier, {
        ...editForm,
        voice_config: voiceSettings,
      });
      if (response.success && response.data) {
        setVirtualIP(response.data);
        setEditing(false);
        showAlert({ message: "更新成功", variant: "success" });
      } else {
        showAlert({ message: `更新失败：${response.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("Error updating virtual IP:", error);
      showAlert({ message: "更新失败，请稍后重试", variant: "error" });
    }
  };

  // Delete virtual IP
  const handleDeleteIP = () => {
    showAlert({
      title: "确认删除虚拟IP",
      message: "确定删除该虚拟IP吗？此操作不可恢复！",
      variant: "warning",
      confirmText: "删除",
      onConfirm: async () => {
        try {
          const identifier = virtualIP?.business_id || ipKey;
          const response = await virtualIPAPI.deleteVirtualIP(identifier);
          if (response.success) {
            showAlert({ message: "删除成功", variant: "success" });
            router.push("/virtual-ip");
          } else {
            showAlert({ message: `删除失败：${response.error || "未知错误"}`, variant: "error" });
          }
        } catch (error) {
          console.error("Error deleting virtual IP:", error);
          showAlert({ message: "删除失败，请稍后重试", variant: "error" });
        }
      },
    });
  };

  // Tag management
  const addTag = (tag: string) => {
    if (tag && !editForm.tags.includes(tag)) {
      setEditForm({ ...editForm, tags: [...editForm.tags, tag] });
    }
  };

  const removeTag = (tagToRemove: string) => {
    setEditForm({ ...editForm, tags: editForm.tags.filter((tag) => tag !== tagToRemove) });
  };

  // Voice options
  const voiceOptions = useMemo(() => {
    const options: { value: string; label: string }[] = [];
    const pushVoices = (items?: VoiceItem[]) => {
      if (!items) return;
      items.forEach((item) => {
        if (item?.voice_id) {
          options.push({ value: item.voice_id, label: item.voice_name || item.voice_id });
        }
      });
    };

    if (voiceList) {
      if (voiceTypeFilter === "all") {
        pushVoices(voiceList.system_voice);
        pushVoices(voiceList.voice_cloning);
        pushVoices(voiceList.voice_generation);
      } else if (voiceTypeFilter === "system") {
        pushVoices(voiceList.system_voice);
      } else if (voiceTypeFilter === "voice_cloning") {
        pushVoices(voiceList.voice_cloning);
      } else if (voiceTypeFilter === "voice_generation") {
        pushVoices(voiceList.voice_generation);
      }
    }
    if (
      !options.length &&
      voiceEnums?.system_voices &&
      voiceTypeFilter !== "voice_cloning" &&
      voiceTypeFilter !== "voice_generation"
    ) {
      voiceEnums.system_voices.forEach((item) => {
        options.push({ value: item.value, label: item.label_zh || item.label_en || item.value });
      });
    }
    return options;
  }, [voiceList, voiceTypeFilter, voiceEnums?.system_voices]);

  // Voice preview
  const handlePreviewVoice = async () => {
    const fallbackModel =
      voiceSettings.model || voiceEnums?.defaults?.tts_model || voiceEnums?.tts_models?.[0]?.value;
    const fallbackVoiceId =
      voiceSettings.voice_id || voiceEnums?.defaults?.voice_id || voiceOptions[0]?.value;
    const fallbackProvider = voiceSettings.provider || voiceEnums?.providers?.[0]?.value;

    if (!fallbackProvider) {
      showAlert({ message: "请先选择服务商", variant: "error" });
      return;
    }
    if (!fallbackModel) {
      showAlert({ message: "请先选择语音模型", variant: "error" });
      return;
    }

    if (
      fallbackModel !== voiceSettings.model ||
      fallbackVoiceId !== voiceSettings.voice_id ||
      fallbackProvider !== voiceSettings.provider
    ) {
      setVoiceSettings((prev) => ({
        ...prev,
        provider: fallbackProvider,
        model: fallbackModel,
        voice_id: fallbackVoiceId,
      }));
    }

    const text = voicePreviewText || `你好，我是${virtualIP?.name || "角色"}，很高兴认识你。`;
    setPreviewLoading(true);
    try {
      const res = await voiceAPI.preview({
        text,
        model: fallbackModel,
        voice_id: fallbackVoiceId,
        provider: fallbackProvider,
        output_format: "url",
      });
      if (res.success && res.data) {
        const audioUrl =
          res.data.audio_url || (res.data.audio_hex ? hexToAudioUrl(res.data.audio_hex) : null);
        if (audioUrl) {
          if (previewAudioUrl) {
            URL.revokeObjectURL(previewAudioUrl);
          }
          setPreviewAudioUrl(audioUrl);
        }
        showAlert({ message: "试听已生成", variant: "success" });
      } else {
        showAlert({ message: `试听失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("Preview failed", error);
      showAlert({ message: "试听失败，请稍后重试", variant: "error" });
    } finally {
      setPreviewLoading(false);
    }
  };

  // Effects
  useEffect(() => {
    apiClient.updateToken();
  }, []);

  useEffect(() => {
    void fetchVoiceEnums();
  }, [fetchVoiceEnums]);

  useEffect(() => {
    if (ipKey) {
      void fetchVirtualIP();
    }
  }, [fetchVirtualIP, ipKey]);

  useEffect(() => {
    if (voiceSettings.provider) {
      void fetchVoiceList(voiceTypeFilter, voiceSettings.provider);
    }
  }, [fetchVoiceList, voiceSettings.provider, voiceTypeFilter]);

  useEffect(() => {
    setVoiceSettings((prev) => {
      if (prev.voice_type === voiceTypeFilter) return prev;
      return { ...prev, voice_type: voiceTypeFilter, voice_id: undefined };
    });
  }, [voiceTypeFilter]);

  useEffect(() => {
    if (!voiceList) return;
    if (!voiceSettings.voice_id) {
      const first = voiceOptions[0];
      if (first) {
        setVoiceSettings((prev) => ({ ...prev, voice_id: prev.voice_id || first.value }));
      }
    }
  }, [voiceList, voiceTypeFilter, voiceSettings.voice_id, voiceOptions]);

  useEffect(() => {
    if (voiceSettings.voice_type && voiceSettings.voice_type !== voiceTypeFilter) {
      setVoiceTypeFilter(voiceSettings.voice_type);
    }
  }, [voiceSettings.voice_type, voiceTypeFilter]);

  return {
    // Core state
    virtualIP,
    loading,
    editing,
    setEditing,
    editForm,
    setEditForm,

    // Voice state
    voiceEnums,
    voiceTypeFilter,
    setVoiceTypeFilter,
    voiceSettings,
    setVoiceSettings,
    voicePreviewText,
    setVoicePreviewText,
    voiceLoading,
    previewLoading,
    previewAudioUrl,
    voiceOptions,

    // Handlers
    handleUpdateIP,
    handleDeleteIP,
    addTag,
    removeTag,
    handlePreviewVoice,
  };
}
