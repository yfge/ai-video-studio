import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildTimelineClipVideoReworkTaskPayload,
  isTimelineVideoClip,
  timelineClipGridPanelIndex,
} from "../src/components/features/episode/TimelineClipProviderReworkModel";
import { buildTimelineClipReworkPayload } from "../src/components/features/episode/TimelineClipReworkControls";

describe("timeline clip rework controls", () => {
  it("builds compact timeline clip rework payloads", () => {
    assert.deepEqual(
      buildTimelineClipReworkPayload({
        expectedVersion: 3,
        action: "re_render",
        mediaAssetId: 42,
        assetRole: " render_output ",
        reason: " cleaner export ",
      }),
      {
        expected_version: 3,
        action: "re_render",
        media_asset_id: 42,
        asset_role: "render_output",
        reason: "cleaner export",
      },
    );
  });

  it("builds provider video rework task payloads", () => {
    assert.deepEqual(
      buildTimelineClipVideoReworkTaskPayload({
        expectedVersion: 4,
        action: "re_cut",
        prompt: " steadier motion ",
        model: " keling:kling-v2 ",
        duration: 1.2,
        resolution: "1080p",
        ratio: "9:16",
        reason: " motion fix ",
      }),
      {
        expected_version: 4,
        action: "re_cut",
        prompt: "steadier motion",
        model: "keling:kling-v2",
        duration: 1.2,
        resolution: "1080p",
        ratio: "9:16",
        asset_role: "generated_video",
        reason: "motion fix",
        use_end_frame: true,
        return_last_frame: true,
      },
    );
  });

  it("builds provider video rework payloads with grid storyboard references", () => {
    assert.deepEqual(
      buildTimelineClipVideoReworkTaskPayload({
        expectedVersion: 5,
        action: "re_cut",
        model: "volcengine:doubao-seedance-2-0-260128",
        resolution: "720p",
        useStoryboardGrid: true,
      }),
      {
        expected_version: 5,
        action: "re_cut",
        model: "volcengine:doubao-seedance-2-0-260128",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: false,
        return_last_frame: true,
        reference_mode: "storyboard_grid_panel",
        use_storyboard_grid: true,
      },
    );
  });

  it("recognizes native Timeline video clips only", () => {
    assert.equal(
      isTimelineVideoClip({
        id: "video-1",
        startMs: 0,
        endMs: 1000,
        label: "clip",
        type: "video",
        color: "#0f766e",
        meta: { track_type: "video" },
      }),
      true,
    );
    assert.equal(
      isTimelineVideoClip({
        id: "dialogue-1",
        startMs: 0,
        endMs: 1000,
        label: "line",
        type: "dialogue",
        color: "#2563eb",
        meta: { track_type: "dialogue" },
      }),
      false,
    );
  });

  it("reads grid storyboard panel indexes from selected timeline clips", () => {
    assert.equal(
      timelineClipGridPanelIndex({
        id: "video-1",
        startMs: 0,
        endMs: 1000,
        label: "clip",
        type: "video",
        color: "#0f766e",
        meta: {
          track_type: "video",
          source_refs: {
            grid_storyboard_panel: {
              panel_index: 4,
            },
          },
        },
      }),
      4,
    );
  });
});
