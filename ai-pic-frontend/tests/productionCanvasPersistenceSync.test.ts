import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  mergeConfirmedCanvasState,
  productionCanvasStateSignature,
} from "../src/components/features/canvas/productionCanvasPersistenceSync";
import type { ProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

const localState: ProductionCanvasState = {
  edges: [],
  nodes: [
    {
      id: "video",
      label: "Video Candidates",
      title: "本地任务状态",
      status: "running",
      width: 220,
      x: 0,
      y: 0,
      outputs: { task_id: 6292, task_status: "completed" },
    },
  ],
  selectedNodeId: "video",
  viewport: { x: 0, y: 0, zoom: 1 },
};

describe("production canvas persistence sync", () => {
  it("signs the local state acknowledged by server status patches", () => {
    const serverState: ProductionCanvasState = {
      ...localState,
      nodes: [
        {
          ...localState.nodes[0],
          title: "服务端规范化标题",
          status: "review",
          executionInputFingerprint: "a".repeat(64),
        },
      ],
    };

    const acknowledged = mergeConfirmedCanvasState(localState, serverState);
    assert.equal(acknowledged.nodes[0].title, "本地任务状态");
    assert.equal(acknowledged.nodes[0].status, "review");
    assert.equal(
      acknowledged.nodes[0].executionInputFingerprint,
      "a".repeat(64),
    );
    assert.equal(
      productionCanvasStateSignature("run-1", acknowledged),
      productionCanvasStateSignature("run-1", {
        ...localState,
        nodes: [acknowledged.nodes[0]],
      }),
    );
  });
});
