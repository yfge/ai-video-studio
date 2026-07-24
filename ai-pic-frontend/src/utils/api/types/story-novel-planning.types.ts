import type { StorySeedStructuredChapter } from "./story-seed.types";

export interface NovelLengthRange {
  min_chars: number;
  target_chars: number;
  max_chars: number;
}

export interface NovelLengthProfile extends NovelLengthRange {
  profile_id: string;
  name: string;
  count_mode?: "non_whitespace_chars";
}

export interface NovelGenerationLengthProfile {
  profile_id: string;
  profile_name?: string;
  count_mode?: "non_whitespace_chars";
  default_min_chars: number;
  default_target_chars: number;
  default_max_chars: number;
}

export interface NovelChapterLength extends NovelLengthRange {
  source: "profile_default" | "chapter_override";
}

export type NovelChapterLengthOverrides = Record<string, NovelLengthRange>;

export interface StoryNovelPlanChapter extends StorySeedStructuredChapter {
  length?: NovelChapterLength;
  actual_chars?: number;
  generation_status?: string;
  extraction_status?: string;
}

export interface StoryNovelLengthSpecPayload {
  length_profile_id: string;
  custom_length_profile: NovelLengthRange | null;
  chapter_length_overrides: NovelChapterLengthOverrides;
}

export interface StoryNovelCreateRevisionPayload
  extends StoryNovelLengthSpecPayload {
  style: "prose";
  model?: string;
}

export interface StoryNovelUpdateLengthSpecPayload
  extends StoryNovelLengthSpecPayload {
  expected_plan_version: number;
  model?: string | null;
}
