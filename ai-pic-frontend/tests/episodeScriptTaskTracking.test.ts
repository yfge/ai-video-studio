import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  resolveScriptIdFromTask,
  useEpisodeWorkspaceScriptTaskTracking,
} from "../src/hooks/episode/useEpisodeWorkspaceScriptTaskTracking";
import type { Script, Task } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

function script(id: number, createdAt: string): Script {
  return {
    id,
    business_id: `script_${id}`,
    episode_id: 9,
    title: `剧本 ${id}`,
    version: "1.0",
    created_at: createdAt,
    updated_at: createdAt,
  } as unknown as Script;
}

function Harness({
  onReady,
  setScripts,
  onSelectScript,
}: {
  onReady: (track: (taskId: number) => void) => void;
  setScripts: React.Dispatch<React.SetStateAction<Script[]>>;
  onSelectScript: (scriptId: number | null) => void;
}) {
  const tracking = useEpisodeWorkspaceScriptTaskTracking({
    episodeKey: "ep-key-1",
    knownScriptIds: [100],
    setScripts,
    onSelectScript,
    pollIntervalMs: 10,
  });
  onReady(tracking.trackScriptTask);
  return null;
}

describe("episode script task tracking", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
  });

  it("parses script ids from task result paths", () => {
    assert.equal(
      resolveScriptIdFromTask({ result_file_path: "script:321" } as Task),
      321,
    );
    assert.equal(
      resolveScriptIdFromTask({ result_file_path: "script:abc" } as Task),
      null,
    );
    assert.equal(resolveScriptIdFromTask(null), null);
  });

  it("reloads scripts and selects the task's script on completion", async () => {
    globalThis.fetch = (async (url: RequestInfo | URL) => {
      const path = String(url);
      if (path.includes("/api/v1/tasks/77")) {
        return jsonResponse({
          id: 77,
          status: "completed",
          result_file_path: "script:200",
        });
      }
      if (path.includes("/scripts/episode/")) {
        return jsonResponse([
          script(200, "2026-06-10T10:00:00Z"),
          script(100, "2026-06-09T10:00:00Z"),
        ]);
      }
      return jsonResponse({});
    }) as typeof fetch;

    const selected: Array<number | null> = [];
    let scriptsState: Script[] = [];
    let trackFn: ((taskId: number) => void) | null = null;

    render(
      React.createElement(Harness, {
        onReady: (track) => {
          trackFn = track;
        },
        setScripts: ((next: Script[] | ((prev: Script[]) => Script[])) => {
          scriptsState = typeof next === "function" ? next(scriptsState) : next;
        }) as React.Dispatch<React.SetStateAction<Script[]>>,
        onSelectScript: (scriptId: number | null) => selected.push(scriptId),
      }),
      { container: dom.window.document.body },
    );

    trackFn!(77);

    await waitFor(() => assert.deepEqual(selected, [200]), { timeout: 3000 });
    assert.equal(scriptsState.length, 2);
    assert.equal(scriptsState[0].id, 200);
  });
});
