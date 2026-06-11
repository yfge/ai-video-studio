import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  EpisodeWorkspaceHeader,
  type WorkflowStatus,
} from "../src/components/features/episode";
import { EpisodeTimelineWorkspace } from "../src/components/features/episode/EpisodeTimelineWorkspace";
import { AlertModalProvider } from "../src/components/shared/modals";
import { ToastProvider } from "../src/components/shared/notifications";
import { clearAvailableModelsCache } from "../src/hooks/useAvailableModels";
import type {
  Episode,
  Script,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).HTMLSelectElement = dom.window.HTMLSelectElement;
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
    mockWorkspaceFetch({
      resolvedVideos: resolvedVideos("https://example.com/clip-ready.mp4"),
    });

    const utils = render(
      workspace(
        videoTimeline(),
        undefined,
        resolvedVideos("https://example.com/clip-ready.mp4"),
      ),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByText("片段分镜管理"));
      assert.ok(utils.getByText("片段分镜图"));
      assert.ok(utils.getByText("片段视频"));
    });
    assert.equal(utils.queryByText("片段检查器"), null);
    assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    const video = utils.getByLabelText("播放选中片段视频");
    assert.equal(video.getAttribute("src"), "https://example.com/clip-ready.mp4");
  });

  it("renders succeeded timeline render output as an embedded player", async () => {
    mockWorkspaceFetch({
      resolvedVideos: resolvedVideos("https://example.com/clip-ready.mp4"),
      renderJobs: [
        {
          id: 9,
          business_id: "render_9",
          timeline_id: 8,
          timeline_version: 3,
          render_type: "final",
          preset_hash: "hash",
          preset: {},
          status: "succeeded",
          progress: 100,
          output_asset_id: 18,
          output_asset: {
            id: 18,
            business_id: "asset_18",
            asset_type: "video",
            origin: "rendered",
            file_url: "https://example.com/final.mp4",
            created_at: "2026-06-11T00:00:00Z",
            updated_at: "2026-06-11T00:00:00Z",
          },
          created_at: "2026-06-11T00:00:00Z",
          updated_at: "2026-06-11T00:00:00Z",
        },
      ],
    });

    const utils = render(
      workspace(
        videoTimeline(),
        undefined,
        resolvedVideos("https://example.com/clip-ready.mp4"),
      ),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      const video = utils.getByLabelText("播放渲染成片");
      assert.equal(video.getAttribute("src"), "https://example.com/final.mp4");
    });
  });

  it("renders a compact production path header with one primary next action", () => {
    const selectedScript = script();
    const workflowStatus: WorkflowStatus = {
      script: "ready",
      timeline: "pending",
      storyboard: "pending",
    };
    const utils = render(
      <EpisodeWorkspaceHeader
        episode={episode()}
        script={selectedScript}
        scripts={[selectedScript]}
        selectedScriptId={selectedScript.id}
        workflowStatus={workflowStatus}
        activeTab="timeline"
        onTabChange={() => {}}
        onNavigateBack={() => {}}
        onGenerateScript={() => {}}
        onGenerateTimeline={() => {}}
        onSelectScript={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("生产主线"));
    assert.ok(utils.getByLabelText("当前剧本"));
    assert.equal(
      utils.getAllByRole("button", { name: "生成 Timeline" }).length,
      1,
    );
    assert.equal(utils.queryByText("步骤 1"), null);
    assert.equal(utils.queryByRole("button", { name: "剧集概要" }), null);
    assert.ok(utils.getByRole("button", { name: "剧本设置" }));
    assert.ok(utils.getByRole("button", { name: "分镜参考" }));
    assert.ok(utils.getByRole("button", { name: "临时角色/IP 绑定" }));
  });

  it("keeps Timeline generation controls in a compact production setup row", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("Timeline 生成设置"));
      assert.equal(
        utils.getAllByRole("button", { name: "生成 Timeline" }).length,
        1,
      );
    });
  });

  it("defaults to the first video clip so production entries are visible on deep links", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueBeforeVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByText("片段分镜管理"));
      assert.ok(utils.getAllByText("视频 1").length >= 2);
    });
    assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
  });

  it("honors a clip deep link when opening the Timeline workspace", async () => {
    mockWorkspaceFetch();

    const utils = render(
      workspace(twoVideoTimeline(), "video_scene_1_beat_2_002"),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getAllByText("第二个视频").length >= 2);
    });
  });

  it("keeps provider generation hidden for non-video timeline clips", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => assert.ok(utils.getByText("选中片段生产")));
    assert.ok(utils.getAllByText("native dialogue").length >= 1);
    assert.equal(utils.queryByText("片段检查器"), null);
    assert.equal(utils.queryByRole("button", { name: "生成片段分镜图" }), null);
    assert.equal(
      utils.queryByRole("button", { name: "生成/重做此片段视频" }),
      null,
    );
  });

  it("keeps environment binding available for clips without normalized scenes", async () => {
    mockWorkspaceFetch({
      environments: [
        {
          id: 1,
          name: "办公室",
          created_at: "2026-06-09T00:00:00Z",
          updated_at: "2026-06-09T00:00:00Z",
        },
      ],
      environmentDetails: {
        1: {
          id: 1,
          name: "办公室",
          reference_images: ["https://cdn.example/office-env.png"],
          created_at: "2026-06-09T00:00:00Z",
          updated_at: "2026-06-09T00:00:00Z",
        },
      },
    });

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(
        utils.getByText("未匹配规范化场景，当前环境仅用于片段生成参考。"),
      );
      assert.ok(utils.getByLabelText("片段环境"));
      assert.ok(utils.getByText("去临时角色绑定 IP"));
    });

    fireEvent.change(utils.getByLabelText("片段环境"), {
      target: { value: "1" },
    });

    await waitFor(() => assert.ok(utils.getByAltText("环境图 办公室 1")));
    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择环境图 办公室 1")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );

    assert.ok(utils.getByLabelText("视频生成绑定上下文"));
    assert.ok(utils.getByText("环境图：1 张"));
  });
});

