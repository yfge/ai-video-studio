import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  buildTimelineClipVideoReworkTaskPayload,
  isTimelineVideoClip,
  timelineClipStoryboardPanelIndex,
  timelineClipStoryboardSheetUrl,
} from "../src/components/features/episode/TimelineClipProviderReworkModel";
import { TimelineClipProviderReworkControls } from "../src/components/features/episode/TimelineClipProviderReworkControls";
import { buildTimelineClipReworkPayload } from "../src/components/features/episode/TimelineClipReworkControls";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).HTMLInputElement = dom.window.HTMLInputElement;
(globalThis as any).HTMLSelectElement = dom.window.HTMLSelectElement;
(globalThis as any).HTMLTextAreaElement = dom.window.HTMLTextAreaElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;

describe("timeline clip rework controls", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    localStorage.clear();
  });

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

  it("builds provider video rework payloads with clip storyboard references", () => {
    assert.deepEqual(
      buildTimelineClipVideoReworkTaskPayload({
        expectedVersion: 5,
        action: "re_cut",
        model: "volcengine:doubao-seedance-2-0-260128",
        resolution: "720p",
        useClipStoryboard: true,
      }),
      {
        expected_version: 5,
        action: "re_cut",
        model: "volcengine:doubao-seedance-2-0-260128",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: false,
        return_last_frame: true,
        reference_mode: "clip_storyboard_panel",
        use_clip_storyboard: true,
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

  it("reads clip storyboard panel indexes from selected timeline clips", () => {
    const item = {
      id: "video-1",
      startMs: 0,
      endMs: 1000,
      label: "clip",
      type: "video" as const,
      color: "#0f766e",
      meta: {
        track_type: "video",
        source_refs: {
          clip_storyboard: {
            panel_index: 4,
          },
        },
        clip_storyboard_sheet_asset_ref: {
          file_url: "https://cdn.example/clip-storyboard.png",
        },
      },
    };
    assert.equal(timelineClipStoryboardPanelIndex(item), 4);
    assert.equal(
      timelineClipStoryboardSheetUrl(item),
      "https://cdn.example/clip-storyboard.png",
    );
  });

  it("renders storyboard reference and clip video as two separate cards", () => {
    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithStoryboardPanel(),
      }),
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("故事板参考"));
    assert.ok(utils.getByText("片段视频"));
    assert.ok(utils.getByRole("button", { name: "生成故事板参考图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    assert.ok(utils.getByLabelText("视频参考来源"));
    assert.ok(utils.getByRole("option", { name: "故事板 Panel 4" }));
    assert.ok(utils.getByLabelText("附加参考图 URL"));
  });

  it("keeps storyboard and video submit paths clip-scoped from the two-step controls", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 88, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithStoryboardPanel(),
      }),
      { container: dom.window.document.body },
    );

    fireEvent.input(utils.getByLabelText("附加参考图 URL"), {
      target: { value: "https://manual.example/ref.png" },
    });
    fireEvent.click(utils.getByRole("button", { name: "生成故事板参考图" }));
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].url,
      "/api/v1/timelines/8/clips/video_scene_1_beat_1_001/storyboard/generate",
    );
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        panel_count: 4,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        reference_images: ["https://manual.example/ref.png"],
      }),
    );

    fireEvent.change(utils.getByLabelText("视频参考来源"), {
      target: { value: "clip_storyboard_panel" },
    });
    fireEvent.click(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    await waitFor(() => assert.equal(calls.length, 2));
    assert.equal(
      calls[1].url,
      "/api/v1/timelines/8/clips/video_scene_1_beat_1_001/rework/video",
    );
    assert.equal(
      calls[1].init?.body,
      JSON.stringify({
        expected_version: 3,
        action: "re_cut",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: false,
        return_last_frame: true,
        reference_mode: "clip_storyboard_panel",
        use_clip_storyboard: true,
        reference_images: ["https://manual.example/ref.png"],
      }),
    );
  });

  it("submits manual reference images as an explicit generation choice", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 89, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithStoryboardPanel(),
      }),
      { container: dom.window.document.body },
    );

    fireEvent.change(utils.getByLabelText("视频参考来源"), {
      target: { value: "manual_refs" },
    });
    fireEvent.input(utils.getByLabelText("附加参考图 URL"), {
      target: {
        value: "https://manual.example/a.png\nhttps://manual.example/b.png",
      },
    });
    fireEvent.click(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        action: "re_cut",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: false,
        return_last_frame: true,
        reference_mode: "start_end",
        reference_images: [
          "https://manual.example/a.png",
          "https://manual.example/b.png",
        ],
      }),
    );
  });
});

function videoClipWithStoryboardPanel() {
  return {
    id: "video-1",
    startMs: 0,
    endMs: 1000,
    label: "clip",
    type: "video" as const,
    color: "#0f766e",
    meta: {
      track_type: "video",
      source_refs: {
        clip_storyboard: {
          panel_index: 4,
        },
      },
      clip_storyboard_sheet_asset_ref: {
        file_url: "https://cdn.example/clip-storyboard.png",
      },
    },
  };
}
