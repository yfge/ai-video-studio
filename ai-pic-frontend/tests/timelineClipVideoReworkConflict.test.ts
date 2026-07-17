import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import { queueTimelineClipVideoReworkWithVersionRefresh } from "../src/components/features/episode/TimelineClipVideoReworkSubmission";
import { httpClient } from "../src/utils/api/client";
import type { TimelineResponse } from "../src/utils/api/types";

const originalFetch = globalThis.fetch;

describe("timeline clip video rework conflicts", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("surfaces FastAPI detail and HTTP status", async () => {
    globalThis.fetch = (async () =>
      new Response(JSON.stringify({ detail: "timeline version conflict" }), {
        status: 409,
        statusText: "Conflict",
        headers: { "content-type": "application/json" },
      })) as typeof fetch;

    const response = await httpClient("/api/test-conflict");

    assert.equal(response.success, false);
    assert.equal(response.status, 409);
    assert.equal(response.error, "timeline version conflict");
  });

  it("refreshes the parent without retrying the video request", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const refreshed: TimelineResponse[] = [];
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      if (calls.length === 1) return conflictResponse();
      return jsonResponse(timelineResponse(16));
    }) as typeof fetch;

    const response = await queueTimelineClipVideoReworkWithVersionRefresh({
      timelineId: 76,
      clipId: "video_scene_591_beat_4352_001",
      payload: {
        expected_version: 15,
        action: "re_cut",
        model: "volcengine:doubao-seedance-2-0-260128",
        operator_reviewed: true,
      },
      onTimelineRefreshed: (timeline) => {
        refreshed.push(timeline);
      },
    });

    assert.equal(response.success, false);
    assert.equal(response.status, 409);
    assert.equal(
      response.error,
      "Timeline 已更新，已刷新；本次未提交视频生成任务，不会产生生成费用。请重新复核后再生成。",
    );
    assert.deepEqual(
      calls.map((call) => call.url),
      [
        "/api/v1/timelines/76/clips/video_scene_591_beat_4352_001/rework/video",
        "/api/v1/timelines/76",
      ],
    );
    assert.equal(refreshed[0]?.version, 16);
  });

  it("does not retry when the clip disappeared from the latest Timeline", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    let refreshedVersion: number | null = null;
    globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      if (calls.length === 1) return conflictResponse();
      return jsonResponse(timelineResponse(16, []));
    }) as typeof fetch;

    const response = await queueTimelineClipVideoReworkWithVersionRefresh({
      timelineId: 76,
      clipId: "video_scene_591_beat_4352_001",
      payload: { expected_version: 15, action: "re_cut" },
      onTimelineRefreshed: (timeline) => {
        refreshedVersion = timeline.version;
      },
    });

    assert.equal(response.success, false);
    assert.equal(response.status, 409);
    assert.equal(
      response.error,
      "Timeline 已更新，已刷新；本次未提交视频生成任务，不会产生生成费用。请重新复核后再生成。",
    );
    assert.equal(refreshedVersion, 16);
    assert.equal(calls.length, 2);
  });

  it("does not refresh or retry non-conflict responses", async () => {
    let callCount = 0;
    globalThis.fetch = (async () => {
      callCount += 1;
      return jsonResponse({ task_id: 6466, status: "pending" });
    }) as typeof fetch;

    const response = await queueTimelineClipVideoReworkWithVersionRefresh({
      timelineId: 76,
      clipId: "video_scene_591_beat_4352_001",
      payload: { expected_version: 15, action: "re_cut" },
    });

    assert.equal(response.success, true);
    assert.equal(response.data?.task_id, 6466);
    assert.equal(callCount, 1);
  });
});

function conflictResponse() {
  return new Response(JSON.stringify({ detail: "timeline version conflict" }), {
    status: 409,
    statusText: "Conflict",
    headers: { "content-type": "application/json" },
  });
}

function jsonResponse(data: unknown) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

function timelineResponse(
  version: number,
  clipIds = ["video_scene_591_beat_4352_001"],
): TimelineResponse {
  return {
    id: 76,
    business_id: "timeline-76",
    episode_id: 194,
    script_id: 146,
    title: "Timeline 76",
    status: "draft",
    version,
    created_at: "2026-07-17T10:00:00Z",
    updated_at: "2026-07-17T10:30:00Z",
    spec: {
      spec_version: "timeline.v1",
      episode_id: 194,
      script_id: 146,
      version,
      tracks: [
        {
          track_type: "video",
          clips: clipIds.map((clipId) => ({
            clip_id: clipId,
            track_type: "video",
            start_ms: 0,
            end_ms: 6000,
          })),
        },
      ],
    },
  };
}
