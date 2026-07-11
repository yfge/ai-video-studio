import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  captureProductionCanvasDefinition,
  restoreProductionCanvasDefinition,
} from "../src/components/features/canvas/productionCanvasDefinition";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

describe("production canvas definition history", () => {
  it("restores graph configuration without rolling back execution evidence", () => {
    const initial = createProductionCanvasState();
    initial.nodes[0] = {
      ...initial.nodes[0],
      outputs: { model: "original" },
    };
    const snapshot = captureProductionCanvasDefinition(initial);
    const current = {
      ...initial,
      viewport: { x: 120, y: 80, zoom: 0.8 },
      nodes: [
        {
          ...initial.nodes[0],
          x: 420,
          status: "approved" as const,
          outputs: { model: "current", task_id: 77 },
          selectedOutputId: 9,
        },
        ...initial.nodes.slice(1),
        {
          id: "task-77",
          label: "Task",
          title: "执行证据",
          status: "running" as const,
          x: 420,
          y: 420,
          width: 180,
          kind: "skill_result" as const,
          outputs: { task_id: 77 },
        },
      ],
      edges: [...initial.edges, { from: "brief", to: "task-77" }],
    };

    const restored = restoreProductionCanvasDefinition(current, snapshot);
    const brief = restored.nodes.find((node) => node.id === "brief");
    assert.equal(brief?.x, initial.nodes[0].x);
    assert.equal(brief?.status, "approved");
    assert.deepEqual(brief?.outputs, { task_id: 77, model: "original" });
    assert.equal(brief?.selectedOutputId, 9);
    assert.ok(restored.nodes.some((node) => node.id === "task-77"));
    assert.ok(restored.edges.some((edge) => edge.to === "task-77"));
    assert.deepEqual(restored.viewport, current.viewport);
  });
});
