import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import { virtualizedProductionCanvasNodes } from "../src/components/features/canvas/productionCanvasVirtualization";

function scaleNodes(count: number): ProductionCanvasNode[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `scale-${index}`,
    label: `Node ${index}`,
    title: `Scale node ${index}`,
    status: "ready",
    x: (index % 25) * 260,
    y: Math.floor(index / 25) * 160,
    width: 220,
  }));
}

describe("production canvas viewport virtualization", () => {
  it("keeps a 500-node fixture within the heavy-card render budget", () => {
    const nodes = scaleNodes(500);
    const rendered = virtualizedProductionCanvasNodes(
      nodes,
      { x: 0, y: 0, zoom: 1 },
      { width: 1180, height: 520 },
    );

    assert.ok(rendered.length <= 60, `rendered ${rendered.length} heavy cards`);
    assert.ok(rendered.some((node) => node.id === "scale-0"));
    assert.equal(
      rendered.some((node) => node.id === "scale-499"),
      false,
    );
  });

  it("always retains selected or executing nodes outside the viewport", () => {
    const nodes = scaleNodes(500);
    const rendered = virtualizedProductionCanvasNodes(
      nodes,
      { x: 0, y: 0, zoom: 1 },
      { width: 1180, height: 520 },
      new Set(["scale-499"]),
    );

    assert.ok(rendered.some((node) => node.id === "scale-499"));
  });

  it("does not virtualize small canvases", () => {
    const nodes = scaleNodes(80);
    assert.equal(
      virtualizedProductionCanvasNodes(
        nodes,
        { x: -10000, y: -10000, zoom: 1 },
        { width: 1180, height: 520 },
      ),
      nodes,
    );
  });
});
