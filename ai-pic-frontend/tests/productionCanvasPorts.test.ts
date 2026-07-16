import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  productionCanvasEdges,
  productionCanvasNodes,
} from "../src/components/features/canvas/productionCanvasModel";
import {
  compatibleProductionCanvasEdges,
  isTypedProductionCanvasEdge,
  productionCanvasPortContract,
} from "../src/components/features/canvas/productionCanvasPorts";
import { toProductionCanvasSavedState } from "../src/components/features/canvas/productionCanvasPersistence";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

describe("production canvas typed ports", () => {
  it("persists the default workflow as a graph v2 definition", () => {
    const saved = toProductionCanvasSavedState(createProductionCanvasState());

    assert.equal(saved.graph_version, 2);
    assert.ok(productionCanvasEdges.every(isTypedProductionCanvasEdge));
    assert.ok(saved.edges?.every((edge) => edge.edge_id));
    assert.ok(saved.edges?.every((edge) => edge.from_port && edge.to_port));
    assert.ok(saved.nodes.every((node) => node.definition_version === 1));
    assert.ok(
      saved.nodes
        .filter((node) => node.kind !== "note")
        .every((node) => node.input_ports?.length || node.output_ports?.length),
    );
  });

  it("keeps untyped restored edges on graph v1", () => {
    const state = createProductionCanvasState(productionCanvasNodes, [
      { from: "brief", to: "script" },
    ]);

    assert.equal(toProductionCanvasSavedState(state).graph_version, 1);
  });

  it("defaults video to a storyboard while preserving explicit legacy ports", () => {
    const base = {
      id: "video-contract",
      label: "Video",
      title: "Video",
      status: "ready" as const,
      x: 0,
      y: 0,
      width: 220,
      kind: "skill_result" as const,
      skill: "video.candidates",
    };

    assert.deepEqual(
      productionCanvasPortContract(base).inputPorts?.map((port) => [
        port.id,
        port.required,
      ]),
      [["approved_storyboard", true]],
    );
    assert.deepEqual(
      productionCanvasPortContract({
        ...base,
        inputPorts: [
          {
            id: "start_frame",
            label: "起始帧",
            type: "image" as const,
            required: false,
          },
        ],
      }).inputPorts?.map((port) => port.id),
      ["start_frame"],
    );
  });

  it("discovers only compatible unbound port pairs", () => {
    const storyboard = productionCanvasNodes.find(
      (node) => node.id === "storyboard",
    );
    const video = productionCanvasNodes.find((node) => node.id === "video");
    const report = productionCanvasNodes.find((node) => node.id === "report");
    assert.ok(storyboard && video && report);
    assert.deepEqual(
      productionCanvasPortContract(productionCanvasNodes[0]!).inputPorts,
      [],
    );

    assert.deepEqual(
      compatibleProductionCanvasEdges(storyboard, video, productionCanvasEdges),
      [],
    );
    const withoutStoryboardBinding = productionCanvasEdges.filter(
      (edge) =>
        edge.edgeId !==
        "storyboard-approved_storyboard-to-video-approved_storyboard",
    );
    const [binding] = compatibleProductionCanvasEdges(
      storyboard,
      video,
      withoutStoryboardBinding,
    );
    assert.equal(binding?.fromPort, "approved_storyboard");
    assert.equal(binding?.toPort, "approved_storyboard");
    assert.equal(binding?.bindingType, "selected_output");
    assert.deepEqual(
      compatibleProductionCanvasEdges(
        storyboard,
        report,
        withoutStoryboardBinding,
      ),
      [],
    );
  });
});
