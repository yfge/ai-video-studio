export type EnvironmentFormState = {
  name: string
  category: string
  tags: string[]
  description: string
  reference_images: string[]
}

export type EnvironmentImage = {
  url: string
}

export type GenerationFormState = {
  enabled: boolean
  prompt: string
  model: string
  count: number
  size: string
  style: string
}

export const EMPTY_ENV_FORM: EnvironmentFormState = {
  name: '',
  category: 'indoor',
  tags: [],
  description: '',
  reference_images: [],
}

export const EMPTY_GENERATION: GenerationFormState = {
  enabled: false,
  prompt: '',
  model: '',
  count: 1,
  size: '',
  style: 'realistic',
}
