"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { voiceAPI } from "@/utils/api/endpoints";
import type {
  VirtualIP,
  VoiceConfig,
  VoiceEnums,
  VoiceList,
} from "@/utils/api/types";
import {
  buildDefaultVoiceSettings,
  buildVoiceOptions,
  hexToAudioUrl,
  mergeVoiceSettings,
} from "./useVirtualIPDetailVoiceUtils";

type ShowAlert = (opts: {
  message: string;
  variant: "success" | "error" | "warning" | "info";
  title?: string;
  confirmText?: string;
  onConfirm?: () => void;
}) => void;

type UseVirtualIPDetailVoiceOptions = {
  showAlert: ShowAlert;
  virtualIPName?: string | null;
};

export function useVirtualIPDetailVoice({
  showAlert,
  virtualIPName,
}: UseVirtualIPDetailVoiceOptions) {
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

  const syncVirtualIPVoice = useCallback(
    (virtualIP: VirtualIP) => {
      const incomingVoice = virtualIP.voice_config;
      setVoiceSettings((prev) => {
        const defaults = voiceEnums
          ? buildDefaultVoiceSettings(voiceEnums)
          : prev;
        return mergeVoiceSettings(prev, defaults, incomingVoice);
      });
      if (!voicePreviewText) {
        setVoicePreviewText(`你好，我是${virtualIP.name}，很高兴认识你。`);
      }
    },
    [voiceEnums, voicePreviewText],
  );

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

  const fetchVoiceList = useCallback(
    async (voiceType: string, provider?: string) => {
      if (!provider) return;
      try {
        setVoiceLoading(true);
        const res = await voiceAPI.getVoices({
          voice_type: voiceType,
          provider,
        });
        if (res.success && res.data) {
          setVoiceList(res.data);
        }
      } catch (error) {
        console.error("Failed to fetch voice list", error);
      } finally {
        setVoiceLoading(false);
      }
    },
    [],
  );

  const voiceOptions = useMemo(
    () =>
      buildVoiceOptions(voiceList, voiceTypeFilter, voiceEnums?.system_voices),
    [voiceList, voiceTypeFilter, voiceEnums?.system_voices],
  );

  const handlePreviewVoice = async () => {
    const fallbackModel =
      voiceSettings.model ||
      voiceEnums?.defaults?.tts_model ||
      voiceEnums?.tts_models?.[0]?.value;
    const fallbackVoiceId =
      voiceSettings.voice_id ||
      voiceEnums?.defaults?.voice_id ||
      voiceOptions[0]?.value;
    const fallbackProvider =
      voiceSettings.provider || voiceEnums?.providers?.[0]?.value;

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

    const text =
      voicePreviewText ||
      `你好，我是${virtualIPName || "角色"}，很高兴认识你。`;
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
          res.data.audio_url ||
          (res.data.audio_hex ? hexToAudioUrl(res.data.audio_hex) : null);
        if (audioUrl) {
          if (previewAudioUrl) {
            URL.revokeObjectURL(previewAudioUrl);
          }
          setPreviewAudioUrl(audioUrl);
        }
        showAlert({ message: "试听已生成", variant: "success" });
      } else {
        showAlert({
          message: `试听失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("Preview failed", error);
      showAlert({ message: "试听失败，请稍后重试", variant: "error" });
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    void fetchVoiceEnums();
  }, [fetchVoiceEnums]);

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
        setVoiceSettings((prev) => ({
          ...prev,
          voice_id: prev.voice_id || first.value,
        }));
      }
    }
  }, [voiceList, voiceTypeFilter, voiceSettings.voice_id, voiceOptions]);

  useEffect(() => {
    if (
      voiceSettings.voice_type &&
      voiceSettings.voice_type !== voiceTypeFilter
    ) {
      setVoiceTypeFilter(voiceSettings.voice_type);
    }
  }, [voiceSettings.voice_type, voiceTypeFilter]);

  return {
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
    syncVirtualIPVoice,
    handlePreviewVoice,
  };
}
