"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { voiceAPI } from "@/utils/api/endpoints";
import type { VoiceConfig, VoiceEnums } from "@/utils/api/types";
import type { AlertOptions } from "@/components/shared/modals/AlertModalProvider";

interface UseVoicePreviewArgs {
  voiceConfig: VoiceConfig;
  setVoiceConfig?: React.Dispatch<React.SetStateAction<VoiceConfig>>;
  voiceEnums: VoiceEnums | null;
  voiceOptions: { value: string; label: string }[];
  defaultText: string;
  showAlert: (options: AlertOptions) => void;
}

const hexToAudioUrl = (hexString: string): string => {
  const bytes = new Uint8Array(
    hexString.match(/.{1,2}/g)?.map((byte) => parseInt(byte, 16)) || [],
  );
  const blob = new Blob([bytes], { type: "audio/mpeg" });
  return URL.createObjectURL(blob);
};

const revokeIfBlob = (url: string | null) => {
  if (url && url.startsWith("blob:")) {
    URL.revokeObjectURL(url);
  }
};

export function useVoicePreview({
  voiceConfig,
  setVoiceConfig,
  voiceEnums,
  voiceOptions,
  defaultText,
  showAlert,
}: UseVoicePreviewArgs) {
  const [previewText, setPreviewText] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);
  const [previewSourceUrl, setPreviewSourceUrl] = useState<string | null>(null);

  const configSignature = useMemo(
    () =>
      `${voiceConfig.provider || ""}|${voiceConfig.model || ""}|${
        voiceConfig.voice_id || ""
      }|${voiceConfig.voice_type || ""}`,
    [
      voiceConfig.model,
      voiceConfig.provider,
      voiceConfig.voice_id,
      voiceConfig.voice_type,
    ],
  );

  const lastConfigRef = useRef(configSignature);

  const resetPreview = useCallback(() => {
    setPreviewAudioUrl((prev) => {
      revokeIfBlob(prev);
      return null;
    });
    setPreviewSourceUrl(null);
  }, []);

  const setPreviewUrls = useCallback(
    (audioUrl: string | null, sourceUrl: string | null) => {
      setPreviewAudioUrl((prev) => {
        revokeIfBlob(prev);
        return audioUrl;
      });
      setPreviewSourceUrl(sourceUrl);
    },
    [],
  );

  const handlePreviewVoice = useCallback(async () => {
    const fallbackProvider =
      voiceConfig.provider || voiceEnums?.providers?.[0]?.value;
    const fallbackModel =
      voiceConfig.model ||
      voiceEnums?.defaults?.tts_model ||
      voiceEnums?.tts_models?.[0]?.value;
    const fallbackVoiceId =
      voiceConfig.voice_id ||
      voiceEnums?.defaults?.voice_id ||
      voiceOptions[0]?.value;

    if (!fallbackProvider) {
      showAlert({ message: "请先选择服务商", variant: "error" });
      return;
    }
    if (!fallbackModel) {
      showAlert({ message: "请先选择语音模型", variant: "error" });
      return;
    }

    if (
      setVoiceConfig &&
      (fallbackProvider !== voiceConfig.provider ||
        fallbackModel !== voiceConfig.model ||
        fallbackVoiceId !== voiceConfig.voice_id)
    ) {
      setVoiceConfig((prev) => ({
        ...prev,
        provider: fallbackProvider,
        model: fallbackModel,
        voice_id: fallbackVoiceId,
      }));
    }

    const text = previewText || defaultText;
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
          setPreviewUrls(audioUrl, res.data.audio_url || null);
        } else {
          setPreviewUrls(null, null);
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
  }, [
    defaultText,
    previewText,
    setPreviewUrls,
    setVoiceConfig,
    showAlert,
    voiceConfig.model,
    voiceConfig.provider,
    voiceConfig.voice_id,
    voiceEnums?.defaults?.tts_model,
    voiceEnums?.defaults?.voice_id,
    voiceEnums?.providers,
    voiceEnums?.tts_models,
    voiceOptions,
  ]);

  useEffect(() => {
    if (!previewText && defaultText) {
      setPreviewText(defaultText);
    }
  }, [defaultText, previewText]);

  useEffect(() => {
    if (lastConfigRef.current !== configSignature) {
      resetPreview();
      lastConfigRef.current = configSignature;
    }
  }, [configSignature, resetPreview]);

  useEffect(() => {
    return () => {
      revokeIfBlob(previewAudioUrl);
    };
  }, [previewAudioUrl]);

  return {
    previewText,
    setPreviewText,
    previewLoading,
    previewAudioUrl,
    previewSourceUrl,
    handlePreviewVoice,
    resetPreview,
  };
}
