import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { useProductionCanvasExecutionTracker } from "../src/components/features/canvas/useProductionCanvasExecutionTracker";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const sourceNode: ProductionCanvasNode = {
  id: "skill-environment-image",
  label: "Environment Image",
  title: "Queue environment image",
  status: "ready",
  x: 0,
  y: 0,
  width: 220,
};
const runningSkillNode: ProductionCanvasNode = {
  ...sourceNode,
  status: "running",
  outputs: { dispatched_task_id: 101, task_status: "pending" },
};
const taskNode: ProductionCanvasNode = {
  id: "skill-environment-image-task-101",
  kind: "note",
  label: "Task #101",
  title: "Environment task",
  status: "running",
  x: 0,
  y: 120,
  width: 220,
  outputs: { source_node_id: sourceNode.id, task_id: 101 },
};

const renderSkillNode: ProductionCanvasNode = {
  ...sourceNode,
  id: "skill-timeline-render",
  skill: "timeline.render",
  status: "running",
  outputs: {
    timeline_id: 71,
    render_job_id: 122,
    render_status: "queued",
  },
};
const renderNode: ProductionCanvasNode = {
  ...taskNode,
  id: "skill-timeline-render-render-122",
  label: "Render #122",
  outputs: {
    source_node_id: renderSkillNode.id,
    timeline_id: 71,
    render_job_id: 122,
    render_status: "queued",
  },
};

describe("useProductionCanvasExecutionTracker", () => {
  afterEach(() => cleanup());

  it("polls a dispatched task and updates both canvas nodes with its artifact", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    globalThis.fetch = async (input) => {
      assert.equal(String(input), "/api/v1/tasks/101");
      return new Response(
        JSON.stringify({
          id: 101,
          business_id: "task-101",
          title: "环境图已完成",
          status: "completed",
          result_file_path: "environment_images:13:1",
          created_at: "2026-07-10T10:00:00Z",
          user_id: 1,
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
      });
      return (
        <button
          type="button"
          onClick={() => publish(sourceNode, [runningSkillNode, taskNode])}
        >
          publish
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish" }).click();

      await waitFor(() => assert.equal(updates.length, 2));
      assert.equal(updates[1][0].status, "review");
      assert.equal(updates[1][1].outputs?.task_status, "completed");
      assert.equal(
        updates[1][0].outputs?.result_file_path,
        "environment_images:13:1",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("polls a RenderJob until the final video link is ready", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    let requestCount = 0;
    globalThis.fetch = async (input) => {
      assert.equal(String(input), "/api/v1/timelines/71/render-jobs");
      requestCount += 1;
      const succeeded = requestCount > 1;
      return new Response(
        JSON.stringify({
          items: [
            {
              id: 122,
              business_id: "render-122",
              timeline_id: 71,
              timeline_version: 6,
              render_type: "final",
              preset_hash: "preset",
              preset: { fps: 24 },
              status: succeeded ? "succeeded" : "running",
              progress: succeeded ? 100 : 50,
              output_asset_id: succeeded ? 375 : null,
              output_asset: succeeded
                ? {
                    id: 375,
                    business_id: "asset-375",
                    asset_type: "video",
                    origin: "timeline_render",
                    file_url: "/media/final.mp4",
                    created_at: "2026-07-10T10:00:00Z",
                    updated_at: "2026-07-10T10:00:00Z",
                  }
                : null,
              created_at: "2026-07-10T10:00:00Z",
              updated_at: "2026-07-10T10:00:01Z",
            },
          ],
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
      });
      return (
        <button
          type="button"
          onClick={() =>
            publish(renderSkillNode, [renderSkillNode, renderNode])
          }
        >
          publish render
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish render" }).click();

      await waitFor(() => assert.equal(updates.length, 3));
      assert.equal(updates[1][0].outputs?.render_progress, 50);
      assert.equal(updates[2][0].status, "ready");
      assert.equal(updates[2][1].outputs?.render_status, "succeeded");
      assert.equal(updates[2][0].actionHref, "/media/final.mp4");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("resumes an active RenderJob from restored run state", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const requests: string[] = [];
    globalThis.fetch = async (input) => {
      const url = String(input);
      requests.push(url);
      if (url === "/api/v1/production-canvas/runs/canvas-run-active") {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              prompt: "restore active render",
              run_id: "canvas-run-active",
              task_id: 900,
              skill_manifest: { version: "production_canvas.v1" },
              selected_assets: { virtual_ips: [], environments: [] },
              nodes: [],
              saved_state: {
                nodes: [
                  {
                    ...renderSkillNode,
                    outputs: {
                      ...renderSkillNode.outputs,
                      canvas_run_id: "canvas-run-active",
                    },
                  },
                  {
                    ...renderNode,
                    outputs: {
                      ...renderNode.outputs,
                      canvas_run_id: "canvas-run-active",
                    },
                  },
                ],
                edges: [],
                viewport: { x: 0, y: 0, zoom: 1 },
                selected_node_id: renderSkillNode.id,
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      assert.equal(url, "/api/v1/timelines/71/render-jobs");
      return new Response(
        JSON.stringify({
          items: [
            {
              id: 122,
              business_id: "render-122",
              timeline_id: 71,
              timeline_version: 6,
              render_type: "final",
              preset_hash: "preset",
              preset: { fps: 24 },
              status: "succeeded",
              progress: 100,
              output_asset_id: 375,
              output_asset: {
                id: 375,
                business_id: "asset-375",
                asset_type: "video",
                origin: "timeline_render",
                file_url: "/media/restored-final.mp4",
                created_at: "2026-07-10T10:00:00Z",
                updated_at: "2026-07-10T10:00:00Z",
              },
              created_at: "2026-07-10T10:00:00Z",
              updated_at: "2026-07-10T10:00:01Z",
            },
          ],
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
        runId: "canvas-run-active",
      });
      return null;
    }

    try {
      render(<Harness />, { container: dom.window.document.body });

      await waitFor(() => assert.equal(updates.length, 1));
      assert.deepEqual(requests, [
        "/api/v1/production-canvas/runs/canvas-run-active",
        "/api/v1/timelines/71/render-jobs",
      ]);
      assert.equal(updates[0][0].status, "ready");
      assert.equal(updates[0][1].outputs?.render_status, "succeeded");
      assert.equal(updates[0][0].actionHref, "/media/restored-final.mp4");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
