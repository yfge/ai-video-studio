import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
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

describe("WorkspaceStoryboardTabContent", () => {
  afterEach(() => cleanup());

  it("shows the storyboard generation entry on the default storyboard tab", () => {
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

    assert.ok(utils.getByRole("button", { name: "生成宫格分镜" }));
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
