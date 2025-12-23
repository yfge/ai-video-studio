import type { AIImageGenerationRequest } from "@/utils/api";

export interface ImageGenerationFormState extends AIImageGenerationRequest {
  size?: string;
}

export interface UploadFormState {
  file: File | null;
  category: string;
  tags: string;
  is_default: boolean;
}
