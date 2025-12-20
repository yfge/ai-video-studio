import type { VoiceConfig } from '@/utils/api'

export interface VirtualIPCreateFormState {
  name: string
  description: string
  tags: string[]
  background_story: string
  biography: string
  style_prompt: string
  style_reference_images: string[]
  voice_config: VoiceConfig
  is_active: boolean
  is_public: boolean
}
