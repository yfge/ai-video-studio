const at = "2026-07-15T08:00:00Z";

export const virtualIPs = [
  {
    id: 1,
    business_id: "ip-mirror-city",
    name: "镜城主角",
    description: "层级画布测试 IP",
    tags: ["短剧"],
    is_active: true,
    is_public: false,
    created_at: at,
  },
  {
    id: 2,
    business_id: "ip-mirror-city-support",
    name: "镜城副角",
    tags: ["短剧"],
    is_active: true,
    is_public: false,
    created_at: at,
  },
];

export const environmentLinks = [
  {
    id: 81,
    business_id: "ip-environment-81",
    virtual_ip_id: 1,
    environment_id: 8,
    usage_type: "available",
    sort_order: 0,
    is_default: true,
    created_at: at,
    environment: {
      id: 8,
      business_id: "environment-rooftop",
      name: "雨夜天台",
      description: "IP 可复用环境",
      created_at: at,
      updated_at: at,
    },
  },
];

export const stories = [
  {
    id: 10,
    business_id: "story-mirror-city",
    title: "镜城来信",
    genre: "悬疑",
    premise: "一封来自未来的信",
    status: "draft",
    is_public: false,
    created_at: at,
    updated_at: at,
    story_characters: [{ virtual_ip_id: 1 }, { virtual_ip_id: 2 }],
  },
];

export const episodes = [
  {
    id: 100,
    business_id: "episode-100",
    story_id: 10,
    episode_number: 1,
    title: "天台重逢",
    status: "draft",
    created_at: at,
    updated_at: at,
  },
];

export const scripts = [
  {
    id: 299,
    business_id: "script-299",
    episode_id: 100,
    title: "天台重逢 v1",
    format_type: "structured_json",
    language: "zh-CN",
    status: "completed",
    version: "1",
    created_at: at,
    updated_at: at,
  },
  {
    id: 300,
    business_id: "script-300",
    episode_id: 100,
    title: "天台重逢 v2",
    format_type: "structured_json",
    language: "zh-CN",
    status: "completed",
    version: "2",
    created_at: at,
    updated_at: at,
  },
];

const clips = [
  { clip_id: "clip-ready", text: "雨幕中的信", start_ms: 0, end_ms: 2000 },
  {
    clip_id: "clip-generating",
    text: "追逐倒影",
    start_ms: 2000,
    end_ms: 5000,
  },
  { clip_id: "clip-missing", text: "门后真相", start_ms: 5000, end_ms: 8000 },
].map((clip) => ({ ...clip, track_type: "video" }));

const timeline = {
  id: 501,
  business_id: "timeline-501",
  episode_id: 100,
  script_id: 300,
  title: "天台重逢 Timeline",
  status: "draft",
  version: 7,
  created_at: at,
  updated_at: at,
  spec: {
    spec_version: "1",
    episode_id: 100,
    script_id: 300,
    version: 7,
    tracks: [{ track_type: "video", clips }],
  },
};

export const timelines = [
  {
    ...timeline,
    id: 499,
    business_id: "timeline-499",
    version: 6,
    spec: { ...timeline.spec, version: 6 },
  },
  timeline,
  {
    ...timeline,
    id: 599,
    business_id: "timeline-599",
    script_id: 299,
    version: 99,
    spec: { ...timeline.spec, script_id: 299, version: 99 },
  },
];

function videoAssetLink(
  id: number,
  mediaAssetId: number,
  timelineVersion: number,
) {
  return {
    id,
    business_id: `asset-link-${id}`,
    timeline_id: 501,
    timeline_version: timelineVersion,
    clip_id: "clip-ready",
    asset_role: "video_output",
    media_asset_id: mediaAssetId,
    source: "video_generation",
    created_at: at,
    media_asset: {
      id: mediaAssetId,
      business_id: `media-${mediaAssetId}`,
      asset_type: "video",
      origin: "generated",
      file_url: `https://cdn.test/${mediaAssetId}.mp4`,
      created_at: at,
      updated_at: at,
    },
  };
}

export const assetsByClip: Record<string, unknown[]> = {
  "clip-ready": [videoAssetLink(900, 700, 6), videoAssetLink(901, 701, 7)],
  "clip-generating": [],
  "clip-missing": [],
};

export const clipTasks = {
  items: [
    {
      task_id: 801,
      clip_id: "clip-generating",
      status: "processing",
      task_type: "video_generation",
      title: "追逐倒影视频生成",
    },
  ],
};
