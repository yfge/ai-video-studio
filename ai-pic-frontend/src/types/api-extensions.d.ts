import type {} from "@/utils/api";
import type {} from "@/utils/api/types";

declare module "@/utils/api" {
  export interface CreatorInfo {
    id: number;
    username: string;
    full_name?: string | null;
  }

  export interface Environment {
    creator?: CreatorInfo | null;
  }

  export interface Story {
    creator?: CreatorInfo | null;
  }

  export interface VirtualIP {
    creator?: CreatorInfo | null;
  }
}

declare module "@/utils/api/types" {
  export interface CreatorInfo {
    id: number;
    username: string;
    full_name?: string | null;
  }

  export interface Environment {
    creator?: CreatorInfo | null;
  }

  export interface Story {
    creator?: CreatorInfo | null;
  }

  export interface VirtualIP {
    creator?: CreatorInfo | null;
  }
}

export {};
