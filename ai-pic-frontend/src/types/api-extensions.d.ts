import type {} from "@/utils/api";

declare module "@/utils/api" {
  export interface CreatorInfo {
    id: number
    username: string
    full_name?: string | null
  }

  export interface Environment {
    creator?: CreatorInfo | null
  }

  export interface Story {
    creator?: CreatorInfo | null
  }

  export interface VirtualIP {
    creator?: CreatorInfo | null
  }
}

export {}
