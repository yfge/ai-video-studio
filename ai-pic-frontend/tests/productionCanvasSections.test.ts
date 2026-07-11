import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { selectProductionCanvasNode } from "../src/components/features/canvas/productionCanvasSelection";
import {
  collapsedProductionCanvasNodeIds,
  createProductionCanvasSection,
  toggleProductionCanvasSection,
} from "../src/components/features/canvas/productionCanvasSections";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

describe("production canvas sections", () => {
  it("creates and collapses a section around selected nodes", () => {
    let state = createProductionCanvasState();
    state = selectProductionCanvasNode(state, "brief");
    state = selectProductionCanvasNode(state, "script", true);
    state = createProductionCanvasSection(state, "scene");
    const section = state.sections?.[0];

    assert.equal(section?.id, "scene-section-1");
    assert.deepEqual(section?.nodeIds, ["brief", "script"]);
    assert.ok((section?.width || 0) > 400);
    state = toggleProductionCanvasSection(state, "scene-section-1");
    assert.deepEqual([...collapsedProductionCanvasNodeIds(state)].sort(), [
      "brief",
      "script",
    ]);
  });
});
