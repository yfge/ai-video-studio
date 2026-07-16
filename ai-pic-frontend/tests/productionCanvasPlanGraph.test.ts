import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasNodes } from "../src/components/features/canvas/productionCanvasModel";
import {
  isProductionCanvasPlanBatch,
  productionCanvasPlanEdges,
  productionCanvasSavedEdges,
  withoutProductionCanvasPlaceholders,
} from "../src/components/features/canvas/productionCanvasPlanGraph";
import { withProductionCanvasPortContract } from "../src/components/features/canvas/productionCanvasPorts";
import { productionCanvasStateFromRun } from "../src/components/features/canvas/productionCanvasPersistence";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";
import { appendProductionCanvasNodes } from "../src/components/features/canvas/useProductionCanvasDefinitionActions";

const planSkills = [
  "brief.compose",
  "asset.select",
  "script.generate",
  "timeline.assemble",
  "storyboard.candidates",
  "video.candidates",
  "timeline.place",
  "timeline.render",
  "timeline.export",
  "report.summarize",
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
    assert.equal(edges.length, 11);
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

  it("requires an approved storyboard without a start-frame binding", () => {
    const edge = productionCanvasPlanEdges(planNodes).find(
      (candidate) => candidate.edgeId?.includes("approved_storyboard"),
    );
    assert.equal(edge?.bindingType, "selected_output");
    assert.equal(edge?.toPort, "approved_storyboard");
    assert.equal(
      productionCanvasPlanEdges(planNodes).some(
        (candidate) => candidate.toPort === "start_frame",
      ),
      false,
    );
  });

  it("uses a server-planned subset and typed edges instead of the fixed graph", () => {
    const nodes = planNodes
      .filter((node) =>
        ["brief.compose", "script.generate"].includes(node.skill || ""),
      )
      .map((node) => ({ ...node }));
    const plannedEdges = productionCanvasSavedEdges([
      {
        edge_id: "brief-to-script",
        from: nodes[0].id,
        from_port: "production_brief",
        to: nodes[1].id,
        to_port: "production_brief",
        binding_type: "value",
        required: true,
      },
    ]);
    nodes[0].plannedEdges = plannedEdges;

    const state = appendProductionCanvasNodes(
      createProductionCanvasState(),
      nodes,
    );

    assert.deepEqual(
      state.nodes.map((node) => node.skill),
      ["brief.compose", "script.generate"],
    );
    assert.deepEqual(state.edges, plannedEdges);
  });

  it("restores server-planned edges before any client state is saved", () => {
    const nodes = planNodes.filter((node) =>
      ["brief.compose", "script.generate"].includes(node.skill || ""),
    );
    const restored = productionCanvasStateFromRun({
      prompt: "只生成剧本",
      nodes: nodes.map((node) => ({
        ...node,
        skill: node.skill || "",
        input_ports: node.inputPorts,
        output_ports: node.outputPorts,
      })),
      edges: [
        {
          edge_id: "brief-to-script",
          from: nodes[0].id,
          from_port: "production_brief",
          to: nodes[1].id,
          to_port: "production_brief",
          binding_type: "value",
          required: true,
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      planner: {
        mode: "autonomous",
        version: "production_canvas.planner.v1",
        objective: "只生成剧本",
        selected_skills: ["brief.compose", "script.generate"],
      },
    });

    assert.equal(restored.edges.length, 1);
    assert.equal(restored.edges[0].edgeId, "brief-to-script");
    assert.equal(restored.edges[0].toPort, "production_brief");
  });
});
