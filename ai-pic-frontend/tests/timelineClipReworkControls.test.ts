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

    assert.ok(utils.getByText("故事板参考"));
    assert.ok(utils.getByText("片段视频"));
    assert.ok(utils.getByRole("button", { name: "生成故事板参考图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    assert.ok(utils.getByLabelText("视频参考来源"));
    assert.ok(utils.getByRole("option", { name: "故事板 Panel 4" }));
    assert.ok(utils.getByLabelText("附加参考图 URL"));
    assert.ok(utils.getByLabelText("画面风格"));
    assert.ok(utils.getByLabelText("故事板 panel 数"));
    assert.ok(utils.getByLabelText("视频模型"));
    assert.ok(utils.getByRole("option", { name: "自动选择模型" }));
    assert.ok(utils.getByRole("option", { name: "Seedance 2.0" }));
    assert.ok(utils.getByLabelText("画面比例"));
    assert.ok(utils.getByRole("option", { name: "9:16" }));
    assert.ok(utils.getByLabelText("重做动作"));
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
    fireEvent.click(utils.getByRole("button", { name: "生成故事板参考图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        panel_count: 4,
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

    assert.ok(utils.getByAltText("IP 图 快递员 正面"));
    assert.ok(utils.getByAltText("环境图 室内环境"));
    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择 IP 图 快递员 正面")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );
    fireEvent.click(utils.getByRole("button", { name: "生成故事板参考图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        panel_count: 4,
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

    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择 IP 图 快递员 正面")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );
    assert.equal(
      utils.getAllByText("已选 1/1，选中的图会作为生成参考").length,
      2,
    );
    fireEvent.click(utils.getByLabelText("选择 IP 图 快递员 正面"));
    fireEvent.click(utils.getByLabelText("环境图清空"));
    fireEvent.click(utils.getByRole("button", { name: "生成故事板参考图" }));
    await waitFor(() => assert.equal(calls.length, 1));

    assert.equal(
      calls[0].init?.body,
      JSON.stringify({
        expected_version: 3,
        panel_count: 4,
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

    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择 IP 图 快递员 正面")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );

    assert.ok(utils.getByLabelText("视频生成绑定上下文"));
    assert.ok(utils.getByText("视频生成绑定上下文"));
    assert.ok(utils.getByText("已携带绑定"));
    assert.ok(utils.getByText("角色 IP：快递员"));
    assert.ok(utils.getByText("IP 图：1 张"));
    assert.ok(utils.getByText("环境图：1 张"));
    assert.ok(utils.getByText("视频任务会携带上方已选 IP 和环境图。"));

    fireEvent.click(utils.getByRole("button", { name: "生成/重做此片段视频" }));
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

    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择 IP 图 快递员 正面")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );
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

    await waitFor(() => assert.ok(utils.getByAltText("环境图 办公室 1")));
    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择环境图 办公室 1")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );
    fireEvent.click(utils.getByRole("button", { name: "生成故事板参考图" }));
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
        panel_count: 4,
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
