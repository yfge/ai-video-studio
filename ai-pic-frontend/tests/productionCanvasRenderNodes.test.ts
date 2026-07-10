import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasStateFromRun } from "../src/components/features/canvas/productionCanvasPersistence";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import {
  productionCanvasSkillResultToNode,
  productionCanvasSkillResultToTaskNode,
} from "../src/components/features/canvas/productionCanvasSkillNodes";
import type {
  ProductionCanvasRunResponse,
  ProductionCanvasSkillExecuteResponse,
  ProductionCanvasSkillResult,
} from "../src/utils/api/types";

const renderNode: ProductionCanvasNode = {
  id: "skill-timeline-render",
  label: "Render Skill",
  title: "Render current Timeline",
  status: "review",
  x: 100,
  y: 100,
  width: 240,
  skill: "timeline.render",
  actionHref: "/stories",
};

const renderResult: ProductionCanvasSkillResult = {
  skill: "timeline.render",
  label: "Render Skill",
  status: "ready",
  title: "最终渲染已完成",
  detail: "成片资产已生成。",
  outputs: {
    render_job_id: 122,
    render_status: "succeeded",
    output_url: "https://example.test/final.mp4",
  },
  reuse_targets: [],
};

describe("production canvas render nodes", () => {
  it("turns a RenderJob into linked canvas evidence", () => {
    const skillNode = productionCanvasSkillResultToNode(
      renderNode,
      renderResult,
    );
    const evidenceNode = productionCanvasSkillResultToTaskNode(
      renderNode,
      renderResult,
      {
        skill_result: renderResult,
        task_id: null,
        task_status: null,
      } satisfies ProductionCanvasSkillExecuteResponse,
    );

    assert.equal(skillNode.actionHref, "https://example.test/final.mp4");
    assert.equal(skillNode.actionLabel, "打开成片");
    assert.equal(evidenceNode?.label, "Render #122");
    assert.equal(evidenceNode?.outputs?.render_job_id, 122);
    assert.equal(evidenceNode?.actionHref, "https://example.test/final.mp4");
  });

  it("clears a stale output link while a new RenderJob is running", () => {
    const node = productionCanvasSkillResultToNode(
      {
        ...renderNode,
        actionHref: "https://example.test/old.mp4",
        actionLabel: "打开成片",
      },
      {
        ...renderResult,
        status: "running",
        title: "已提交最终渲染任务",
        outputs: {
          render_job_id: 123,
          render_status: "queued",
          render_progress: 0,
        },
      },
    );

    assert.equal(node.actionHref, undefined);
    assert.equal(node.actionLabel, undefined);
  });

  it("appends newly introduced plan nodes when restoring an older saved run", () => {
    const planNode = (id: string, skill: string, x: number) => ({
      id,
      label: skill,
      title: skill,
      status: "review" as const,
      x,
      y: 100,
      width: 240,
      kind: "skill_result",
      skill,
      detail: skill,
      outputs: { script_id: 130 },
      reuse_targets: [],
    });
    const script = planNode("skill-script-generate", "script.generate", 100);
    const render = planNode("skill-timeline-render", "timeline.render", 400);
    const exported = planNode("skill-timeline-export", "timeline.export", 700);
    const run = {
      prompt: "restore",
      run_id: "canvas-run",
      task_id: 1,
      skill_manifest: {
        version: "production_canvas.v1",
        entry_skill: "production_canvas.create",
        skills: [],
        reuse_policy: "reuse",
      },
      selected_assets: { virtual_ips: [], environments: [] },
      skill_results: [],
      nodes: [script, render, exported],
      saved_state: {
        nodes: [script],
        edges: [],
        viewport: { x: 0, y: 0, zoom: 1 },
        selected_node_id: script.id,
      },
    } as ProductionCanvasRunResponse;

    const restored = productionCanvasStateFromRun(run);

    assert.deepEqual(
      restored.nodes.map((node) => node.skill),
      ["script.generate", "timeline.render", "timeline.export"],
    );
  });
});
