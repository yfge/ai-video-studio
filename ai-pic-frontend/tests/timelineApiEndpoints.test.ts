import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import { timelineAPI } from "../src/utils/api/endpoints/timeline.endpoints";

const originalFetch = globalThis.fetch;

describe("timeline API endpoints", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("queues clip-scoped storyboard generation through the selected clip endpoint", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return new Response(JSON.stringify({ task_id: 77, status: "pending" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    const res = await timelineAPI.generateTimelineClipStoryboard(
      8,
      "video_scene_001_beat_002_001",
      {
        expected_version: 3,
        panel_count: 4,
      },
    );

    assert.equal(res.success, true);
    assert.equal(res.data?.task_id, 77);
    assert.equal(
      calls[0].url,
      "/api/v1/timelines/8/clips/video_scene_001_beat_002_001/storyboard/generate",
    );
    assert.equal(calls[0].init?.method, "POST");
    assert.equal(
      calls[0].init?.body,
      JSON.stringify({ expected_version: 3, panel_count: 4 }),
    );
  });
});
