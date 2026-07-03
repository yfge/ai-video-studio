import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  addProductionCanvasNote,
  createProductionCanvasState,
  moveProductionCanvasNode,
  zoomProductionCanvas,
} from "../src/components/features/canvas/productionCanvasState";
import {
  centerProductionCanvasOnNode,
  displayProductionCanvasNodeTitle,
  getWorldBounds,
} from "../src/components/features/canvas/productionCanvasViewModel";

describe("productionCanvasState", () => {
  it("dedupes restored canvas nodes by id", () => {
    const state = createProductionCanvasState();
    const restored = createProductionCanvasState([
      state.nodes[0]!,
      { ...state.nodes[0]!, title: "Duplicate brief" },
      state.nodes[1]!,
    ]);

    assert.deepEqual(
      restored.nodes.map((node) => node.id),
      [state.nodes[0]!.id, state.nodes[1]!.id],
    );
    assert.equal(restored.nodes[0]?.title, state.nodes[0]?.title);
  });

  it("normalizes restored canvas node dimensions", () => {
    const state = createProductionCanvasState();
    const restored = createProductionCanvasState([
      { ...state.nodes[0]!, width: 0, height: -12 },
    ]);

    assert.equal(restored.nodes[0]?.width, 190);
    assert.equal(restored.nodes[0]?.height, undefined);
    assert.equal(
      displayProductionCanvasNodeTitle({
        ...state.nodes[0]!,
        kind: "note",
        title: " ",
      }),
      "未命名便签",
    );
  });

  it("updates reusable canvas state for drag, zoom, and notes", () => {
    const state = createProductionCanvasState();
    const defaultTimeline = state.nodes.find((node) => node.id === "timeline");
    const movedNodes = moveProductionCanvasNode(state.nodes, "script", 24, -12);
    const movedScript = movedNodes.find((node) => node.id === "script");
    const report = state.nodes.find((node) => node.id === "report");

    assert.equal(defaultTimeline?.status, "blocked");
    assert.equal(movedScript?.x, 294);
    assert.equal(movedScript?.y, 52);
    assert.deepEqual(
      createProductionCanvasState(state.nodes, [
        { from: "brief", to: "script" },
        { from: "brief", to: "script" },
        { from: "brief", to: "brief" },
        { from: "brief", to: "missing-node" },
      ]).edges,
      [{ from: "brief", to: "script" }],
    );

    assert.equal(zoomProductionCanvas(state.viewport, 10).zoom, 1.6);
    assert.equal(zoomProductionCanvas(state.viewport, -10).zoom, 0.5);
    assert.deepEqual(
      zoomProductionCanvas(
        { x: Number.NaN, y: Number.POSITIVE_INFINITY, zoom: Number.NaN },
        1,
      ),
      { x: 0, y: 0, zoom: 1.1 },
    );

    const withNote = addProductionCanvasNote(state.nodes, 1);
    const note = withNote.find((node) => node.id === "note-1");
    const safeNote = addProductionCanvasNote(state.nodes, 1, {
      x: Number.NaN,
      y: Number.POSITIVE_INFINITY,
    }).find((node) => node.id === "note-1");

    assert.equal(note?.kind, "note");
    assert.equal(note?.label, "便签");
    assert.equal(safeNote?.x, 160);
    assert.equal(safeNote?.y, 340);
    assert.deepEqual(
      getWorldBounds([
        {
          ...state.nodes[0]!,
          height: Number.NaN,
          width: Number.NaN,
          x: Number.NaN,
          y: Number.NaN,
        },
      ]),
      { minX: 0, minY: 0, width: 1260, height: 600 },
    );
    assert.deepEqual(
      getWorldBounds([
        {
          ...state.nodes[0]!,
          height: -30,
          width: -100,
          x: 1200,
          y: 500,
        },
      ]),
      { minX: 0, minY: 0, width: 1470, height: 666 },
    );

    assert.ok(report);
    assert.deepEqual(
      centerProductionCanvasOnNode(state.viewport, report, {
        width: 1180,
        height: 520,
      }),
      { x: -495, y: -43, zoom: 1 },
    );
    assert.deepEqual(
      centerProductionCanvasOnNode({ x: 0, y: 0, zoom: 0 }, report, {
        width: 1180,
        height: 520,
      }),
      { x: 48, y: 109, zoom: 0.5 },
    );
  });
});
