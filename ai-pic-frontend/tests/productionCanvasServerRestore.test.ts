import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasStateFromRun } from "../src/components/features/canvas/productionCanvasPersistence";

describe("productionCanvasStateFromRun", () => {
  it("sanitizes server plan nodes", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run",
      task_id: 1,
      nodes: [
        {
          id: "brief",
          label: "Brief",
          title: "Brief",
          status: "review",
          x: Number.NaN,
          y: Number.POSITIVE_INFINITY,
          width: Number.NaN,
          height: Number.NaN,
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
    } as any);

    assert.equal(restored.nodes[0]?.x, 0);
    assert.equal(restored.nodes[0]?.y, 0);
    assert.equal(restored.nodes[0]?.width, 220);
    assert.equal(restored.nodes[0]?.height, 118);
  });

  it("sanitizes saved server canvas state", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run",
      task_id: 1,
      nodes: [],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [
          { from: "brief", to: "script" },
          { from: "brief", to: "script" },
          { from: "brief", to: "brief" },
          { from: "brief", to: "missing" },
        ],
        nodes: [
          {
            id: "brief",
            label: "Brief",
            title: "Brief",
            status: "review",
            x: Number.NaN,
            y: Number.POSITIVE_INFINITY,
            width: 0,
            height: -1,
          },
          {
            id: "brief",
            label: "Brief duplicate",
            title: "Duplicate",
            status: "review",
            x: 10,
            y: 10,
            width: 220,
          },
          {
            id: "script",
            label: "Script",
            title: "Script",
            status: "review",
            x: 300,
            y: 0,
            width: 220,
          },
        ],
        selected_node_id: "missing",
        viewport: { x: Number.NaN, y: Number.POSITIVE_INFINITY, zoom: 0 },
      },
    } as any);

    assert.deepEqual(
      restored.nodes.map((node) => node.id),
      ["brief", "script"],
    );
    assert.equal(restored.nodes[0]?.x, 0);
    assert.equal(restored.nodes[0]?.y, 0);
    assert.equal(restored.nodes[0]?.width, 190);
    assert.equal(restored.nodes[0]?.height, undefined);
    assert.deepEqual(restored.edges, [{ from: "brief", to: "script" }]);
    assert.deepEqual(restored.viewport, { x: 0, y: 0, zoom: 0.5 });
    assert.equal(restored.selectedNodeId, "brief");
  });
});
