const SINGLE_VIDEO_CREATION_MODE = "single_video";

type MetadataCarrier = {
  extra_metadata?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
};

function metadataOf(entity?: MetadataCarrier | null) {
  return entity?.extra_metadata || entity?.metadata || {};
}

function positiveNumber(value: unknown) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export function isSingleVideoProject(entity?: MetadataCarrier | null) {
  return metadataOf(entity).creation_mode === SINGLE_VIDEO_CREATION_MODE;
}

export function singleVideoProjectEpisodeId(entity?: MetadataCarrier | null) {
  return positiveNumber(metadataOf(entity).episode_id);
}

export function singleVideoProjectTaskId(entity?: MetadataCarrier | null) {
  return positiveNumber(metadataOf(entity).script_task_id);
}

export function singleVideoProjectTitle(title: string, prompt: string) {
  return title.trim() || prompt.trim().slice(0, 40) || "未命名单条视频";
}
