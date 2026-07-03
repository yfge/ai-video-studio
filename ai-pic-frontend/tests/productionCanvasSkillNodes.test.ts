import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isManualProductionCanvasNote,
  productionCanvasNodeStatusMeta,
  productionCanvasSkillResultToTaskNode,
  productionCanvasTaskStatusLabel,
} from "../src/components/features/canvas/productionCanvasSkillNodes";

describe("productionCanvasSkillNodes", () => {
  it("maps task nodes to task-aware labels and links", () => {
    assert.equal(productionCanvasTaskStatusLabel("completed"), "已完成");
    assert.deepEqual(
      productionCanvasNodeStatusMeta({
        id: "task-77",
        label: "Task #77",
        title: "Task",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        kind: "note",
        outputs: { task_id: 77, task_status: "failed" },
      }),
      { label: "失败", tone: "red" },
    );
    assert.deepEqual(
      productionCanvasNodeStatusMeta({
        id: "brief",
        label: "Brief",
        title: "Brief",
        status: "ready",
        x: 0,
        y: 0,
        width: 220,
      }),
      { label: "可复用", tone: "green" },
    );
  });

  it("distinguishes manual notes from task evidence notes", () => {
    assert.equal(
      isManualProductionCanvasNote({
        id: "note-1",
        label: "便签",
        title: "Manual",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        kind: "note",
      }),
      true,
    );
    assert.equal(
      isManualProductionCanvasNote({
        id: "task-77",
        label: "Task #77",
        title: "Task",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        kind: "note",
        outputs: { task_id: 77 },
      }),
      false,
    );
  });

  it("deep-links generated task evidence nodes", () => {
    const taskNode = productionCanvasSkillResultToTaskNode(
      {
        id: "script",
        label: "Script",
        title: "Script",
        status: "ready",
        x: 10,
        y: 20,
        width: 220,
      },
      {
        skill: "script.generate",
        label: "Script Skill",
        title: "剧本任务",
        status: "running",
        detail: "queued",
        outputs: {},
        reuse_targets: [],
      },
      {
        success: true,
        task_id: 77,
        task_status: "pending",
        skill_result: {
          skill: "script.generate",
          label: "Script Skill",
          title: "剧本任务",
          status: "running",
          detail: "queued",
          outputs: {},
          reuse_targets: [],
        },
      },
    );

    assert.equal(taskNode?.actionHref, "/tasks?task_id=77");
    assert.equal(taskNode?.actionLabel, "查看任务");
  });
});
