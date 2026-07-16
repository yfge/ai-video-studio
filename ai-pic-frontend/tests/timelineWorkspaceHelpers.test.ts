import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  firstTimelineItemId,
  resolveTimelineSelection,
} from "../src/components/features/Timeline/timelineViewModel";
import { timelineLayoutForMeasuredWidth } from "../src/components/features/Timeline/timelineLayout";
import {
  buildEpisodeTimelineTracks,
  sceneForTimelineMeta,
} from "../src/components/features/episode/EpisodeTimelineWorkspaceModel";
import {
  preferredTimelineItemId,
  preferredVideoTimelineItemId,
  timelineItemIdForClipId,
} from "../src/components/features/episode/EpisodeTimelineSelectionModel";
import {
  buildTimelineRenderReadinessFromResolvedVideos,
  buildTimelineRenderReadiness,
  timelineClipVideoStatus,
} from "../src/components/features/episode/EpisodeTimelineRenderModel";
import { timelineClipProductionReadiness } from "../src/components/features/episode/TimelineClipProductionReadiness";
import {
  buildStoryboardGridSupport,
  buildStoryboardSupportFrames,
  buildStoryboardSupportSummary,
} from "../src/components/features/episode/WorkspaceStoryboardSupportModel";
import { buildStoryboardTimelineOverview } from "../src/components/features/episode/WorkspaceStoryboardTimelineOverviewModel";
import { buildShotPlanPromptLayerPatch } from "../src/components/features/episode/WorkspaceStoryboardPromptLayers";
import { hasTimeline } from "../src/components/features/stories/StoryProductionModel";
import type { TimelineTrack } from "../src/components/features/Timeline/Timeline";
import type { TimelineResponse } from "../src/utils/api/types";
import { episodeWorkspaceHref } from "../src/utils/routes";

const tracks: TimelineTrack[] = [
  {
    id: "dialogue",
    label: "对白",
    items: [
      {
        id: "beat-1",
        startMs: 0,
        endMs: 1200,
        label: "开场对白",
      },
    ],
  },
  {
    id: "storyboard",
    label: "分镜",
    items: [
      {
        id: "frame-1",
        startMs: 0,
        endMs: 1200,
        label: "主角推门",
      },
    ],
  },
];

