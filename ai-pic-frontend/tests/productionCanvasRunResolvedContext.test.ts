import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasStateFromRun } from "../src/components/features/canvas/productionCanvasPersistence";

describe("productionCanvasStateFromRun resolved context", () => {
  it("restores top-level context when saved nodes cover every plan node", () => {
    const planNodes = ["asset", "report"].map((id, index) => ({
      id,
      label: id,
      title: `Plan ${id}`,
      status: "ready",
      x: index * 240,
      y: 0,
      width: 220,
      kind: "skill_result",
      skill: id === "asset" ? "asset.select" : "report.summarize",
    }));
    const restored = productionCanvasStateFromRun({
      run_id: "run-context",
      task_id: 700,
      resolved_context: {
        virtual_ip_id: 84,
        environment_id: 13,
        story_id: 61,
        episode_id: 174,
        script_id: 144,
        timeline_id: 70,
        timeline_version: 6,
        clip_id: "clip-7",
        task_id: 6357,
      },
      nodes: planNodes,
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        nodes: planNodes.map((node) => ({
          ...node,
          title: `Saved ${node.id}`,
          outputs:
            node.id === "asset"
              ? { virtual_ip_ids: [999], environment_ids: [998] }
              : {},
        })),
        viewport: { x: 0, y: 0, zoom: 1 },
      },
    } as any);

    assert.deepEqual(
      restored.nodes.map((node) => node.title),
      ["Saved asset", "Saved report"],
    );
    for (const node of restored.nodes) {
      assert.deepEqual(node.outputs?.virtual_ip_ids, [84]);
      assert.deepEqual(node.outputs?.environment_ids, [13]);
      assert.equal(node.outputs?.story_id, 61);
      assert.equal(node.outputs?.episode_id, 174);
      assert.equal(node.outputs?.script_id, 144);
      assert.equal(node.outputs?.timeline_id, 70);
      assert.equal(node.outputs?.timeline_version, 6);
      assert.equal(node.outputs?.clip_id, "clip-7");
      assert.equal(node.outputs?.task_id, undefined);
    }
  });
});
