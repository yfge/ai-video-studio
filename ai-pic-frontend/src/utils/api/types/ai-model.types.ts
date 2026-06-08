/**
 * AI model type definitions.
 */

// AI model type constants
export const AIModelType = {
  Text: "text_generation",
  Image: "text_to_image",
  Video: "text_to_video",
  Audio: "text_to_speech",
  SpeechToText: "speech_to_text",
  ImageToImage: "image_to_image",
  ImageToVideo: "image_to_video",
  ImageUnderstanding: "image_understanding",
  VideoUnderstanding: "video_understanding",
  TEXT_GENERATION: "text_generation",
  TEXT_TO_IMAGE: "text_to_image",
  IMAGE_TO_IMAGE: "image_to_image",
  TEXT_TO_VIDEO: "text_to_video",
  IMAGE_TO_VIDEO: "image_to_video",
  TEXT_TO_SPEECH: "text_to_speech",
  SPEECH_TO_TEXT: "speech_to_text",
  EMBEDDING: "embedding",
} as const;

// AI model entity
export interface AIModel {
  model_id: string;
  id?: string;
  name: string;
  provider: string;
  type: string;
  capabilities: string[];
  metadata?: Record<string, unknown>;
  is_available?: boolean;
}

// Available models response
export interface AvailableModelsResponse {
  models: AIModel[];
  default?: string;
  count?: number;
  default_model_id?: string;
  categories?: Record<string, AIModel[]>;
}