describe("timeline workspace helpers", () => {
  it("uses a compact Timeline layout on narrow workspaces", () => {
    assert.deepEqual(timelineLayoutForMeasuredWidth(390), {
      compact: true,
      secondaryTrackHeight: 16,
      tickLaneHeight: 44,
      trackGap: 1,
      trackHeight: 104,
      trackLabelWidth: 88,
      trackRightPadding: 8,
    });
    assert.deepEqual(timelineLayoutForMeasuredWidth(600), {
      compact: false,
      secondaryTrackHeight: 18,
      tickLaneHeight: 44,
      trackGap: 2,
      trackHeight: 116,
      trackLabelWidth: 112,
      trackRightPadding: 8,
    });
  });

  it("defaults episode workspace links to the timeline tab", () => {
    assert.equal(
      episodeWorkspaceHref("episode_123"),
      "/episodes/episode_123/workspace?tab=timeline",
    );
  });

  it("resolves the selected timeline item and first fallback item", () => {
    const selection = resolveTimelineSelection(tracks, "frame-1");

    assert.equal(firstTimelineItemId(tracks), "beat-1");
    assert.equal(selection.item?.label, "主角推门");
    assert.equal(selection.track?.id, "storyboard");
    assert.deepEqual(resolveTimelineSelection(tracks, "missing"), {
      item: null,
      track: null,
    });
  });

  it("prefers the video track even when items use legacy clip types", () => {
    const legacyVideoTracks = [
      tracks[0],
      {
        id: "video",
        label: "视频",
        items: [
          {
            id: "legacy-video-item",
            startMs: 0,
            endMs: 1200,
            label: "视频片段",
            type: "clip",
          },
        ],
      },
    ];

    assert.equal(
      preferredVideoTimelineItemId(legacyVideoTracks),
      "legacy-video-item",
    );
    assert.equal(
      preferredTimelineItemId(legacyVideoTracks),
      "legacy-video-item",
    );
  });

  it("does not resolve URL clip ids to storyboard support items", () => {
    assert.equal(
      timelineItemIdForClipId(
        [
          {
            id: "storyboard",
            label: "分镜",
            items: [
              {
                id: "storyboard-video_scene_1_beat_1_001",
                startMs: 0,
                endMs: 1200,
                label: "support",
                type: "storyboard",
                meta: { timeline_clip_id: "video_scene_1_beat_1_001" },
              },
            ],
          },
        ],
        "video_scene_1_beat_1_001",
      ),
      null,
    );
  });

  it("maps a selected timeline item to the normalized scene environment", () => {
    const scene = sceneForTimelineMeta(
      [
        {
          id: 7,
          scene_number: "2",
          slug_line: "INT. 公寓 - 夜",
          status: "draft",
          environment_id: 11,
        },
      ],
      { scene_number: "2" },
      { 7: 12 },
    );

    assert.equal(scene?.id, 7);
    assert.equal(scene?.environment_id, 12);
  });

  it("builds workspace tracks from native Timeline Spec before legacy beats", () => {
    const timeline = {
      id: 3,
      business_id: "timeline_3",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "draft",
      version: 1,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 1,
        tracks: [
          {
            track_type: "dialogue",
            clips: [
              {
                clip_id: "dialogue_scene_1_beat_1_001",
                track_type: "dialogue",
                start_ms: 0,
                end_ms: 1200,
                text: "native dialogue",
              },
            ],
          },
        ],
      },
    } satisfies TimelineResponse;

    const result = buildEpisodeTimelineTracks(
      timeline,
      {
        beats: [
          {
            start_ms: 0,
            end_ms: 1200,
            text: "legacy dialogue",
          },
        ],
      },
      null,
    );

    assert.equal(result[0].id, "dialogue");
    assert.equal(result[0].items[0].label, "native dialogue");
  });

  it("enriches native video clips from matching audio beats", () => {
    const timeline = {
      id: 3,
      business_id: "timeline_3",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "draft",
      version: 1,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 1,
        tracks: [
          {
            track_type: "video",
            clips: [
              {
                clip_id: "video_scene_1_beat_1_001",
                beat_id: 3991,
                track_type: "video",
                start_ms: 0,
                end_ms: 1200,
                text: "native video",
              },
            ],
          },
        ],
      },
    } satisfies TimelineResponse;

    const result = buildEpisodeTimelineTracks(
      timeline,
      {
        beats: [
          {
            beat_id: 3991,
            speaker_name: "老拐",
            characters_involved: ["老拐", "阿盖儿"],
            dialogue_action: "打开手机",
            dialogue_emotion: "confident",
          },
        ],
      },
      null,
    );

    const videoItem = result[0].items[0];
    assert.equal(videoItem.type, "video");
    assert.equal(videoItem.meta?.speaker_name, "老拐");
    assert.deepEqual(videoItem.meta?.characters_involved, ["老拐", "阿盖儿"]);
    assert.equal(videoItem.meta?.dialogue_action, "打开手机");
    assert.equal(videoItem.meta?.dialogue_emotion, "confident");
  });

  it("uses the matching storyboard frame image for a timeline video clip", () => {
    const timeline = {
      id: 3,
      business_id: "timeline_3",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "draft",
      version: 39,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 39,
        tracks: [
          {
            track_type: "video",
            clips: [
              {
                clip_id: "video_scene_1_beat_1_001",
                track_type: "video",
                start_ms: 0,
                end_ms: 1200,
                text: "native video",
              },
            ],
          },
        ],
      },
    } satisfies TimelineResponse;
    const imageUrl = "https://example.com/storyboard.png";

    const result = buildEpisodeTimelineTracks(timeline, null, {
      frames: [
        {
          timeline_clip_id: "video_scene_1_beat_1_001",
          image_url: imageUrl,
        },
      ],
    });
    const readiness = timelineClipProductionReadiness(result[0].items[0]);

    assert.equal(result[0].items[0].meta?.image_url, imageUrl);
    assert.equal(readiness.storyboardReady, true);
    assert.equal(readiness.storyboardSheetUrl, imageUrl);
  });

  it("falls back to legacy audio timeline tracks when Timeline Spec is absent", () => {
    const result = buildEpisodeTimelineTracks(
      null,
      {
        beats: [
          {
            start_ms: 0,
            end_ms: 1200,
            text: "legacy dialogue",
          },
        ],
      },
      null,
    );

    assert.equal(result[0].id, "dialogue");
    assert.equal(result[0].items[0].label, "legacy dialogue");
  });

  it("uses Timeline rows for story production readiness", () => {
    assert.equal(
      hasTimeline(
        { id: 1, extra_metadata: {} } as Parameters<typeof hasTimeline>[0],
        { id: 2 } as Parameters<typeof hasTimeline>[1],
        [{ script_id: 2 } as TimelineResponse],
      ),
      true,
    );
    assert.equal(
      hasTimeline(
        { id: 1, extra_metadata: {} } as Parameters<typeof hasTimeline>[0],
        { id: 2 } as Parameters<typeof hasTimeline>[1],
        [{ script_id: 3 } as TimelineResponse],
      ),
      false,
    );
  });

  it("preflights timeline render videos from direct clip assets", () => {
    const timeline = {
      id: 4,
      business_id: "timeline_4",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "ready",
      version: 1,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 1,
        tracks: [
          {
            track_type: "video",
            clips: [
              {
                clip_id: "video_scene_1_beat_1_001",
                track_type: "video",
                start_ms: 0,
                end_ms: 1200,
                asset_ref: { file_url: "https://example.com/clip.mp4" },
              },
            ],
          },
        ],
      },
    } satisfies TimelineResponse;

    const readiness = buildTimelineRenderReadiness(timeline, null);

    assert.equal(readiness.ready, true);
    assert.equal(readiness.videoClipCount, 1);
    assert.equal(readiness.missingClips.length, 0);
  });

  it("preflights missing timeline render videos", () => {
    const readiness = buildTimelineRenderReadiness(
      {
        id: 5,
        business_id: "timeline_5",
        episode_id: 1,
        script_id: 2,
        title: "Timeline",
        status: "ready",
        version: 1,
        created_at: "2026-05-12T00:00:00Z",
        updated_at: "2026-05-12T00:00:00Z",
        spec: {
          spec_version: "timeline.v1",
          episode_id: 1,
          script_id: 2,
          version: 1,
          tracks: [
            {
              track_type: "video",
              clips: [
                {
                  clip_id: "video_scene_2_beat_3_001",
                  track_type: "video",
                  scene_number: 2,
                  start_ms: 0,
                  end_ms: 1000,
                },
              ],
            },
          ],
        },
      } satisfies TimelineResponse,
      null,
    );

    assert.equal(readiness.ready, false);
    assert.equal(readiness.missingClips[0].clipId, "video_scene_2_beat_3_001");
    assert.equal(readiness.missingClips[0].reason, "missing_video_url");
  });

  it("marks missing clips with in-flight tasks as generating", () => {
    const readiness = buildTimelineRenderReadiness(
      {
        id: 6,
        business_id: "timeline_6",
        episode_id: 1,
        script_id: 2,
        title: "Timeline",
        status: "ready",
        version: 1,
        created_at: "2026-05-12T00:00:00Z",
        updated_at: "2026-05-12T00:00:00Z",
        spec: {
          spec_version: "timeline.v1",
          episode_id: 1,
          script_id: 2,
          version: 1,
          tracks: [
            {
              track_type: "video",
              clips: [
                {
                  clip_id: "video_a",
                  track_type: "video",
                  start_ms: 0,
                  end_ms: 1000,
                },
                {
                  clip_id: "video_b",
                  track_type: "video",
                  start_ms: 1000,
                  end_ms: 2000,
                },
              ],
            },
          ],
        },
      } satisfies TimelineResponse,
      null,
      new Set(["video_a"]),
    );

    assert.equal(readiness.ready, false);
    const reasons = Object.fromEntries(
      readiness.missingClips.map((clip) => [clip.clipId, clip.reason]),
    );
    assert.equal(reasons.video_a, "generating");
    assert.equal(reasons.video_b, "missing_video_url");
  });

  it("preflights timeline render videos from resolved clip videos", () => {
    const readiness = buildTimelineRenderReadinessFromResolvedVideos({
      timeline_id: 8,
      timeline_version: 3,
      ready: false,
      video_clip_count: 3,
      missing_clip_count: 1,
      generating_clip_count: 1,
      items: [
        {
          clip_id: "video_ready",
          status: "ready",
          url: "https://example.com/ready.mp4",
          source: "timeline_clip_asset:provider_rework",
          start_ms: 0,
          end_ms: 1000,
          duration_seconds: 1,
        },
        {
          clip_id: "video_generating",
          status: "generating",
          reason: "generating",
          start_ms: 1000,
          end_ms: 2000,
          duration_seconds: 1,
          task_id: 12,
          task_type: "video_generation",
        },
        {
          clip_id: "video_missing",
          status: "missing",
          reason: "missing_video_url",
          start_ms: 2000,
          end_ms: 3000,
          duration_seconds: 1,
        },
      ],
    });

    assert.equal(readiness.ready, false);
    assert.equal(readiness.videoClipCount, 3);
    assert.deepEqual(
      readiness.missingClips.map((clip) => [clip.clipId, clip.reason]),
      [
        ["video_generating", "generating"],
        ["video_missing", "missing_video_url"],
      ],
    );
  });

  it("resolves selected clip video status from storyboard support frames", () => {
    const status = timelineClipVideoStatus(
      { clip_id: "video_scene_1_beat_1_001" },
      {
        frames: [
          {
            timeline_clip_id: "video_scene_1_beat_1_001",
            video_url: "https://example.com/storyboard.mp4",
          },
        ],
      },
    );

    assert.equal(status.ready, true);
    assert.equal(status.source, "storyboard_frame");
    assert.equal(status.url, "https://example.com/storyboard.mp4");
  });

  it("builds storyboard support frames as a read-only timeline view", () => {
    const storyboard = {
      meta: {
        generation_source: "timeline_spec",
        timeline_id: 7,
        timeline_version: 3,
      },
      frames: [
        {
          frame_id: "frame-1",
          frame_number: 1,
          timeline_clip_id: "dialogue_scene_1_beat_1_001",
          scene_number: "1",
          start_ms: 0,
          end_ms: 1800,
          description: "主角推门进入实验室",
          prompt_description: "2D cartoon, vertical short drama shot",
          shot_plan_prompt_layers: {
            direction_anchor: "朝向实验室门口的悬疑进入",
            aesthetic_reference: "IMAX film, Panavision C lens",
            composition_geometry: "门在中心线，主角位于左三分线",
            motion_timeline: [
              { at_ms: 0, action: "主角伸手推门" },
              { at_ms: 1800, action: "门缝透出冷光" },
            ],
            emotional_landing: "冷光里的紧张停顿",
          },
          image_url: "https://example.com/frame.png",
          video_url: "https://example.com/clip.mp4",
          source: { kind: "timeline_clip" },
        },
      ],
    };

    const summary = buildStoryboardSupportSummary(storyboard);
    const frames = buildStoryboardSupportFrames(storyboard, [
      {
        id: 1,
        scene_number: "1",
        slug_line: "INT. 实验室 - 夜",
        status: "draft",
      },
    ]);

    assert.deepEqual(summary, {
      frameCount: 1,
      imageCount: 1,
      videoCount: 1,
      generationSource: "timeline_spec",
      timelineId: "7",
      timelineVersion: "3",
      gridSheetUrl: null,
      gridPanelCount: 0,
      gridGeneratedAt: null,
    });
    assert.equal(frames[0].clipId, "dialogue_scene_1_beat_1_001");
    assert.equal(frames[0].sceneLabel, "1 · INT. 实验室 - 夜");
    assert.equal(frames[0].imageUrl, "https://example.com/frame.png");
    assert.equal(frames[0].videoUrl, "https://example.com/clip.mp4");
    assert.equal(frames[0].sourceKind, "timeline_clip");
    assert.equal(
      frames[0].promptLayers?.compositionGeometry,
      "门在中心线，主角位于左三分线",
    );
    assert.equal(frames[0].promptLayers?.motionTimeline[1].atMs, 1800);
  });

  it("builds storyboard grid support metadata from Timeline support views", () => {
    const timeline = {
      id: 8,
      business_id: "timeline_8",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "draft",
      version: 3,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 3,
        tracks: [],
        support_views: {
          storyboard_grid: {
            generated_at: "2026-06-01T00:00:00Z",
            sheet: {
              file_url: "https://example.com/grid.png",
              panel_count: 9,
              columns: 3,
              rows: 3,
            },
            panels: [
              {
                panel_id: "grid_panel_001",
                panel_index: 1,
                clip_id: "video_scene_1_beat_1_001",
                start_ms: 0,
                end_ms: 1200,
                visual_prompt: "主角推门",
                video_prompt: "镜头推近",
                direction_anchor: "朝向门口的动作起势",
                aesthetic_reference: "analog film still",
                composition_geometry: "门框居中，主角从右侧入画",
                motion_timeline: [
                  { at_ms: 0, action: "主角推门" },
                  { at_ms: 1200, action: "众人回头" },
                ],
                emotional_landing: "突然被注视的压迫感",
              },
            ],
          },
        },
      },
    } satisfies TimelineResponse;

    const summary = buildStoryboardSupportSummary(null, timeline);
    const grid = buildStoryboardGridSupport(timeline);

    assert.equal(summary.gridSheetUrl, "https://example.com/grid.png");
    assert.equal(summary.gridPanelCount, 9);
    assert.equal(summary.gridGeneratedAt, "2026-06-01T00:00:00Z");
    assert.equal(grid.panels[0].panelIndex, 1);
    assert.equal(grid.panels[0].clipId, "video_scene_1_beat_1_001");
    assert.equal(grid.panels[0].timeLabel, "0:00.000 - 0:01.200");
    assert.equal(
      grid.panels[0].promptLayers?.directionAnchor,
      "朝向门口的动作起势",
    );
    assert.equal(grid.panels[0].promptLayers?.motionTimeline[1].atMs, 1200);
  });

  it("builds storyboard Timeline overview from native Timeline Spec", () => {
    const timeline = {
      id: 10,
      business_id: "timeline_10",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "draft",
      version: 5,
      source_audio_timeline_version: 3,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 5,
        duration_ms: 4600,
        source: {
          episode_audio: {
            oss_url: "https://example.com/episode.mp3",
            duration_seconds: 4.6,
          },
        },
        tracks: [
          {
            track_type: "dialogue",
            clips: [
              {
                clip_id: "dialogue_scene_1_beat_1_001",
                track_type: "dialogue",
                start_ms: 0,
                end_ms: 1800,
              },
            ],
          },
          {
            track_type: "video",
            clips: [
              {
                clip_id: "video_scene_1_beat_1_001",
                track_type: "video",
                start_ms: 0,
                end_ms: 1800,
              },
              {
                clip_id: "video_scene_1_beat_2_002",
                track_type: "video",
                start_ms: 2800,
                end_ms: 4600,
              },
            ],
          },
        ],
      },
    } satisfies TimelineResponse;

    const overview = buildStoryboardTimelineOverview(timeline, null);

    assert.equal(overview?.timelineLabel, "Timeline 10 · v5");
    assert.equal(overview?.durationLabel, "4.6s");
    assert.equal(overview?.trackSummary, "2 轨 · 3 clips");
    assert.equal(overview?.dialogueClipCount, 1);
    assert.equal(overview?.videoClipCount, 2);
    assert.equal(overview?.audioUrl, "https://example.com/episode.mp3");
  });

  it("patches shot plan prompt layers without changing clip identity or timing", () => {
    const timeline = {
      id: 9,
      business_id: "timeline_9",
      episode_id: 1,
      script_id: 2,
      title: "Timeline",
      status: "draft",
      version: 4,
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      spec: {
        spec_version: "timeline.v1",
        episode_id: 1,
        script_id: 2,
        version: 4,
        support_views: {
          storyboard_grid: {
            sheet: { file_url: "https://example.com/grid.png" },
            panels: [],
          },
        },
        tracks: [
          {
            track_type: "video",
            clips: [
              {
                clip_id: "video_scene_1_beat_1_001",
                track_type: "video",
                start_ms: 0,
                end_ms: 1200,
                duration_ms: 1200,
                source_refs: {
                  grid_storyboard_panel: { panel_index: 1 },
                  timeline_shot_plan: {
                    clip_id: "video_scene_1_beat_1_001",
                    duration_ms: 1200,
                    visual_prompt: "old visual",
                    video_prompt: "old video",
                  },
                },
              },
            ],
          },
        ],
      },
    } satisfies TimelineResponse;

    const patched = buildShotPlanPromptLayerPatch(
      timeline,
      "video_scene_1_beat_1_001",
      {
        directionAnchor: "朝向门口的动作起势",
        aestheticReference: "analog film still",
        shotType: "low angle medium shot",
        cameraMovement: "slow push-in",
        compositionGeometry: "门框居中，主角从右侧入画",
        motionTimeline: [
          { atMs: 0, action: "主角推门" },
          { atMs: 1200, action: "众人回头" },
        ],
        emotionalLanding: "突然被注视的压迫感",
        promptMethod: "direction_reference_geometry_timeline_emotion_v1",
      },
    );

    assert.ok(patched);
    const clip = patched.tracks[0].clips[0];
    assert.equal(clip.clip_id, "video_scene_1_beat_1_001");
    assert.equal(clip.start_ms, 0);
    assert.equal(clip.end_ms, 1200);
    const refs = clip.source_refs as Record<string, unknown>;
    assert.equal(refs.grid_storyboard_panel, undefined);
    const shotPlan = refs.timeline_shot_plan as Record<string, unknown>;
    assert.equal(shotPlan.direction_anchor, "朝向门口的动作起势");
    assert.deepEqual(shotPlan.motion_timeline, [
      { at_ms: 0, action: "主角推门" },
      { at_ms: 1200, action: "众人回头" },
    ]);
    assert.equal(patched.support_views?.storyboard_grid, undefined);
  });
});
