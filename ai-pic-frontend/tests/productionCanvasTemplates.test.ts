import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  insertProductionCanvasTemplate,
  productionCanvasTemplates,
} from "../src/components/features/canvas/productionCanvasTemplates";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

describe("production canvas domain templates", () => {
  it("keeps template definitions provider agnostic", () => {
    const source = JSON.stringify(productionCanvasTemplates).toLowerCase();
    for (const implementationTerm of [
      "provider",
      "worker",
      "repository",
      "service",
      "api",
    ]) {
      assert.equal(source.includes(implementationTerm), false);
    }
  });

  it("inserts reusable typed subflows with unique identities and sections", () => {
    const initial = createProductionCanvasState([], []);
    const first = insertProductionCanvasTemplate(initial, "shot-review");
    const second = insertProductionCanvasTemplate(first, "shot-review");

    assert.equal(first.nodes.length, 2);
    assert.equal(first.edges.length, 1);
    assert.equal(first.edges[0].bindingType, "selected_output");
    assert.equal(first.edges[0].fromPort, "approved_storyboard");
    assert.equal(first.edges[0].toPort, "approved_storyboard");
    assert.equal(first.sections?.[0].title, "镜头评审子流程");
    assert.equal(second.nodes.length, 4);
    assert.equal(new Set(second.nodes.map((item) => item.id)).size, 4);
    assert.equal(second.sections?.length, 2);
    assert.deepEqual(second.selectedNodeIds, second.sections?.[1].nodeIds);
    assert.equal(second.selectedNodeId, "");
    assert.ok(second.viewport.x < 0);
  });

  it("leaves the canvas unchanged for an unknown template", () => {
    const initial = createProductionCanvasState([], []);
    assert.equal(insertProductionCanvasTemplate(initial, "missing"), initial);
  });

  it("propagates existing production context into inserted subflows", () => {
    const initial = createProductionCanvasState(
      [
        {
          id: "script-context",
          label: "剧本",
          title: "已有剧本",
          status: "ready",
          x: 0,
          y: 0,
          width: 200,
          outputs: {
            canvas_run_id: "run-42",
            script_id: 42,
            task_id: 420,
          },
        },
      ],
      [],
    );
    const inserted = insertProductionCanvasTemplate(initial, "shot-review");
    const storyboardNode = inserted.nodes.find(
      (item) => item.skill === "storyboard.candidates",
    );

    assert.equal(storyboardNode?.outputs?.script_id, 42);
    assert.equal(storyboardNode?.outputs?.canvas_run_id, "run-42");
    assert.equal(storyboardNode?.outputs?.task_id, 420);
  });

  it("keeps Timeline placement explicit in the delivery template", () => {
    const inserted = insertProductionCanvasTemplate(
      createProductionCanvasState([], []),
      "delivery",
    );

    assert.ok(inserted.nodes.some((item) => item.skill === "timeline.place"));
    assert.ok(
      inserted.edges.some(
        (item) =>
          item.fromPort === "placed_timeline" && item.toPort === "timeline",
      ),
    );
    assert.equal(
      inserted.edges.some((item) => item.toPort === "approved_video"),
      false,
    );
  });
});
