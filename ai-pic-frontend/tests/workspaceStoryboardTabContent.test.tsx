import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { WorkspaceStoryboardTabContent } from "../src/components/features/episode/WorkspaceStoryboardTabContent";
import type { TimelineResponse } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>");
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

const timelineWithVideo = {
  id: 8,
  business_id: "timeline_8",
  episode_id: 1,
  script_id: 131,
  title: "Timeline",
  status: "draft",
  version: 3,
  created_at: "2026-06-03T00:00:00Z",
  updated_at: "2026-06-03T00:00:00Z",
  spec: {
    spec_version: "timeline.v1",
    episode_id: 1,
    script_id: 131,
    version: 3,
    tracks: [
      {
        track_type: "video",
        clips: [
          {
            clip_id: "video_scene_1_beat_1_001",
            track_type: "video",
            start_ms: 0,
            end_ms: 1200,
          },
        ],
      },
    ],
  },
} satisfies TimelineResponse;

const timelineWithAudio = {
  ...timelineWithVideo,
  spec: {
    ...timelineWithVideo.spec,
    duration_ms: 1200,
    source: {
      episode_audio: {
        oss_url: "https://example.com/episode-audio.mp3",
        duration_seconds: 1.2,
        generated_at: "2026-06-04T08:00:00Z",
        version: 2,
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
            end_ms: 1200,
            duration_ms: 1200,
            text: "native dialogue",
          },
        ],
      },
      ...timelineWithVideo.spec.tracks,
    ],
  },
} satisfies TimelineResponse;

describe("WorkspaceStoryboardTabContent", () => {
  afterEach(() => cleanup());

  it("surfaces clip-scoped storyboard management without whole-Timeline generation", () => {
    const utils = render(
      <WorkspaceStoryboardTabContent
        episodeKey="episode_7"
        selectedScriptId={131}
        hasStoryboard={false}
        selectedTimelineSpec={timelineWithVideo}
        selectedStoryboard={null}
        normalizedScenes={[]}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.queryByRole("button", { name: "生成宫格分镜" }), null);
    assert.equal(utils.queryByRole("button", { name: "生成故事板" }), null);
    assert.equal(utils.queryByRole("button", { name: "生成整集故事板" }), null);
    assert.equal(utils.queryByText("宫格故事板"), null);
    assert.equal(utils.queryByRole("button", { name: "同步分镜占位" }), null);
    assert.ok(utils.getByText("片段分镜管理"));
    assert.ok(utils.getAllByText("视频 1").length >= 1);
    assert.ok(utils.getByText("环境/IP 待绑定"));
    assert.ok(utils.getByText("分镜待生成"));
    assert.equal(
      utils
        .getByRole("link", { name: "进入第一个片段分镜" })
        .getAttribute("href"),
      "/episodes/episode_7/workspace?tab=timeline&scriptId=131&clipId=video_scene_1_beat_1_001",
    );
    const link = utils.getByRole("link", { name: "进入片段分镜" });
    assert.equal(
      link.getAttribute("href"),
      "/episodes/episode_7/workspace?tab=timeline&scriptId=131&clipId=video_scene_1_beat_1_001",
    );
  });

  it("surfaces native Timeline context and audio playback on the storyboard tab", () => {
    const utils = render(
      <WorkspaceStoryboardTabContent
        episodeKey="episode_7"
        selectedScriptId={131}
        hasStoryboard={false}
        selectedTimelineSpec={timelineWithAudio}
        selectedStoryboard={null}
        normalizedScenes={[]}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getAllByText("Timeline 8 · v3").length, 2);
    assert.ok(utils.getByText("2 轨 · 2 clips"));
    assert.ok(utils.getByText("时长 1.2s"));
    const audio = utils.container.querySelector("audio");
    assert.equal(
      audio?.getAttribute("src"),
      "https://example.com/episode-audio.mp3",
    );
  });

  it("renders editable prompt-layer context for storyboard frames", () => {
    const utils = render(
      <WorkspaceStoryboardTabContent
        episodeKey="episode_7"
        selectedScriptId={131}
        hasStoryboard
        selectedTimelineSpec={timelineWithVideo}
        selectedStoryboard={{
          frames: [
            {
              frame_id: "frame-1",
              frame_number: 1,
              timeline_clip_id: "video_scene_1_beat_1_001",
              start_ms: 0,
              end_ms: 1200,
              description: "主角推开实验室门",
              shot_plan_prompt_layers: {
                direction_anchor: "朝向实验室门口的悬疑进入",
                aesthetic_reference: "IMAX film, Panavision C lens",
                composition_geometry: "门在中心线，主角位于左三分线",
                motion_timeline: [
                  { at_ms: 0, action: "主角伸手推门" },
                  { at_ms: 1200, action: "门缝透出冷光" },
                ],
                emotional_landing: "冷光里的紧张停顿",
              },
            },
          ],
        }}
        normalizedScenes={[]}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("五层提示词"));
    assert.ok(utils.getByText("朝向实验室门口的悬疑进入"));
    assert.ok(utils.getByText("0ms 主角伸手推门 / 1200ms 门缝透出冷光"));
  });

  it("falls back to audio timeline storyboard sync when native Timeline is absent", () => {
    const utils = render(
      <WorkspaceStoryboardTabContent
        episodeKey="episode_7"
        selectedScriptId={131}
        hasStoryboard={false}
        selectedAudioTimeline={{ version: 1, beats: [{ start_ms: 0 }] }}
        selectedTimelineSpec={null}
        selectedStoryboard={null}
        normalizedScenes={[]}
      />,
      { container: dom.window.document.body },
    );

    const button = utils.getByRole("button", { name: "同步分镜占位" });
    assert.equal(button.hasAttribute("disabled"), false);
  });
});
