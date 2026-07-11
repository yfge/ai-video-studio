import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  MINIMAP_HEIGHT,
  MINIMAP_WIDTH,
  productionCanvasMinimapNodeRect,
  productionCanvasMinimapViewportRect,
  productionCanvasWorldPointFromMinimap,
} from "../src/components/features/canvas/productionCanvasMinimapModel";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const bounds = { minX: -100, minY: -50, width: 1200, height: 600 };
const node: ProductionCanvasNode = {
  id: "scene-1",
  label: "Scene 1",
  title: "开场",
  status: "ready",
  x: 0,
  y: 50,
  width: 200,
};

describe("production canvas minimap", () => {
  it("maps nodes and the viewport into the minimap", () => {
    const nodeRect = productionCanvasMinimapNodeRect(node, bounds);
    const viewportRect = productionCanvasMinimapViewportRect(
      { x: 100, y: 50, zoom: 1 },
      bounds,
      { width: 600, height: 300 },
    );

    assert.ok(nodeRect.left >= 0 && nodeRect.left < MINIMAP_WIDTH);
    assert.ok(nodeRect.top >= 0 && nodeRect.top < MINIMAP_HEIGHT);
    assert.ok(viewportRect.width > nodeRect.width);
    assert.ok(viewportRect.height > nodeRect.height);
  });

  it("maps minimap clicks back into clamped world coordinates", () => {
    const center = productionCanvasWorldPointFromMinimap(
      { x: MINIMAP_WIDTH / 2, y: MINIMAP_HEIGHT / 2 },
      bounds,
    );
    const outside = productionCanvasWorldPointFromMinimap(
      { x: -100, y: 500 },
      bounds,
    );

    assert.deepEqual(center, { x: 500, y: 250 });
    assert.deepEqual(outside, { x: -100, y: 550 });
  });
});
