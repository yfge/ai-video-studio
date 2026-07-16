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
      outputs: {
        virtual_ip_id: 84,
        environment_id: 13,
        story_id: 60,
        episode_id: 170,
        script_id: 140,
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "old-clip",
        task_id: 6292,
        task_status: "completed",
      },
    },
  ],
  selectedNodeId: "video",
  viewport: { x: 0, y: 0, zoom: 1 },
};

describe("production canvas persistence sync", () => {
  it("signs the local state acknowledged by server status patches", () => {
    const serverState: ProductionCanvasState = {
      ...localState,
      resolvedContextRevision: 7,
      nodes: [
        {
          ...localState.nodes[0],
          title: "服务端规范化标题",
          status: "review",
          definitionVersion: 3,
          executionInputFingerprint: "a".repeat(64),
          selectedOutputId: 42,
          selectedOutputUrl: "https://example.com/approved.png",
          selectedOutputReviewedBy: 7,
          selectedOutputReviewedAt: "2026-07-11T12:00:00Z",
          outputs: {
            approved_image: "https://example.com/approved.png",
            virtual_ip_id: 85,
            environment_id: 14,
            story_id: 61,
            episode_id: 175,
            script_id: 301,
            timeline_id: 502,
            timeline_version: 1,
            task_id: 6300,
            model: "server-ignored-model",
          },
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
    assert.equal(acknowledged.nodes[0].definitionVersion, 3);
    assert.equal(acknowledged.nodes[0].selectedOutputId, 42);
    assert.equal(acknowledged.nodes[0].selectedOutputReviewedBy, 7);
    assert.equal(acknowledged.resolvedContextRevision, 7);
    assert.deepEqual(acknowledged.nodes[0].outputs, {
      approved_image: "https://example.com/approved.png",
      virtual_ip_id: 85,
      environment_id: 14,
      story_id: 61,
      episode_id: 175,
      script_id: 301,
      timeline_id: 502,
      timeline_version: 1,
      task_id: 6300,
    });
    assert.equal(
      productionCanvasStateSignature("run-1", acknowledged),
      productionCanvasStateSignature("run-1", {
        ...localState,
        resolvedContextRevision: 7,
        nodes: [acknowledged.nodes[0]],
      }),
    );
  });
});
