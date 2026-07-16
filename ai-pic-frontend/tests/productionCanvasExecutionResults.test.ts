import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { productionCanvasExecutionPublications } from "../src/components/features/canvas/productionCanvasExecutionResults";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";
import { appendProductionCanvasNodes } from "../src/components/features/canvas/useProductionCanvasDefinitionActions";

function node(runId: string, title: string): ProductionCanvasNode {
  return {
    id: "skill-script",
    label: "Script",
    title,
    status: "ready",
    x: runId === "run-a" ? 10 : 310,
    y: 20,
    width: 220,
    skill: "script.generate",
    outputs: { canvas_run_id: runId },
  };
}

describe("productionCanvasExecutionPublications", () => {
  it("uses the requested new-plan node when an old plan reused its id", () => {
    const oldNode = node("run-a", "旧计划节点");
    const newNode = node("run-b", "新计划节点");
    const [publication] = productionCanvasExecutionPublications(
      {
        node_id: newNode.id,
        skill_result: {
          label: "Script",
          title: "新计划执行完成",
          status: "review",
          outputs: {},
          reuse_targets: [],
        },
      },
      newNode,
      [oldNode],
    );

    assert.equal(publication.sourceNode, newNode);
    assert.equal(publication.resultNodes[0].x, 310);
    assert.equal(publication.resultNodes[0].outputs?.canvas_run_id, "run-b");
  });

  it("publishes the resolved context and clears stale descendants", () => {
    const sourceNode = {
      ...node("run-a", "旧故事节点"),
      outputs: {
        canvas_run_id: "run-a",
        virtual_ip_ids: [84],
        environment_ids: [13],
        story_id: 61,
        episode_id: 174,
        script_id: 144,
        timeline_id: 70,
        timeline_version: 6,
        clip_id: "old-clip",
      },
    };
    const [publication] = productionCanvasExecutionPublications(
      {
        node_id: sourceNode.id,
        task_id: 999,
        task_status: "pending",
        resolved_context: {
          virtual_ip_id: 84,
          environment_id: 13,
          story_id: 62,
          episode_id: 175,
        },
        skill_result: {
          label: "Script",
          title: "新故事执行完成",
          status: "running",
          outputs: { dispatched_task_id: 999 },
          reuse_targets: [],
        },
      },
      sourceNode,
      [sourceNode],
    );

    assert.equal(publication.resultNodes.length, 2);
    for (const resultNode of publication.resultNodes) {
      assert.equal(resultNode.outputs?.story_id, 62);
      assert.equal(resultNode.outputs?.episode_id, 175);
      assert.equal(resultNode.outputs?.script_id, undefined);
      assert.equal(resultNode.outputs?.timeline_id, undefined);
      assert.equal(resultNode.outputs?.timeline_version, undefined);
      assert.equal(resultNode.outputs?.clip_id, undefined);
    }
  });

  it("publishes runtime identity and keeps outputs produced after resolution", () => {
    const sourceNode = {
      ...node("run-a", "故事节点"),
      definitionVersion: 1,
      outputs: {
        story_id: 61,
        episode_id: 174,
        script_id: 144,
        timeline_id: 70,
        timeline_version: 6,
        clip_id: "old-clip",
      },
    };
    const [publication] = productionCanvasExecutionPublications(
      {
        node_id: sourceNode.id,
        input_fingerprint: "a".repeat(64),
        resolved_context_revision: 3,
        resolved_context: {
          virtual_ip_id: null,
          environment_id: null,
          story_id: 61,
          episode_id: 175,
          script_id: null,
          timeline_id: null,
          timeline_version: null,
          clip_id: null,
          task_id: null,
        },
        skill_result: {
          label: "Script",
          title: "新剧本已生成",
          status: "review",
          outputs: { script_id: 301 },
          reuse_targets: [],
        },
      },
      sourceNode,
      [sourceNode],
    );

    assert.equal(publication.resultNodes[0].definitionVersion, 1);
    assert.equal(
      publication.resultNodes[0].executionInputFingerprint,
      "a".repeat(64),
    );
    assert.equal(publication.resultNodes[0].outputs?.script_id, 301);
    assert.equal(publication.resultNodes[0].outputs?.timeline_id, undefined);
    assert.equal(publication.resolvedContext.script_id, 301);
    assert.equal(publication.resolvedContext.timeline_id, null);
    assert.equal(
      publication.resultNodes[0].outputs?.resolved_context_revision,
      3,
    );
    const state = appendProductionCanvasNodes(
      createProductionCanvasState([sourceNode]),
      publication.resultNodes,
      publication.resolvedContext,
    );
    assert.equal(state.resolvedContextRevision, 3);
  });

  it("applies authoritative clears to retained nodes while appending results", () => {
    const sourceNode = node("run-a", "故事节点");
    const retained: ProductionCanvasNode = {
      ...node("run-a", "旧渲染"),
      id: "render",
      skill: "timeline.render",
      outputs: {
        story_id: 61,
        episode_id: 174,
        script_id: 144,
        timeline_id: 70,
        timeline_version: 6,
        clip_id: "old-clip",
      },
    };
    const [publication] = productionCanvasExecutionPublications(
      {
        node_id: sourceNode.id,
        resolved_context: {
          virtual_ip_id: null,
          environment_id: null,
          story_id: 61,
          episode_id: null,
          script_id: null,
          timeline_id: null,
          timeline_version: null,
          clip_id: null,
          task_id: null,
        },
        skill_result: {
          label: "Script",
          title: "回到故事层",
          status: "review",
          outputs: {},
          reuse_targets: [],
        },
      },
      sourceNode,
      [sourceNode, retained],
    );
    const next = appendProductionCanvasNodes(
      createProductionCanvasState([sourceNode, retained]),
      publication.resultNodes,
      publication.resolvedContext,
    );
    const render = next.nodes.find((item) => item.id === "render");

    assert.equal(render?.outputs?.story_id, 61);
    assert.equal(render?.outputs?.episode_id, undefined);
    assert.equal(render?.outputs?.script_id, undefined);
    assert.equal(render?.outputs?.timeline_id, undefined);
    assert.equal(render?.outputs?.clip_id, undefined);
  });
});
