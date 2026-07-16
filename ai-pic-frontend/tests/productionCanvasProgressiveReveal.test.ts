import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import {
  initialProductionCanvasRevealedNodeIds,
  productionCanvasExecutionRevealedNodeIds,
} from "../src/components/features/canvas/productionCanvasProgressiveReveal";

const node = (
  id: string,
  status: ProductionCanvasNode["status"] = "ready",
): ProductionCanvasNode => ({
  id,
  label: id,
  title: id,
  status,
  x: 0,
  y: 0,
  width: 220,
  skill: `${id}.skill`,
});

describe("productionCanvasProgressiveReveal", () => {
  const edges = [
    { from: "brief", to: "asset" },
    { from: "asset", to: "script" },
  ];

  it("starts from graph roots instead of painting the whole plan", () => {
    assert.deepEqual(
      [
        ...initialProductionCanvasRevealedNodeIds(
          [node("brief"), node("asset"), node("script")],
          edges,
        ),
      ],
      ["brief", "asset"],
    );
  });

  it("reveals task evidence immediately and downstream nodes after settlement", () => {
    const active = productionCanvasExecutionRevealedNodeIds(
      [
        {
          ...node("brief", "running"),
          outputs: { task_status: "processing" },
        },
        {
          ...node("brief-task", "running"),
          kind: "note",
          outputs: { task_id: 9, task_status: "processing" },
        },
      ],
      edges,
    );
    assert.deepEqual([...active], ["brief", "brief-task"]);

    const settled = productionCanvasExecutionRevealedNodeIds(
      [node("brief", "review")],
      edges,
    );
    assert.deepEqual([...settled], ["brief", "asset"]);
  });
});
