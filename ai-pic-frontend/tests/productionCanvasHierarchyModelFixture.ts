import type {
  Episode,
  Script,
  Story,
  TimelineClipAssetResponse,
  TimelineClipTaskItem,
  TimelineResponse,
  VirtualIP,
  VirtualIPEnvironmentLink,
} from "../src/utils/api/types";

export function virtualIp(id: number): VirtualIP {
  return {
    id,
    business_id: `ip-${id}`,
    name: `IP ${id}`,
    tags: [],
    is_active: true,
    is_public: false,
    created_at: "2026-01-01T00:00:00Z",
  };
}

export function story(id: number, ipIds: number[]): Story {
  return {
    id,
    business_id: `story-${id}`,
    title: `故事 ${id}`,
    genre: "剧情",
    status: "ready",
    is_public: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    story_characters: ipIds.map((virtual_ip_id, index) => ({
      id: id * 10 + index,
      business_id: `character-${id}-${index}`,
      story_id: id,
      importance: 1,
      virtual_ip_id,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    })),
  };
}

export function episode(id: number, storyId: number): Episode {
  return {
    id,
    business_id: `episode-${id}`,
    story_id: storyId,
    episode_number: 1,
    title: `剧集 ${id}`,
    status: "ready",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

export function environmentLink(
  ipId: number,
  environmentId: number,
  sortOrder = 0,
): VirtualIPEnvironmentLink {
  return {
    id: ipId * 100 + sortOrder,
    business_id: `link-${ipId}-${sortOrder}`,
    virtual_ip_id: ipId,
    environment_id: environmentId,
    usage_type: "scene",
    sort_order: sortOrder,
    is_default: false,
    environment: {
      id: environmentId,
      business_id: `environment-${environmentId}`,
      name: `环境 ${environmentId}`,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
    created_at: "2026-01-01T00:00:00Z",
  };
}

export function clip(clipId: string) {
  return {
    clip_id: clipId,
    track_type: "video",
    start_ms: 0,
    end_ms: 1000,
    text: clipId,
  };
}

export function timelineResponse(
  id: number,
  version: number,
  episodeId: number,
  clips: ReturnType<typeof clip>[],
  scriptId = 300,
): TimelineResponse {
  return {
    id,
    business_id: `timeline-${id}`,
    episode_id: episodeId,
    script_id: scriptId,
    title: "Timeline",
    status: "ready",
    version,
    spec: {
      spec_version: "1",
      episode_id: episodeId,
      script_id: scriptId,
      version,
      tracks: [{ track_type: "video", clips }],
    },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  };
}

export function scriptVersion(
  id: number,
  version: string,
  createdAt: string,
): Script {
  return {
    id,
    business_id: `script-${id}`,
    episode_id: 100,
    title: `Script ${id}`,
    format_type: "structured_json",
    language: "zh-CN",
    status: "completed",
    version,
    created_at: createdAt,
    updated_at: createdAt,
  };
}

export function assetLink(
  id: number,
  mediaAssetId: number,
  timelineVersion: number,
  clipId: string,
): TimelineClipAssetResponse {
  return {
    id,
    business_id: `asset-link-${id}`,
    timeline_id: 501,
    timeline_version: timelineVersion,
    clip_id: clipId,
    asset_role: "video_output",
    media_asset_id: mediaAssetId,
    source: "video_generation",
    created_at: "2026-01-01T00:00:00Z",
    media_asset: {
      id: mediaAssetId,
      business_id: `media-${mediaAssetId}`,
      asset_type: "video",
      origin: "generated",
      file_url: `https://cdn.test/${mediaAssetId}.mp4`,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  };
}

export function clipTask(clipId: string): TimelineClipTaskItem {
  return {
    task_id: 801,
    clip_id: clipId,
    status: "processing",
    task_type: "video_generation",
  };
}
