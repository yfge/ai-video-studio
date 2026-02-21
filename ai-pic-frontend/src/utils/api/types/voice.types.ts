/**
 * Voice-related type definitions for TTS.
 */

// Voice option for selection
export interface VoiceOption {
  value: string;
  label_zh: string;
  label_en: string;
  language?: string;
}

// Voice item from catalog
export interface VoiceItem {
  voice_id: string;
  voice_name: string;
  language: string;
  created_time?: number;
}

// Voice enums for UI configuration
export interface VoiceEnums {
  providers: VoiceOption[];
  voice_types: VoiceOption[];
  tts_models: VoiceOption[];
  emotions: VoiceOption[];
  language_boost: VoiceOption[];
  output_formats: VoiceOption[];
  audio_formats: VoiceOption[];
  sample_rates: VoiceOption[];
  bitrates: VoiceOption[];
  channels: VoiceOption[];
  music_models: VoiceOption[];
  defaults: Record<string, string>;
  system_voices: VoiceOption[];
}

// Voice list response
export interface VoiceList {
  system_voice: VoiceItem[];
  voice_cloning: VoiceItem[];
  voice_generation: VoiceItem[];
  trace_id?: string;
  base_resp?: Record<string, unknown>;
}

// Voice configuration for character
export interface VoiceConfig {
  provider?: string;
  model?: string;
  voice_id?: string;
  voice_type?: string;
  tts_model?: string;
  display_name?: string;
  sample_url?: string;
  emotion?: string;
  speed?: number;
  vol?: number;
  pitch?: number;
}

// Voice preview response
export interface VoicePreviewResponse {
  audio_url?: string;
  audio_hex?: string;
  subtitle_file?: string;
  trace_id?: string;
  extra_info?: Record<string, unknown>;
  base_resp?: Record<string, unknown>;
}
