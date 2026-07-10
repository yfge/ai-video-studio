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

const runId = "canvas-run-active";
const renderSkillNode = {
  id: "skill-timeline-render",
  label: "Render Skill",
  title: "已提交最终渲染任务",
  status: "running",
  x: 100,
  y: 100,
  width: 240,
  kind: "skill_result",
  skill: "timeline.render",
  outputs: {
    canvas_run_id: runId,
    timeline_id: 71,
    render_job_id: 122,
    render_status: "queued",
  },
} satisfies ProductionCanvasNode;
const renderEvidenceNode = {
  ...renderSkillNode,
  id: "skill-timeline-render-render-122",
  label: "Render #122",
  kind: "note",
  outputs: {
    ...renderSkillNode.outputs,
    source_node_id: renderSkillNode.id,
  },
} satisfies ProductionCanvasNode;

function runResponse({
  savedActive,
  serverActive,
}: {
  savedActive: boolean;
  serverActive: boolean;
}) {
  const staleSavedNode = {
    ...renderSkillNode,
    status: "review",
    outputs: { canvas_run_id: runId, script_id: 130 },
  };
  return {
    prompt: "restore active render",
    run_id: runId,
    task_id: 900,
    skill_manifest: { version: "production_canvas.v1" },
    selected_assets: { virtual_ips: [], environments: [] },
    nodes: serverActive
      ? [
          {
            ...renderSkillNode,
            reuse_targets: [],
            action_href: "/stories",
          },
        ]
      : [],
    saved_state: {
      nodes: savedActive
        ? [renderSkillNode, renderEvidenceNode]
        : [staleSavedNode],
      edges: [],
      viewport: { x: 0, y: 0, zoom: 1 },
      selected_node_id: renderSkillNode.id,
    },
  };
}

function renderJobsResponse() {
  return {
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
  };
}

async function verifyResume(options: {
  savedActive: boolean;
  serverActive: boolean;
}) {
  const updates: ProductionCanvasNode[][] = [];
  const requests: string[] = [];
  globalThis.fetch = async (input) => {
    const url = String(input);
    requests.push(url);
    const data = url.includes("production-canvas/runs")
      ? { success: true, data: runResponse(options) }
      : renderJobsResponse();
    return new Response(JSON.stringify(data), {
      headers: { "content-type": "application/json" },
    });
  };

  function Harness() {
    useProductionCanvasExecutionTracker({
      onNodesCreated: (nodes) => updates.push(nodes),
      pollIntervalMs: 5,
      maxPollMs: 500,
      runId,
    });
    return null;
  }

  render(<Harness />, { container: dom.window.document.body });
  await waitFor(() => assert.equal(updates.length, 1));
  assert.deepEqual(requests, [
    `/api/v1/production-canvas/runs/${runId}`,
    "/api/v1/timelines/71/render-jobs",
  ]);
  assert.equal(updates[0][0].status, "ready");
  assert.equal(updates[0][1].outputs?.render_status, "succeeded");
  assert.equal(updates[0][0].actionHref, "/media/restored-final.mp4");
}

describe("restored production canvas RenderJob tracking", () => {
  const originalFetch = globalThis.fetch;
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
  });

  it("resumes active evidence saved by the browser", async () => {
    await verifyResume({ savedActive: true, serverActive: false });
  });

  it("resumes server-persisted execution before browser autosave", async () => {
    await verifyResume({ savedActive: false, serverActive: true });
  });
});
