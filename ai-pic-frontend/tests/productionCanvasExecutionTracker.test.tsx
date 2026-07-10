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
});
