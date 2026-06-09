import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { EpisodeTimelineWorkspace } from "../src/components/features/episode/EpisodeTimelineWorkspace";
import { AlertModalProvider } from "../src/components/shared/modals";
import { clearAvailableModelsCache } from "../src/hooks/useAvailableModels";
import type { Script, TimelineResponse } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;

describe("EpisodeTimelineWorkspace layout", () => {
  afterEach(() => {
    cleanup();
    clearAvailableModelsCache();
    globalThis.fetch = originalFetch;
    localStorage.clear();
  });

  it("puts video clip generation in the main canvas instead of a right inspector", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByText("故事板参考"));
      assert.ok(utils.getByText("片段视频"));
    });
    assert.equal(utils.queryByText("片段检查器"), null);
    assert.ok(utils.getByRole("button", { name: "生成故事板参考图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
  });

  it("defaults to the first video clip so production entries are visible on deep links", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueBeforeVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getAllByText("视频 1").length >= 2);
    });
    assert.ok(utils.getByRole("button", { name: "生成故事板参考图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
  });

  it("keeps provider generation hidden for non-video timeline clips", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => assert.ok(utils.getByText("选中片段生产")));
    assert.ok(utils.getAllByText("native dialogue").length >= 1);
    assert.equal(utils.queryByText("片段检查器"), null);
    assert.equal(
      utils.queryByRole("button", { name: "生成故事板参考图" }),
      null,
    );
    assert.equal(
      utils.queryByRole("button", { name: "生成/重做此片段视频" }),
      null,
    );
  });
});

function workspace(selectedTimelineSpec: TimelineResponse) {
  return (
    <AlertModalProvider>
      <EpisodeTimelineWorkspace
        selectedScriptId={128}
        selectedScript={{ version: "1.0" } as Script}
        selectedTimelineSpec={selectedTimelineSpec}
        selectedAudioTimeline={null}
        selectedStoryboard={null}
        normalizedScenes={[]}
        normalizedScenesLoading={false}
        normalizedScenesError={null}
        timingModel=""
        setTimingModel={() => {}}
        useDurationControl={false}
        setUseDurationControl={() => {}}
        onNavigateToTasks={() => {}}
        onNavigateToScript={() => {}}
        onNavigateToStoryboard={() => {}}
      />
    </AlertModalProvider>
  );
}

function mockWorkspaceFetch() {
  globalThis.fetch = (async (url: RequestInfo | URL) => {
    const path = String(url);
    if (path.includes("/api/v1/ai/models/available")) {
      return jsonResponse({ models: [], default: "" });
    }
    if (path.includes("/api/v1/story-structure/environments")) {
      return jsonResponse([]);
    }
    if (path.includes("/render-jobs")) {
      return jsonResponse({ items: [] });
    }
    if (path.includes("/clip-assets")) {
      return jsonResponse({ items: [] });
    }
    return jsonResponse({});
  }) as typeof fetch;
}

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

function videoTimeline() {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "视频 1",
        },
      ],
    },
  ]);
}

function dialogueTimeline() {
  return baseTimeline([
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
  ]);
}

function dialogueBeforeVideoTimeline() {
  return baseTimeline([
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
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "视频 1",
        },
      ],
    },
  ]);
}

function baseTimeline(tracks: NonNullable<TimelineResponse["spec"]>["tracks"]) {
  return {
    id: 8,
    business_id: "timeline_8",
    episode_id: 1,
    script_id: 128,
    title: "Timeline",
    status: "draft",
    version: 3,
    created_at: "2026-06-04T00:00:00Z",
    updated_at: "2026-06-04T00:00:00Z",
    spec: {
      spec_version: "timeline.v1",
      episode_id: 1,
      script_id: 128,
      version: 3,
      tracks,
    },
  } satisfies TimelineResponse;
}
