import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasNodes } from "../src/components/features/canvas/productionCanvasModel";
import {
  isProductionCanvasPlanBatch,
  productionCanvasPlanEdges,
  withoutProductionCanvasPlaceholders,
} from "../src/components/features/canvas/productionCanvasPlanGraph";
import { withProductionCanvasPortContract } from "../src/components/features/canvas/productionCanvasPorts";

const planSkills = [
  "brief.compose",
  "script.generate",
  "timeline.assemble",
  "storyboard.plan",
  "image.candidates",
  "video.candidates",
  "timeline.render",
  "timeline.export",
];

const planNodes = planSkills.map((skill, index) =>
  withProductionCanvasPortContract({
    id: `skill-${skill.replaceAll(".", "-")}`,
    label: skill,
    title: skill,
    status: "ready",
    x: index * 260,
    y: 0,
    width: 220,
    kind: "skill_result",
    skill,
  }),
);

describe("production canvas plan graph", () => {
  it("replaces placeholders with one typed executable skill graph", () => {
    assert.equal(isProductionCanvasPlanBatch(planNodes), true);
    assert.deepEqual(
      withoutProductionCanvasPlaceholders(productionCanvasNodes),
      [],
    );

    const edges = productionCanvasPlanEdges(planNodes);
    assert.equal(edges.length, 7);
    const byId = new Map(planNodes.map((node) => [node.id, node]));
    for (const edge of edges) {
      const source = byId.get(edge.from);
      const target = byId.get(edge.to);
      const output = source?.outputPorts?.find(
        (port) => port.id === edge.fromPort,
      );
      const input = target?.inputPorts?.find((port) => port.id === edge.toPort);
      assert.ok(output, `missing output ${edge.fromPort}`);
      assert.ok(input, `missing input ${edge.toPort}`);
      assert.equal(output.type, input.type);
    }
  });

  it("requires an approved image before video execution", () => {
    const edge = productionCanvasPlanEdges(planNodes).find(
      (candidate) => candidate.edgeId?.includes("approved_image"),
    );
    assert.equal(edge?.bindingType, "selected_output");
    assert.equal(edge?.toPort, "start_frame");
  });
});
