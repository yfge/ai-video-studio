import type {
  VoiceConfig,
  VoiceEnums,
  VoiceItem,
  VoiceList,
} from "@/utils/api/types";

export const buildDefaultVoiceSettings = (enums: VoiceEnums): VoiceConfig => {
  const provider = enums.providers?.[0]?.value;
  const model =
    enums.defaults?.tts_model || enums.tts_models?.[0]?.value || undefined;
  const voice_id = enums.defaults?.voice_id || undefined;
  const voice_type = enums.voice_types?.[0]?.value || "system";
  return { provider, model, voice_type, voice_id };
};

export const mergeVoiceSettings = (
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

export const hexToAudioUrl = (hexString: string): string => {
  const bytes = new Uint8Array(
    hexString.match(/.{1,2}/g)?.map((byte) => parseInt(byte, 16)) || [],
  );
  const blob = new Blob([bytes], { type: "audio/mpeg" });
  return URL.createObjectURL(blob);
};

export function buildVoiceOptions(
  voiceList: VoiceList | null,
  voiceTypeFilter: string,
  systemVoices?: VoiceEnums["system_voices"],
): { value: string; label: string }[] {
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
    systemVoices &&
    voiceTypeFilter !== "voice_cloning" &&
    voiceTypeFilter !== "voice_generation"
  ) {
    systemVoices.forEach((item) => {
      options.push({
        value: item.value,
        label: item.label_zh || item.label_en || item.value,
      });
    });
  }
  return options;
}
