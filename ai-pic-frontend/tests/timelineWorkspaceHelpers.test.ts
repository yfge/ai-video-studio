import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  firstTimelineItemId,
  resolveTimelineSelection,
} from "../src/components/features/Timeline/timelineViewModel";
import {
  buildEpisodeTimelineTracks,
  sceneForTimelineMeta,
} from "../src/components/features/episode/EpisodeTimelineWorkspaceModel";
import {
  buildTimelineRenderReadiness,
  timelineClipVideoStatus,
} from "../src/components/features/episode/EpisodeTimelineRenderModel";
import {
  buildStoryboardSupportFrames,
  buildStoryboardSupportSummary,
} from "../src/components/features/episode/WorkspaceStoryboardSupportModel";
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
    });
    assert.equal(frames[0].clipId, "dialogue_scene_1_beat_1_001");
    assert.equal(frames[0].sceneLabel, "1 · INT. 实验室 - 夜");
    assert.equal(frames[0].imageUrl, "https://example.com/frame.png");
    assert.equal(frames[0].videoUrl, "https://example.com/clip.mp4");
    assert.equal(frames[0].sourceKind, "timeline_clip");
  });
});
