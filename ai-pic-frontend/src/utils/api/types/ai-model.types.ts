/**
 * AI model type definitions.
 */

// AI model type constants
export const AIModelType = {
  TEXT_GENERATION: "text_generation",
  TEXT_TO_IMAGE: "text_to_image",
  IMAGE_TO_IMAGE: "image_to_image",
  TEXT_TO_VIDEO: "text_to_video",
  IMAGE_TO_VIDEO: "image_to_video",
  TEXT_TO_SPEECH: "text_to_speech",
  SPEECH_TO_TEXT: "speech_to_text",
  EMBEDDING: "embedding",
} as const;

export type AIModelTypeValue = (typeof AIModelType)[keyof typeof AIModelType];

// AI model entity
export interface AIModel {
  id: string;
  model_id?: string; // Backend may return enriched model_id like "provider:id"
  name: string;
  provider: string;
  type: AIModelTypeValue;
  capabilities?: string[];
  metadata?: Record<string, unknown>;
  is_available?: boolean;
}

// Available models response
export interface AvailableModelsResponse {
  models: AIModel[];
  default_model_id?: string;
  categories?: Record<string, AIModel[]>;
}
