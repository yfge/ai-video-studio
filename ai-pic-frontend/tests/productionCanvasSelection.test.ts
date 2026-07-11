import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  alignProductionCanvasSelection,
  duplicateProductionCanvasSelection,
  moveProductionCanvasNodes,
  selectProductionCanvasNode,
} from "../src/components/features/canvas/productionCanvasSelection";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

describe("production canvas selection", () => {
  it("selects, aligns, distributes, and moves several nodes", () => {
    let state = createProductionCanvasState();
    state = selectProductionCanvasNode(state, "brief");
    state = selectProductionCanvasNode(state, "script", true);
    state = selectProductionCanvasNode(state, "storyboard", true);
    state = alignProductionCanvasSelection(state, "left");
    assert.deepEqual(
      state.nodes
        .filter((node) => ["brief", "script", "storyboard"].includes(node.id))
        .map((node) => node.x),
      [40, 40, 40],
    );
    state = alignProductionCanvasSelection(state, "distribute-y");
    const selected = state.nodes
      .filter((node) => ["brief", "script", "storyboard"].includes(node.id))
      .sort((left, right) => left.y - right.y);
    assert.equal(
      selected[1]!.y - selected[0]!.y,
      selected[2]!.y - selected[1]!.y,
    );
    const scriptY = state.nodes.find((node) => node.id === "script")!.y;
    const moved = moveProductionCanvasNodes(
      state.nodes,
      ["brief", "script"],
      10,
      20,
    );
    assert.equal(moved.find((node) => node.id === "brief")?.x, 50);
    assert.equal(moved.find((node) => node.id === "script")?.y, scriptY + 20);
  });

  it("duplicates production configuration and internal edges without evidence", () => {
    let state = createProductionCanvasState();
    state = selectProductionCanvasNode(state, "brief");
    state = selectProductionCanvasNode(state, "script", true);
    state.nodes = state.nodes.map((node) =>
      node.id === "script"
        ? {
            ...node,
            outputs: { episode_id: 12, task_id: 88, video_duration: 5 },
            selectedOutputId: 9,
          }
        : node,
    );
    const duplicated = duplicateProductionCanvasSelection(state);
    const scriptCopy = duplicated.nodes.find(
      (node) => node.id === "script-copy-1",
    );

    assert.equal(duplicated.nodes.length, state.nodes.length + 2);
    assert.deepEqual(scriptCopy?.outputs, {
      episode_id: 12,
      video_duration: 5,
    });
    assert.equal(scriptCopy?.selectedOutputId, undefined);
    assert.equal(scriptCopy?.status, "draft");
    assert.ok(
      duplicated.edges.some(
        (edge) => edge.from === "brief-copy-1" && edge.to === "script-copy-1",
      ),
    );
  });
});
