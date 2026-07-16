import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import {
  isScopedProductionCanvasMediaNode,
  productionCanvasSharedContextForNode,
} from "../src/components/features/canvas/productionCanvasScopedContext";
import {
  applyProductionCanvasContext,
  collectProductionCanvasContext,
} from "../src/components/features/canvas/productionCanvasSharedContext";

describe("productionCanvasScopedContext", () => {
  it("does not let queued image evidence replace the global Timeline", () => {
    const global: ProductionCanvasNode = {
      id: "render",
      label: "Render",
      title: "Render",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "timeline.render",
      outputs: {
        script_id: 301,
        timeline_id: 502,
        timeline_version: 1,
        clip_id: "clip-global",
      },
    };
    const imageTask: ProductionCanvasNode = {
      id: "image-a-task-9",
      kind: "note",
      label: "Task #9",
      title: "Image",
      status: "review",
      x: 240,
      y: 0,
      width: 220,
      outputs: {
        source_node_id: "image-a",
        skill: "image.candidates",
        queued_frame_indexes: [0],
        task_id: 9,
        script_id: 140,
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "clip-b",
      },
    };

    assert.equal(isScopedProductionCanvasMediaNode(imageTask), true);
    assert.equal(
      productionCanvasSharedContextForNode(imageTask, {
        script_id: 140,
        timeline_id: 501,
      }),
      undefined,
    );
    assert.equal(
      productionCanvasSharedContextForNode(
        {
          ...imageTask,
          kind: undefined,
          skill: "image.candidates",
          outputs: {},
        },
        { script_id: 140 },
      ),
      undefined,
    );
    assert.deepEqual(collectProductionCanvasContext([global, imageTask]), {
      script_id: 301,
      timeline_id: 502,
      timeline_version: 1,
      clip_id: "clip-global",
    });
  });

  it("does not promote placed scoped video evidence into global context", () => {
    const video: ProductionCanvasNode = {
      id: "video-a",
      label: "Video",
      title: "Video",
      status: "approved",
      x: 0,
      y: 0,
      width: 220,
      skill: "video.candidates",
      outputs: {
        frame_indexes: [0],
        script_id: 301,
        timeline_id: 502,
        timeline_version: 2,
        clip_id: "clip-a",
        placed_timeline_clip_id: "clip-a",
      },
    };
    const task: ProductionCanvasNode = {
      id: "video-a-task-10",
      kind: "note",
      label: "Task #10",
      title: "Video Task",
      status: "review",
      x: 0,
      y: 120,
      width: 220,
      outputs: {
        source_node_id: "video-a",
        skill: "video.candidates",
        frame_indexes: [0],
        task_id: 10,
        script_id: 301,
        timeline_id: 502,
        timeline_version: 2,
        clip_id: "clip-a",
      },
    };
    assert.deepEqual(collectProductionCanvasContext([video, task]), {});
    assert.deepEqual(collectProductionCanvasContext([task, video]), {});
  });

  it("keeps scoped execution lineage coherent while clearing global lineage", () => {
    const global: ProductionCanvasNode = {
      id: "render",
      label: "Render",
      title: "Render",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "timeline.render",
      outputs: {
        virtual_ip_ids: [84],
        story_id: 61,
        script_id: 301,
        timeline_id: 502,
        timeline_version: 2,
        clip_id: "clip-global",
        task_id: 700,
      },
    };
    const scoped: ProductionCanvasNode = {
      id: "video-a",
      label: "Video",
      title: "Video",
      status: "running",
      x: 0,
      y: 120,
      width: 220,
      skill: "video.candidates",
      outputs: {
        frame_indexes: [0],
        virtual_ip_ids: [84],
        environment_ids: [13],
        story_id: 60,
        episode_id: 170,
        script_id: 140,
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "clip-a",
        dispatched_task_id: 802,
      },
    };
    const cleared = applyProductionCanvasContext([global, scoped], {
      virtual_ip_id: 85,
      environment_id: null,
      story_id: null,
      episode_id: null,
      script_id: null,
      timeline_id: null,
      timeline_version: null,
      clip_id: null,
      task_id: null,
    });

    assert.deepEqual(cleared[0].outputs, { virtual_ip_ids: [85] });
    assert.deepEqual(cleared[1].outputs, {
      frame_indexes: [0],
      virtual_ip_ids: [84],
      environment_ids: [13],
      story_id: 60,
      episode_id: 170,
      script_id: 140,
      timeline_id: 501,
      timeline_version: 7,
      clip_id: "clip-a",
      dispatched_task_id: 802,
      task_id: 802,
    });
    assert.deepEqual(collectProductionCanvasContext(cleared), {
      virtual_ip_id: 85,
    });
  });

  it("clears old task-note descendants without losing its task identity", () => {
    const task: ProductionCanvasNode = {
      id: "script-task-700",
      kind: "note",
      label: "Task #700",
      title: "Old Task",
      status: "review",
      x: 0,
      y: 0,
      width: 220,
      outputs: {
        source_node_id: "script",
        task_id: 700,
        story_id: 61,
        episode_id: 175,
        script_id: 301,
        timeline_id: 502,
        timeline_version: 2,
        clip_id: "clip-old",
      },
    };
    const render: ProductionCanvasNode = {
      id: "render",
      label: "Render",
      title: "Render",
      status: "ready",
      x: 0,
      y: 120,
      width: 220,
      skill: "timeline.render",
      outputs: { ...task.outputs },
    };
    const cleared = applyProductionCanvasContext([task, render], {
      virtual_ip_id: null,
      environment_id: null,
      story_id: 61,
      episode_id: null,
      script_id: null,
      timeline_id: null,
      timeline_version: null,
      clip_id: null,
      task_id: null,
    });

    assert.deepEqual(cleared[0].outputs, {
      source_node_id: "script",
      task_id: 700,
      story_id: 61,
    });
    assert.deepEqual(collectProductionCanvasContext(cleared), { story_id: 61 });
  });
});
