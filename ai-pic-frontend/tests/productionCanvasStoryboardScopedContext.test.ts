import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import {
  isScopedProductionCanvasMediaNode,
  productionCanvasSharedContextForNode,
} from "../src/components/features/canvas/productionCanvasScopedContext";

describe("ProductionCanvas storyboard scoped context", () => {
  it("keeps clip storyboard and video lineage scoped without frame indexes", () => {
    for (const skill of ["storyboard.candidates", "video.candidates"]) {
      const node: ProductionCanvasNode = {
        id: skill,
        label: skill,
        title: skill,
        status: "ready",
        x: 0,
        y: 0,
        width: 220,
        skill,
        outputs: {
          timeline_id: 501,
          timeline_version: 7,
          clip_id: "clip-a",
          ...(skill === "video.candidates"
            ? { placement_mode: "explicit_node" }
            : {}),
        },
      };

      assert.equal(isScopedProductionCanvasMediaNode(node), true);
      assert.equal(
        productionCanvasSharedContextForNode(node, { timeline_id: 502 }),
        undefined,
      );
    }
  });
});
