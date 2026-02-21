"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { voiceAPI } from "@/utils/api/endpoints";
import type {
  VoiceConfig,
  VoiceEnums,
  VoiceList,
  VoiceItem,
} from "@/utils/api/types";

interface UseVoiceConfigOptionsArgs {
  voiceConfig: VoiceConfig;
  setVoiceConfig: React.Dispatch<React.SetStateAction<VoiceConfig>>;
}

const buildDefaultVoiceSettings = (enums: VoiceEnums): VoiceConfig => {
  const provider = enums.providers?.[0]?.value;
  const model =
    enums.defaults?.tts_model || enums.tts_models?.[0]?.value || undefined;
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
  voice_type:
    incoming?.voice_type ??
    current.voice_type ??
    defaults.voice_type ??
    "system",
  voice_id: incoming?.voice_id ?? current.voice_id ?? defaults.voice_id,
  display_name: incoming?.display_name ?? current.display_name,
  sample_url: incoming?.sample_url ?? current.sample_url,
});

export function useVoiceConfigOptions({
  voiceConfig,
  setVoiceConfig,
}: UseVoiceConfigOptionsArgs) {
  const [voiceEnums, setVoiceEnums] = useState<VoiceEnums | null>(null);
  const [voiceList, setVoiceList] = useState<VoiceList | null>(null);
  const [voiceTypeFilter, setVoiceTypeFilter] = useState(
    voiceConfig.voice_type || "system",
  );
  const [voiceLoading, setVoiceLoading] = useState(false);

  const hasVoiceConfig = Boolean(
    voiceConfig.provider ||
      voiceConfig.model ||
      voiceConfig.voice_id ||
      voiceConfig.voice_type,
  );

  const fetchVoiceEnums = useCallback(async () => {
    try {
      const res = await voiceAPI.getEnums();
      if (res.success && res.data) {
        setVoiceEnums(res.data);
      }
    } catch (error) {
      console.error("Failed to fetch voice enums", error);
    }
  }, []);

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

  const voiceOptions = useMemo(() => {
    const options: { value: string; label: string }[] = [];
    const pushVoices = (items?: VoiceItem[]) => {
      if (!items) return;
      items.forEach((item) => {
        if (item?.voice_id) {
          options.push({
            value: item.voice_id,
            label: item.voice_name || item.voice_id,
          });
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
        options.push({
          value: item.value,
          label: item.label_zh || item.label_en || item.value,
        });
      });
    }

    return options;
  }, [voiceEnums?.system_voices, voiceList, voiceTypeFilter]);

  useEffect(() => {
    void fetchVoiceEnums();
  }, [fetchVoiceEnums]);

  useEffect(() => {
    if (!voiceEnums || !hasVoiceConfig) return;
    const defaults = buildDefaultVoiceSettings(voiceEnums);
    setVoiceConfig((prev) => mergeVoiceSettings(prev, defaults));
  }, [hasVoiceConfig, setVoiceConfig, voiceEnums]);

  useEffect(() => {
    if (!voiceConfig.provider) {
      setVoiceList(null);
      return;
    }
    void fetchVoiceList(voiceTypeFilter, voiceConfig.provider);
  }, [fetchVoiceList, voiceConfig.provider, voiceTypeFilter]);

  useEffect(() => {
    if (!voiceConfig.provider) return;
    setVoiceConfig((prev) => {
      if (prev.voice_type === voiceTypeFilter) return prev;
      return { ...prev, voice_type: voiceTypeFilter, voice_id: undefined };
    });
  }, [setVoiceConfig, voiceConfig.provider, voiceTypeFilter]);

  useEffect(() => {
    if (voiceConfig.voice_type && voiceConfig.voice_type !== voiceTypeFilter) {
      setVoiceTypeFilter(voiceConfig.voice_type);
    }
  }, [voiceConfig.voice_type, voiceTypeFilter]);

  useEffect(() => {
    if (!voiceConfig.provider || voiceConfig.voice_id) return;
    const first = voiceOptions[0];
    if (first) {
      setVoiceConfig((prev) =>
        prev.voice_id ? prev : { ...prev, voice_id: first.value },
      );
    }
  }, [
    setVoiceConfig,
    voiceConfig.provider,
    voiceConfig.voice_id,
    voiceOptions,
  ]);

  return {
    voiceEnums,
    voiceTypeFilter,
    setVoiceTypeFilter,
    voiceOptions,
    voiceLoading,
  };
}
