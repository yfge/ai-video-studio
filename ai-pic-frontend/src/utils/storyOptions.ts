import type { StoryGenerationRequest } from "@/utils/api/types";

export const STORY_GENRES = [
  { value: "drama", label: "剧情" },
  { value: "comedy", label: "喜剧" },
  { value: "romance", label: "爱情" },
  { value: "thriller", label: "惊悚" },
  { value: "action", label: "动作" },
  { value: "fantasy", label: "奇幻" },
  { value: "sci-fi", label: "科幻" },
  { value: "horror", label: "恐怖" },
  { value: "mystery", label: "悬疑" },
  { value: "historical", label: "历史" },
];

export const STORY_STATUSES = [
  { value: "", label: "全部状态" },
  { value: "draft", label: "草稿" },
  { value: "approved", label: "已批准" },
  { value: "published", label: "已发布" },
];

export type StoryFormat = "short_drama" | "tv_series" | "film";

export const STORY_FORMATS: Array<{ value: StoryFormat; label: string }> = [
  { value: "short_drama", label: "短剧" },
  { value: "tv_series", label: "电视剧/网剧" },
  { value: "film", label: "电影" },
];

export type StoryAspectRatio = "9:16" | "16:9";

export const STORY_ASPECT_RATIOS: Array<{
  value: StoryAspectRatio;
  label: string;
}> = [
  { value: "9:16", label: "9:16 竖屏" },
  { value: "16:9", label: "16:9 横屏" },
];

export type StoryGenerationForm = StoryGenerationRequest & {
  story_format: StoryFormat;
};

export const STORY_GENERATE_DEFAULTS: StoryGenerationForm = {
  title: "",
  story_format: "short_drama",
  genre: "drama",
  market_region: "",
  micro_genre: "",
  pacing_template: "",
  theme: "",
  target_audience: "",
  duration_minutes: 30,
  default_aspect_ratio: "9:16",
  character_ids: [],
  setting_time: "",
  setting_location: "",
  world_building: "",
  additional_requirements: "",
  style_preferences: [],
  content_restrictions: [],
  tags: [],
  model: "",
  temperature: 0.7,
};
