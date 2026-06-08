/**
 * Voice/TTS API endpoints.
 */

import { httpClient } from "../client";
import type {
  VoiceEnums,
  VoiceList,
  VoicePreviewResponse,
} from "../types/voice.types";
import type { ApiResponse } from "../types/common.types";

/**
 * Get voice configuration enums (providers, models, emotions, etc.).
 */
async function getVoiceEnums(): Promise<ApiResponse<VoiceEnums>> {
  return httpClient<VoiceEnums>("/api/v1/voice/enums");
}

/**
 * Get available voices.
 */
async function getVoices(params?: {
  voice_type?: string;
  provider?: string;
  refresh?: boolean;
}): Promise<ApiResponse<VoiceList>> {
  const searchParams = new URLSearchParams();
  if (params?.voice_type) searchParams.append("voice_type", params.voice_type);
  if (params?.provider) searchParams.append("provider", params.provider);
  if (params?.refresh) searchParams.append("refresh", "true");

  const query = searchParams.toString();
  const endpoint = query
    ? `/api/v1/voice/voices?${query}`
    : "/api/v1/voice/voices";
  return httpClient<VoiceList>(endpoint);
}

/**
 * Preview voice with text-to-speech.
 */
async function previewVoice(payload: {
  text: string;
  model: string;
  voice_id?: string;
  provider?: string;
  output_format?: "url" | "hex";
}): Promise<ApiResponse<VoicePreviewResponse>> {
  const body = {
    ...payload,
    output_format: payload.output_format || "url",
    stream: false,
  };
  return httpClient<VoicePreviewResponse>("/api/v1/voice/tts", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * Voice API namespace.
 */
export const voiceAPI = {
  getEnums: getVoiceEnums,
  getVoices,
  preview: previewVoice,
};
