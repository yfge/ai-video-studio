import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import {
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  buildTimelineClipVideoReworkTaskPayload,
  isTimelineVideoClip,
  timelineClipStartEndFrameStatus,
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
        resolution: "1080p",
        ratio: "9:16",
        reason: " motion fix ",
      }),
      {
        expected_version: 4,
        action: "re_cut",
        prompt: "steadier motion",
        model: "keling:kling-v2",
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
        reference_mode: "clip_storyboard_sheet",
        use_clip_storyboard: true,
      },
    );
  });

  it("adds operator review confirmation to provider video payloads", () => {
    assert.deepEqual(
      buildTimelineClipVideoReworkTaskPayload({
        expectedVersion: 5,
        action: "re_cut",
        resolution: "720p",
        operatorReviewed: true,
      }),
      {
        expected_version: 5,
        action: "re_cut",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: true,
        return_last_frame: true,
        operator_reviewed: true,
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

  it("reports selected clip start and end keyframe readiness", () => {
    assert.deepEqual(timelineClipStartEndFrameStatus(null), {
      startReady: false,
      endReady: false,
      label: "首尾帧待生成",
    });
    assert.deepEqual(
      timelineClipStartEndFrameStatus(videoClipWithStoryboardPanel()),
      {
        startReady: true,
        endReady: true,
        label: "首尾帧已生成",
      },
    );
    assert.deepEqual(
      timelineClipStartEndFrameStatus(videoClipWithoutStartEndFrames()),
      {
        startReady: false,
        endReady: false,
        label: "首尾帧待生成",
      },
    );
  });

  it("renders storyboard reference and clip video as two separate cards", () => {
    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithStoryboardPanel(),
        videoModels: [
          {
            id: "doubao-seedance-2-0-260128",
            name: "Seedance 2.0",
            provider: "volcengine",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByLabelText("步骤 1 · 片段分镜图"));
    assert.ok(utils.getByLabelText("步骤 3 · 片段视频"));
    const chain = utils.getByLabelText("片段生图生视频链路");
    assert.ok(within(chain).getByText("选参考/绑定"));
    assert.ok(within(chain).getByText("生图：分镜图"));
    assert.ok(within(chain).getByText("生图：首尾帧"));
    assert.ok(within(chain).getByText("生视频：片段视频"));
    assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    assert.ok(utils.getByLabelText("视频参考来源"));
    assert.ok(utils.getByRole("option", { name: "片段宫格故事板（整张）" }));
    assert.ok(utils.getByLabelText("附加参考图 URL"));
    assert.ok(utils.getByLabelText("画面风格"));
    assert.ok(utils.getByLabelText("分镜 panel 数"));
    const storyboardModelSelect = utils.getByLabelText("分镜生图模型");
    assert.ok(
      within(storyboardModelSelect).getByRole("option", {
        name: "自动选择模型",
      }),
    );
    const videoModelSelect = utils.getByLabelText("视频模型");
    const visibleVideoControls = dom.window.document.querySelector(
      '[data-clip-video-primary-controls="visible"]',
    );
    assert.ok(visibleVideoControls);
    assert.ok(visibleVideoControls.contains(videoModelSelect));
    assert.equal(videoModelSelect.closest("details"), null);
    assert.ok(
      within(videoModelSelect).getByRole("option", { name: "自动选择模型" }),
    );
    assert.ok(
      within(videoModelSelect).getByRole("option", { name: "Seedance 2.0" }),
    );
    assert.ok(utils.getByLabelText("画面比例"));
    assert.ok(utils.getByRole("option", { name: "9:16" }));
    assert.ok(utils.getByLabelText("重做动作"));
    assert.ok(utils.getByLabelText("运动提示词覆盖"));
    assert.match(
      utils.getByLabelText("Timeline 视频目标时长").textContent || "",
      /Timeline 目标 1 秒，Provider 自动适配并裁切/,
    );
    assert.equal(utils.queryByText("时长（秒）"), null);
    assert.ok(utils.getByText("留空则使用 Timeline 镜头运动规划"));
  });

  it("keeps shared references available in a collapsed production context", async () => {
    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithStoryboardPanel(),
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
        storyboardEnvironmentImageOptions: [
          { url: "https://cdn.example/interior-env.png", label: "室内环境" },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(utils.getByLabelText("片段共享参考上下文")));
    const sharedContext = utils.getByLabelText(
      "片段共享参考上下文",
    ) as HTMLDetailsElement;
    assert.equal(sharedContext.closest("[data-clip-parameter-details]"), null);
    assert.equal(sharedContext.tagName, "DETAILS");
    assert.equal(sharedContext.open, false);
    assert.ok(within(sharedContext).getByText("共享参考"));
    assert.ok(within(sharedContext).getByText("快递员"));
    assert.ok(within(sharedContext).getByText(/IP 图 1 · 环境图 1/));
    assert.ok(
      within(sharedContext).getByText("会用于分镜、首尾帧和视频任务。"),
    );
  });

  it("uses the full storyboard sheet when keyframes are missing", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 96, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;
    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithoutStartEndFrames(),
      }),
      { container: dom.window.document.body },
    );

    assert.ok(utils.getAllByText("首尾帧待生成").length >= 1);
    assert.equal(
      (utils.getByLabelText("视频参考来源") as HTMLSelectElement).value,
      "clip_storyboard_sheet",
    );
    assert.equal(
      (
        utils.getByRole("button", {
          name: "生成/重做此片段视频",
        }) as HTMLButtonElement
      ).disabled,
      false,
    );
    assert.equal(
      (utils.getByRole("option", { name: /首尾帧/ }) as HTMLOptionElement)
        .disabled,
      true,
    );
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
        reference_mode: "clip_storyboard_sheet",
        use_clip_storyboard: true,
      }),
    );
  });

  it("uses start and end frames when the storyboard is missing", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 97, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithoutStoryboardPanel(),
      }),
      { container: dom.window.document.body },
    );

    const videoButton = utils.getByRole("button", {
      name: "生成/重做此片段视频",
    }) as HTMLButtonElement;
    assert.equal(videoButton.disabled, false);
    assert.equal(
      (utils.getByLabelText("视频参考来源") as HTMLSelectElement).value,
      "start_end",
    );
    fireEvent.click(videoButton);
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        action: "re_cut",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: true,
        return_last_frame: true,
      }),
    );
  });

  it("does not let manual references bypass the video generation image gate", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 98, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithoutVisualReferences(),
      }),
      { container: dom.window.document.body },
    );

    fireEvent.input(utils.getByLabelText("附加参考图 URL"), {
      target: { value: "https://manual.example/ref.png" },
    });
    fireEvent.change(utils.getByLabelText("视频参考来源"), {
      target: { value: "manual_refs" },
    });
    const videoButton = utils.getByRole("button", {
      name: "生成/重做此片段视频",
    }) as HTMLButtonElement;
    assert.equal(videoButton.disabled, true);
    fireEvent.submit(videoButton.closest("form")!);
    await waitFor(() => assert.equal(calls.length, 0));
  });

  it("allows Timeline shot plan clips to generate video without extra keyframes", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 99, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithTimelineShotPlanOnly(),
      }),
      { container: dom.window.document.body },
    );

    const videoButton = utils.getByRole("button", {
      name: "生成/重做此片段视频",
    }) as HTMLButtonElement;
    assert.equal(videoButton.disabled, false);
    fireEvent.click(videoButton);
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].url,
      "/api/v1/timelines/8/clips/video_scene_1_beat_1_001/rework/video",
    );
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        action: "re_cut",
        resolution: "720p",
        asset_role: "generated_video",
        use_end_frame: true,
        return_last_frame: true,
      }),
    );
  });

  it("requires operator review for short-drama review-gated video clips", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 77, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithPendingHumanReview(),
      }),
      { container: dom.window.document.body },
    );

    const videoButton = utils.getByRole("button", {
      name: "生成/重做此片段视频",
    }) as HTMLButtonElement;
    assert.equal(videoButton.disabled, true);
    assert.ok(utils.getByText("先完成人工复核"));

    const reviewControl = utils.getByLabelText("已完成人工复核");
    assert.equal(reviewControl.closest("details"), null);
    assert.ok(
      dom.window.document
        .querySelector('[data-clip-human-review-control="visible"]')
        ?.contains(reviewControl),
    );
    fireEvent.click(reviewControl);

    assert.equal(videoButton.disabled, false);
    fireEvent.click(videoButton);
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
        reference_mode: "clip_storyboard_sheet",
        use_clip_storyboard: true,
        operator_reviewed: true,
      }),
    );
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
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].url,
      "/api/v1/timelines/8/clips/video_scene_1_beat_1_001/storyboard/generate",
    );
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        reference_images: ["https://manual.example/ref.png"],
      }),
    );

    fireEvent.change(utils.getByLabelText("视频参考来源"), {
      target: { value: "clip_storyboard_sheet" },
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
        reference_mode: "clip_storyboard_sheet",
        use_clip_storyboard: true,
        reference_images: ["https://manual.example/ref.png"],
      }),
    );
  });

  it("keeps an explicit storyboard panel count when the operator selects one", async () => {
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

    fireEvent.change(utils.getByLabelText("分镜 panel 数"), {
      target: { value: "6" },
    });
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        panel_count: 6,
      }),
    );
  });

  it("submits selected role IP bindings with clip storyboard generation", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 90, status: "pending" }), {
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
        episodeCharacters: [
          episodeCharacter("林晚", 31),
          episodeCharacter("快递员", 32),
        ],
      }),
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("绑定角色 IP"));
    fireEvent.click(utils.getByLabelText("绑定角色 IP 快递员"));
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
      }),
    );
  });

  it("submits the selected image model with clip storyboard generation", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 93, status: "pending" }), {
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
        imageModels: [
          {
            id: "doubao-seedream-4-5-251128",
            model_id: "volcengine:doubao-seedream-4-5-251128",
            name: "Seedream 4.5",
            provider: "volcengine",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    fireEvent.change(utils.getByLabelText("分镜生图模型"), {
      target: { value: "volcengine:doubao-seedream-4-5-251128" },
    });
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        model: "volcengine:doubao-seedream-4-5-251128",
      }),
    );
  });

  it("defaults role IP bindings from selected clip character names", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 96, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithCharacterNames(["快递员"]),
        episodeCharacters: [
          episodeCharacter("林晚", 31),
          episodeCharacter("快递员", 32),
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() =>
      assert.equal(
        (utils.getByLabelText("绑定角色 IP 快递员") as HTMLInputElement)
          .checked,
        true,
      ),
    );
    assert.equal(
      (utils.getByLabelText("绑定角色 IP 林晚") as HTMLInputElement).checked,
      false,
    );
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
      }),
    );
  });

  it("auto-selects default IP and environment thumbnails for storyboard generation", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 91, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
        storyboardEnvironmentImageOptions: [
          {
            url: "https://cdn.example/interior-env.png",
            label: "室内环境",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(hasText(utils, "IP 图：1 张")));
    assert.ok(utils.getByAltText("已选 IP 图 快递员 正面"));
    assert.ok(utils.getByAltText("已选环境图 室内环境"));
    assert.equal(utils.queryByLabelText("选择 IP 图 快递员 正面"), null);
    const ipDialog = openReferencePicker(utils, "选择 IP 图");
    assert.equal(
      within(ipDialog)
        .getByLabelText("选择 IP 图 快递员 正面")
        .getAttribute("aria-pressed"),
      "true",
    );
    fireEvent.click(within(ipDialog).getByRole("button", { name: "应用选择" }));
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
        character_reference_images: ["https://cdn.example/courier-pose.png"],
        environment_reference_images: ["https://cdn.example/interior-env.png"],
      }),
    );
  });

  it("keeps reference image controls visible outside collapsed parameter menus", async () => {
    const utils = render(
      React.createElement(TimelineClipProviderReworkControls, {
        timelineId: 8,
        timelineVersion: 3,
        clipId: "video_scene_1_beat_1_001",
        item: videoClipWithStoryboardPanel(),
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
        storyboardEnvironmentImageOptions: [
          {
            url: "https://cdn.example/interior-env.png",
            label: "室内环境",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() =>
      assert.ok(utils.getByRole("button", { name: "选择 IP 图" })),
    );

    const referenceControls = [
      utils.getByRole("button", { name: "选择 IP 图" }),
      utils.getByRole("button", { name: "选择环境图" }),
      utils.getByLabelText("附加参考图 URL"),
      utils.getByLabelText("视频参考来源"),
    ];

    for (const control of referenceControls) {
      assert.equal(control.closest("[data-clip-parameter-details]"), null);
    }
  });

  it("deselects default thumbnails and clears selections on demand", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 95, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
        storyboardEnvironmentImageOptions: [
          {
            url: "https://cdn.example/interior-env.png",
            label: "室内环境",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(hasText(utils, "IP 图：1 张")));
    assert.equal(utils.getAllByText("已选 1/1").length, 2);
    const ipDialog = openReferencePicker(utils, "选择 IP 图");
    fireEvent.click(within(ipDialog).getByLabelText("选择 IP 图 快递员 正面"));
    fireEvent.click(within(ipDialog).getByRole("button", { name: "应用选择" }));
    fireEvent.click(utils.getByLabelText("环境图清空"));
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
      }),
    );
  });

  it("discards staged reference image changes when picker is cancelled", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 97, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(hasText(utils, "IP 图：1 张")));
    const ipDialog = openReferencePicker(utils, "选择 IP 图");
    fireEvent.click(within(ipDialog).getByLabelText("选择 IP 图 快递员 正面"));
    fireEvent.click(within(ipDialog).getByRole("button", { name: "取消" }));
    assert.ok(hasText(utils, "IP 图：1 张"));

    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
        character_reference_images: ["https://cdn.example/courier-pose.png"],
      }),
    );
  });

  it("clears reference image selections from the picker footer", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 98, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(hasText(utils, "IP 图：1 张")));
    const ipDialog = openReferencePicker(utils, "选择 IP 图");
    fireEvent.click(within(ipDialog).getByRole("button", { name: "清空" }));
    fireEvent.click(within(ipDialog).getByRole("button", { name: "应用选择" }));
    assert.ok(hasText(utils, "IP 图：0 张"));

    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() => assert.equal(calls.length, 1));
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
      }),
    );
  });

  it("shows and submits selected IP and environment bindings with video rework", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 93, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
        storyboardEnvironmentImageOptions: [
          {
            url: "https://cdn.example/interior-env.png",
            label: "室内环境",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(hasText(utils, "IP 图：1 张")));

    const videoBinding = utils.getByLabelText("视频生成绑定上下文");
    assert.ok(videoBinding);
    assert.ok(within(videoBinding).getByText("视频生成绑定上下文"));
    assert.ok(within(videoBinding).getByText("已携带绑定"));
    assert.ok(within(videoBinding).getByText("角色 IP：快递员"));
    assert.ok(within(videoBinding).getByText("IP 图：1 张"));
    assert.ok(within(videoBinding).getByText("环境图：1 张"));
    assert.ok(
      within(videoBinding).getByText("视频任务会携带上方已选 IP 和环境图。"),
    );

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
        reference_mode: "clip_storyboard_sheet",
        use_clip_storyboard: true,
        character_virtual_ip_ids: [32],
        character_reference_images: ["https://cdn.example/courier-pose.png"],
        environment_reference_images: ["https://cdn.example/interior-env.png"],
      }),
    );
  });

  it("queues selected IP and environment bindings with keyframe generation", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 94, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
        storyboardEnvironmentImageOptions: [
          {
            url: "https://cdn.example/interior-env.png",
            label: "室内环境",
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(hasText(utils, "IP 图：1 张")));
    fireEvent.click(utils.getByRole("button", { name: "生成首尾帧" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].url,
      "/api/v1/timelines/8/clips/video_scene_1_beat_1_001/keyframes/generate",
    );
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        generation_profile: "clip_keyframes",
        aspect_ratio: "9:16",
        character_virtual_ip_ids: [32],
        character_reference_images: ["https://cdn.example/courier-pose.png"],
        environment_reference_images: ["https://cdn.example/interior-env.png"],
      }),
    );
  });

  it("loads selected environment details before showing environment thumbnails", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      if (String(url) === "/api/v1/story-structure/environments/1") {
        return new Response(
          JSON.stringify({
            id: 1,
            name: "办公室",
            reference_images: ["https://cdn.example/office-env.png"],
            created_at: "2026-06-09T00:00:00Z",
            updated_at: "2026-06-09T00:00:00Z",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      }
      return new Response(JSON.stringify({ task_id: 92, status: "pending" }), {
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
        episodeCharacters: [episodeCharacter("快递员", 32)],
        environments: [
          {
            id: 1,
            name: "办公室",
            created_at: "2026-06-09T00:00:00Z",
            updated_at: "2026-06-09T00:00:00Z",
          },
        ],
        selectedEnvironmentId: 1,
        storyboardCharacterImageOptions: {
          32: [
            {
              url: "https://cdn.example/courier-pose.png",
              label: "快递员 正面",
            },
          ],
        },
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(utils.getByAltText("已选环境图 办公室 1")));
    const envDialog = openReferencePicker(utils, "选择环境图");
    assert.equal(
      within(envDialog)
        .getByLabelText("选择环境图 办公室 1")
        .getAttribute("aria-pressed"),
      "true",
    );
    fireEvent.click(
      within(envDialog).getByRole("button", { name: "应用选择" }),
    );
    fireEvent.click(utils.getByRole("button", { name: "生成片段分镜图" }));
    await waitFor(() =>
      assert.ok(
        calls.some((call) => String(call.url).includes("/storyboard/generate")),
      ),
    );

    const storyboardCall = calls.find((call) =>
      String(call.url).includes("/storyboard/generate"),
    );
    assert.equal(
      storyboardCall?.init?.body,
      JSON.stringify({
        expected_version: 3,
        style: "live_action",
        generation_profile: "clip_storyboard",
        size: "1536x1536",
        aspect_ratio: "1:1",
        character_virtual_ip_ids: [32],
        character_reference_images: ["https://cdn.example/courier-pose.png"],
        environment_reference_images: ["https://cdn.example/office-env.png"],
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
      start_frame_asset_ref: {
        file_url: "https://cdn.example/start-frame.png",
      },
      end_frame_asset_ref: {
        file_url: "https://cdn.example/end-frame.png",
      },
    },
  };
}

function openReferencePicker(utils: ReturnType<typeof render>, name: string) {
  fireEvent.click(utils.getByRole("button", { name }));
  return utils.getByRole("dialog");
}

function hasText(utils: ReturnType<typeof render>, text: string) {
  return utils.queryAllByText(text).length > 0;
}

function videoClipWithoutStartEndFrames() {
  const clip = videoClipWithStoryboardPanel();
  return {
    ...clip,
    meta: {
      ...clip.meta,
      start_frame_asset_ref: undefined,
      end_frame_asset_ref: undefined,
      start_frame_url: undefined,
      end_frame_url: undefined,
    },
  };
}

function videoClipWithoutStoryboardPanel() {
  const clip = videoClipWithStoryboardPanel();
  return {
    ...clip,
    meta: {
      ...clip.meta,
      source_refs: {},
      clip_storyboard_sheet_asset_ref: undefined,
    },
  };
}

function videoClipWithoutVisualReferences() {
  const clip = videoClipWithoutStoryboardPanel();
  return {
    ...clip,
    meta: {
      ...clip.meta,
      start_frame_asset_ref: undefined,
      end_frame_asset_ref: undefined,
      start_frame_url: undefined,
      end_frame_url: undefined,
    },
  };
}

function videoClipWithTimelineShotPlanOnly() {
  const clip = videoClipWithoutVisualReferences();
  return {
    ...clip,
    meta: {
      ...clip.meta,
      start_frame_asset_ref: undefined,
      end_frame_asset_ref: undefined,
      start_frame_url: undefined,
      end_frame_url: undefined,
      source_refs: {
        timeline_shot_plan: {
          video_prompt: "Timeline shot plan motion prompt",
          motion_timeline: [{ at_ms: 0, action: "open with a tense push-in" }],
        },
      },
    },
  };
}

function videoClipWithPendingHumanReview() {
  const clip = videoClipWithStoryboardPanel();
  return {
    ...clip,
    meta: {
      ...clip.meta,
      source_refs: {
        ...clip.meta.source_refs,
        human_review: {
          required: true,
          status: "pending",
        },
      },
    },
  };
}

function videoClipWithCharacterNames(names: string[]) {
  const clip = videoClipWithStoryboardPanel();
  return {
    ...clip,
    meta: {
      ...clip.meta,
      characters_involved: names,
    },
  };
}

function episodeCharacter(characterName: string, virtualIpId: number) {
  return {
    id: virtualIpId + 1000,
    business_id: `ep_char_${virtualIpId}`,
    episode_id: 1,
    episode_business_id: "episode_1",
    virtual_ip_id: virtualIpId,
    virtual_ip_business_id: `vip_${virtualIpId}`,
    character_name: characterName,
    role_type: "temporary",
    importance: 3,
    created_at: "2026-06-09T00:00:00Z",
    updated_at: "2026-06-09T00:00:00Z",
  };
}