function workspace(
  selectedTimelineSpec: TimelineResponse,
  initialSelectedClipId?: string,
  resolvedVideosPayload: TimelineResolvedVideoListResponse = resolvedVideosMissing(),
) {
  return (
    <AlertModalProvider>
      <ToastProvider>
        <EpisodeTimelineWorkspace
          selectedScriptId={128}
          initialSelectedClipId={initialSelectedClipId}
          selectedScript={{ version: "1.0" } as Script}
          selectedTimelineSpec={selectedTimelineSpec}
          resolvedVideos={resolvedVideosPayload}
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
          onNavigateToCharacters={() => {}}
        />
      </ToastProvider>
    </AlertModalProvider>
  );
}

function episode(): Episode {
  return {
    id: 1,
    business_id: "episode_1",
    story_id: 7,
    episode_number: 1,
    title: "末日安全屋",
    duration_minutes: 3,
    status: "draft",
    created_at: "2026-06-11T00:00:00Z",
    updated_at: "2026-06-11T00:00:00Z",
  };
}

function script(): Script {
  return {
    id: 128,
    business_id: "script_128",
    episode_id: 1,
    title: "第1集剧本",
    format_type: "screenplay",
    language: "zh-CN",
    status: "draft",
    version: "1.0",
    created_at: "2026-06-11T00:00:00Z",
    updated_at: "2026-06-11T00:00:00Z",
  };
}

function mockWorkspaceFetch({
  environments = [],
  environmentDetails = {},
  resolvedVideos,
  renderJobs = [],
}: {
  environments?: unknown[];
  environmentDetails?: Record<number, unknown>;
  resolvedVideos?: unknown;
  renderJobs?: unknown[];
} = {}) {
  globalThis.fetch = (async (url: RequestInfo | URL) => {
    const path = String(url);
    if (path.includes("/api/v1/ai/models/available")) {
      return jsonResponse({ models: [], default: "" });
    }
    if (path.includes("/characters")) {
      return jsonResponse({ items: [], total: 0, page: 1, page_size: 20 });
    }
    const environmentDetailMatch = path.match(
      /\/api\/v1\/story-structure\/environments\/(\d+)$/,
    );
    if (environmentDetailMatch) {
      return jsonResponse(
        environmentDetails[Number(environmentDetailMatch[1])] || {},
      );
    }
    if (path.includes("/api/v1/story-structure/environments")) {
      return jsonResponse(environments);
    }
    if (path.includes("/resolved-videos")) {
      return jsonResponse(resolvedVideos || resolvedVideosMissing());
    }
    if (path.includes("/render-jobs")) {
      return jsonResponse({ items: renderJobs });
    }
    if (path.includes("/clip-assets")) {
      return jsonResponse({ items: [] });
    }
    return jsonResponse({});
  }) as typeof fetch;
}

function resolvedVideos(url: string): TimelineResolvedVideoListResponse {
  return {
    timeline_id: 8,
    timeline_version: 3,
    ready: true,
    video_clip_count: 1,
    missing_clip_count: 0,
    generating_clip_count: 0,
    items: [
      {
        clip_id: "video_scene_1_beat_1_001",
        status: "ready",
        url,
        source: "timeline_clip_asset:provider_rework",
        start_ms: 0,
        end_ms: 1200,
        duration_seconds: 1.2,
      },
    ],
  };
}

function resolvedVideosMissing(): TimelineResolvedVideoListResponse {
  return {
    timeline_id: 8,
    timeline_version: 3,
    ready: false,
    video_clip_count: 1,
    missing_clip_count: 1,
    generating_clip_count: 0,
    items: [
      {
        clip_id: "video_scene_1_beat_1_001",
        status: "missing",
        reason: "missing_video_url",
        start_ms: 0,
        end_ms: 1200,
        duration_seconds: 1.2,
      },
    ],
  };
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

function twoVideoTimeline() {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "第一个视频",
        },
        {
          clip_id: "video_scene_1_beat_2_002",
          track_type: "video",
          start_ms: 1300,
          end_ms: 2400,
          text: "第二个视频",
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
