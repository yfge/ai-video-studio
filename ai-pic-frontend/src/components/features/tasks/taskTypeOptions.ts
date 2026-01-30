export type TaskTypeOption = { value: string; label: string };

export const TASK_TYPE_OPTIONS: TaskTypeOption[] = [
  { value: "", label: "全部类型" },
  { value: "story_generation", label: "故事生成" },
  { value: "episode_generation", label: "剧集生成" },
  { value: "script_generation", label: "剧本生成" },
  { value: "script_review", label: "剧本质检" },
  { value: "dialogue_audio_generation", label: "对白音轨生成" },
  { value: "timeline_generation", label: "时间轴生成" },
  { value: "timeline_pipeline", label: "一键时间轴流水线" },
  { value: "storyboard_generation", label: "分镜生成" },
  { value: "storyboard_image_generation", label: "分镜图像生成" },
  { value: "video_generation", label: "视频生成" },
  { value: "virtual_ip_image_generation", label: "虚拟IP文生图" },
  { value: "virtual_ip_image_variant_generation", label: "虚拟IP图生图" },
  { value: "environment_image_generation", label: "环境文生图" },
  { value: "environment_image_variant_generation", label: "环境图生图" },
  { value: "image_generation", label: "图像生成" },
  { value: "image_edit", label: "图像编辑" },
  { value: "image_enhancement", label: "图像增强" },
  { value: "text_generation", label: "文本生成" },
];

export const TASK_TYPE_LABELS = Object.fromEntries(
  TASK_TYPE_OPTIONS.filter((opt) => opt.value).map((opt) => [
    opt.value,
    opt.label,
  ]),
) as Record<string, string>;
