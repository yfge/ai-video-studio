import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  useGenerationTaskTracker,
  type TrackedGenerationTask,
} from "../src/hooks/useGenerationTaskTracker";
import type { Task } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;

type Kind = "script" | "episodes";

function Harness({
  onCompleted,
  onNotify,
  onReady,
}: {
  onCompleted?: (kind: Kind, taskId: number, task: Task | null) => void;
  onNotify?: (message: string, variant: string) => void;
  onReady: (
    track: (kind: Kind, taskId: number, contextId?: string | null) => void,
    tasks: Partial<Record<Kind, TrackedGenerationTask>>,
  ) => void;
}) {
  const tracker = useGenerationTaskTracker<Kind>({
    labels: { script: "剧本", episodes: "剧集" },
    onCompleted,
    onNotify,
    pollIntervalMs: 10,
    maxPollMs: 2_000,
  });
  onReady(tracker.track, tracker.tasks);
  return null;
}

function taskResponse(payload: Record<string, unknown>) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

describe("generation task tracker", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
  });

  it("completes a task and passes the final task payload to onCompleted", async () => {
    const statuses = ["processing", "completed"];
    globalThis.fetch = (async (url: RequestInfo | URL) => {
      assert.equal(String(url), "/api/v1/tasks/55");
      const status = statuses.shift() ?? "completed";
      return taskResponse({
        id: 55,
        status,
        result_file_path: "script:321",
      });
    }) as typeof fetch;

    const completed: Array<{ kind: Kind; taskId: number; task: Task | null }> =
      [];
    const notices: Array<{ message: string; variant: string }> = [];
    let trackFn:
      | ((kind: Kind, taskId: number, contextId?: string | null) => void)
      | null = null;

    render(
      React.createElement(Harness, {
        onCompleted: (kind: Kind, taskId: number, task: Task | null) =>
          completed.push({ kind, taskId, task }),
        onNotify: (message: string, variant: string) =>
          notices.push({ message, variant }),
        onReady: (track) => {
          trackFn = track;
        },
      }),
      { container: dom.window.document.body },
    );

    trackFn!("script", 55, "episode-9");

    await waitFor(() => assert.equal(completed.length, 1), { timeout: 3000 });
    assert.equal(completed[0].kind, "script");
    assert.equal(completed[0].taskId, 55);
    assert.equal(completed[0].task?.result_file_path, "script:321");
    assert.ok(
      notices.some(
        (notice) =>
          notice.variant === "success" &&
          notice.message.includes("剧本已生成完成"),
      ),
    );
  });

  it("tracks two kinds independently", async () => {
    globalThis.fetch = (async (url: RequestInfo | URL) => {
      const id = String(url).split("/").pop();
      return taskResponse({
        id: Number(id),
        status: id === "1" ? "completed" : "failed",
        error_message: id === "2" ? "quota exceeded" : undefined,
      });
    }) as typeof fetch;

    const completed: Kind[] = [];
    const notices: string[] = [];
    let trackFn:
      | ((kind: Kind, taskId: number, contextId?: string | null) => void)
      | null = null;
    let latestTasks: Partial<Record<Kind, TrackedGenerationTask>> = {};

    render(
      React.createElement(Harness, {
        onCompleted: (kind: Kind) => completed.push(kind),
        onNotify: (message: string) => notices.push(message),
        onReady: (track, tasks) => {
          trackFn = track;
          latestTasks = tasks;
        },
      }),
      { container: dom.window.document.body },
    );

    trackFn!("script", 1);
    trackFn!("episodes", 2);

    await waitFor(
      () => {
        assert.equal(latestTasks.script?.phase, "completed");
        assert.equal(latestTasks.episodes?.phase, "failed");
      },
      { timeout: 3000 },
    );
    assert.deepEqual(completed, ["script"]);
    assert.ok(notices.some((message) => message.includes("quota exceeded")));
    assert.equal(latestTasks.episodes?.error, "quota exceeded");
  });

  it("times out when the task never reaches a terminal state", async () => {
    globalThis.fetch = (async () =>
      taskResponse({ id: 9, status: "processing" })) as typeof fetch;

    const notices: string[] = [];
    let trackFn:
      | ((kind: Kind, taskId: number, contextId?: string | null) => void)
      | null = null;
    let latestTasks: Partial<Record<Kind, TrackedGenerationTask>> = {};

    function ShortHarness({
      onReady,
    }: {
      onReady: (
        track: (kind: Kind, taskId: number) => void,
        tasks: Partial<Record<Kind, TrackedGenerationTask>>,
      ) => void;
    }) {
      const tracker = useGenerationTaskTracker<Kind>({
        labels: (kind) => (kind === "script" ? "剧本" : "剧集"),
        onNotify: (message: string) => notices.push(message),
        pollIntervalMs: 10,
        maxPollMs: 50,
      });
      onReady(tracker.track, tracker.tasks);
      return null;
    }

    render(
      React.createElement(ShortHarness, {
        onReady: (track, tasks) => {
          trackFn = track;
          latestTasks = tasks;
        },
      }),
      { container: dom.window.document.body },
    );

    trackFn!("script", 9);

    await waitFor(() => assert.equal(latestTasks.script?.phase, "timeout"), {
      timeout: 3000,
    });
    assert.ok(notices.some((message) => message.includes("等待超时")));
  });

  it("replaces a tracked task of the same kind", async () => {
    globalThis.fetch = (async (url: RequestInfo | URL) => {
      const id = String(url).split("/").pop();
      return taskResponse({
        id: Number(id),
        status: id === "11" ? "processing" : "completed",
      });
    }) as typeof fetch;

    const completed: number[] = [];
    let trackFn:
      | ((kind: Kind, taskId: number, contextId?: string | null) => void)
      | null = null;

    render(
      React.createElement(Harness, {
        onCompleted: (_kind: Kind, taskId: number) => completed.push(taskId),
        onReady: (track) => {
          trackFn = track;
        },
      }),
      { container: dom.window.document.body },
    );

    trackFn!("script", 11);
    trackFn!("script", 12);

    await waitFor(() => assert.deepEqual(completed, [12]), { timeout: 3000 });
  });
});
