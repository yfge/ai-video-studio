import type { VoiceConfig } from '@/utils/api'
import type { VirtualIPCreateFormState } from './types'

export const createEmptyForm = (): VirtualIPCreateFormState => ({
  name: '',
  description: '',
  tags: [],
  background_story: '',
  biography: '',
  style_prompt: '',
  voice_config: {},
  is_active: true,
  is_public: false,
})

export const normalizeText = (value: string) => value.trim()

export const normalizeOptionalText = (value: string) => {
  const trimmed = normalizeText(value)
  return trimmed ? trimmed : undefined
}

export const normalizeArray = (values: string[]) =>
  values.map((value) => normalizeText(value)).filter((value) => value.length > 0)

export const normalizeVoiceConfig = (config: VoiceConfig) => {
  const entries = Object.entries(config)
    .map(([key, value]) => [key, typeof value === 'string' ? normalizeText(value) : value])
    .filter(([, value]) => Boolean(value))

  if (entries.length === 0) {
    return undefined
  }

  return Object.fromEntries(entries) as VoiceConfig
}
