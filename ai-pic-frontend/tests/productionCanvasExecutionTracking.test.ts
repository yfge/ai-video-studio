import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  productionCanvasExecutionFailure,
  productionCanvasExecutionFromRenderJob,
  productionCanvasExecutionFromTask,
  reconcileProductionCanvasExecutionTasks,
} from "../src/components/features/canvas/productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import type { Task } from "../src/utils/api/types";

const skillNode: ProductionCanvasNode = {
  id: "skill-virtual-ip-image",
  label: "Virtual IP Image",
  title: "已提交角色图任务",
  status: "running",
  x: 0,
  y: 0,
  width: 220,
  outputs: { dispatched_task_id: 99, task_status: "pending" },
};
const taskNode: ProductionCanvasNode = {
  id: "skill-virtual-ip-image-task-99",
  kind: "note",
  label: "Task #99",
  title: "已提交角色图任务",
  status: "running",
  x: 0,
  y: 120,
  width: 220,
  outputs: { source_node_id: skillNode.id, task_id: 99 },
};

describe("production canvas execution tracking", () => {
  it("propagates completed task artifacts to the skill and evidence nodes", () => {
    const nodes = productionCanvasExecutionFromTask({ skillNode, taskNode }, {
      id: 99,
      business_id: "task-99",
      title: "角色图已完成",
      status: "completed",
      result_file_path: "virtual_ip_image:84:148",
      created_at: "2026-07-10T10:00:00Z",
      user_id: 1,
    } satisfies Task);

    assert.equal(nodes[0].status, "review");
    assert.equal(nodes[1].status, "review");
    assert.equal(nodes[0].outputs?.task_status, "completed");
    assert.equal(nodes[1].outputs?.result_file_path, "virtual_ip_image:84:148");
  });

  it("propagates task failures to both nodes", () => {
    const nodes = productionCanvasExecutionFailure(
      { skillNode, taskNode },
      99,
      "quota exceeded",
    );

    assert.equal(nodes[0].status, "blocked");
    assert.equal(nodes[1].status, "blocked");
    assert.equal(nodes[0].outputs?.task_error_message, "quota exceeded");
  });

  it("turns a succeeded RenderJob into linked export-ready nodes", () => {
    const nodes = productionCanvasExecutionFromRenderJob(
      { skillNode, taskNode },
      {
        id: 122,
        business_id: "render-122",
        timeline_id: 71,
        timeline_version: 6,
        render_type: "final",
        preset_hash: "preset",
        preset: { fps: 24 },
        status: "succeeded",
        progress: 100,
        output_asset_id: 375,
        output_asset: {
          id: 375,
          business_id: "asset-375",
          asset_type: "video",
          origin: "timeline_render",
          file_url: "/media/final.mp4",
          created_at: "2026-07-10T10:00:00Z",
          updated_at: "2026-07-10T10:00:00Z",
        },
        created_at: "2026-07-10T10:00:00Z",
        updated_at: "2026-07-10T10:00:01Z",
      },
    );

    assert.equal(nodes[0].status, "ready");
    assert.equal(nodes[1].outputs?.render_status, "succeeded");
    assert.equal(nodes[0].actionHref, "/media/final.mp4");
    assert.equal(nodes[1].actionLabel, "打开成片");
  });

  it("does not restore stale Timeline context from task evidence", () => {
    const reconciled = reconcileProductionCanvasExecutionTasks([
      {
        ...skillNode,
        outputs: {
          dispatched_task_id: 99,
          task_status: "pending",
          timeline_id: 71,
          timeline_version: 8,
        },
      },
      {
        ...taskNode,
        status: "review",
        outputs: {
          ...taskNode.outputs,
          task_status: "completed",
          timeline_id: 71,
          timeline_version: 7,
          result_file_path: "timeline_videos:71:v7:1",
        },
      },
    ]);

    assert.equal(reconciled[0].outputs?.timeline_version, 8);
    assert.equal(reconciled[0].outputs?.task_status, "completed");
    assert.equal(
      reconciled[0].outputs?.result_file_path,
      "timeline_videos:71:v7:1",
    );
  });
});
