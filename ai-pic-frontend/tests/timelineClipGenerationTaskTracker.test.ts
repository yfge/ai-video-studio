import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  useTimelineClipGenerationTaskTracker,
  type ClipGenerationTaskMap,
} from "../src/components/features/episode/useTimelineClipGenerationTaskTracker";
import { TimelineClipTaskStatusLine } from "../src/components/features/episode/TimelineClipTaskStatusLine";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;

function TrackerHarness({
  onCompleted,
  onNotify,
  onReady,
}: {
  onCompleted?: (kind: string, taskId: number) => void;
  onNotify?: (message: string, variant: string) => void;
  onReady: (
    track: (kind: any, taskId: number, clipId: string | null) => void,
    tasks: ClipGenerationTaskMap,
  ) => void;
}) {
  const tracker = useTimelineClipGenerationTaskTracker({
    onCompleted,
    onNotify,
    pollIntervalMs: 10,
    maxPollMs: 2_000,
  });
  onReady(tracker.track, tracker.tasks);
  return React.createElement(TimelineClipTaskStatusLine, {
    kind: "storyboard",
    task: tracker.tasks.storyboard,
    currentClipId: "clip-1",
  });
}

describe("timeline clip generation task tracker", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
  });

  it("polls a queued task to completion and triggers refresh", async () => {
    const statuses = ["processing", "processing", "completed"];
    globalThis.fetch = (async (url: RequestInfo | URL) => {
      assert.equal(String(url), "/api/v1/tasks/88");
      const status = statuses.shift() ?? "completed";
      return new Response(
        JSON.stringify({ id: 88, status, title: "storyboard" }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const completed: Array<{ kind: string; taskId: number }> = [];
    const notices: Array<{ message: string; variant: string }> = [];
    let trackFn:
      | ((kind: any, taskId: number, clipId: string | null) => void)
      | null = null;

    const utils = render(
      React.createElement(TrackerHarness, {
        onCompleted: (kind: string, taskId: number) =>
          completed.push({ kind, taskId }),
        onNotify: (message: string, variant: string) =>
          notices.push({ message, variant }),
        onReady: (track) => {
          trackFn = track;
        },
      }),
      { container: dom.window.document.body },
    );

    assert.ok(trackFn);
    trackFn!("storyboard", 88, "clip-1");

    await waitFor(() =>
      assert.ok(utils.getByText(/故事板参考图生成中（任务 #88）/)),
    );
    await waitFor(
      () => assert.ok(utils.getByText(/故事板参考图已生成完成（任务 #88）/)),
      { timeout: 3000 },
    );
    assert.deepEqual(completed, [{ kind: "storyboard", taskId: 88 }]);
    assert.ok(
      notices.some(
        (notice) =>
          notice.variant === "success" &&
          notice.message.includes("故事板参考图已生成完成"),
      ),
    );
  });

  it("surfaces task failure with the backend error message", async () => {
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          id: 99,
          status: "failed",
          error_message: "provider quota exceeded",
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      )) as typeof fetch;

    const completed: unknown[] = [];
    let trackFn:
      | ((kind: any, taskId: number, clipId: string | null) => void)
      | null = null;

    const utils = render(
      React.createElement(TrackerHarness, {
        onCompleted: (kind: string, taskId: number) =>
          completed.push({ kind, taskId }),
        onReady: (track) => {
          trackFn = track;
        },
      }),
      { container: dom.window.document.body },
    );

    trackFn!("storyboard", 99, "clip-1");

    await waitFor(() => assert.ok(utils.getByText(/provider quota exceeded/)), {
      timeout: 3000,
    });
    assert.equal(completed.length, 0);
  });

  it("hides status lines that belong to another clip", () => {
    const utils = render(
      React.createElement(TimelineClipTaskStatusLine, {
        kind: "video",
        task: {
          taskId: 7,
          clipId: "clip-other",
          phase: "processing",
          error: null,
        },
        currentClipId: "clip-1",
      }),
      { container: dom.window.document.body },
    );
    assert.equal(utils.queryByRole("status"), null);
  });
});
