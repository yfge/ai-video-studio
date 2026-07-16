import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { emptyProductionCanvasContext } from "../src/components/features/canvas/productionCanvasContext";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import { productionCanvasSkillExecuteRequest } from "../src/components/features/canvas/productionCanvasSkillRequest";
import { productionCanvasSavedNodeMatchesRun } from "../src/components/features/canvas/useProductionCanvasNodeExecution";

describe("productionCanvasSkillExecuteRequest", () => {
  it("preserves single-video planning mode from persisted node outputs", () => {
    const node: ProductionCanvasNode = {
      id: "single-video-script",
      label: "Script",
      title: "Single video script",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "script.generate",
      outputs: {
        episode_id: 20,
        planning_mode: "single_video",
      },
    };

    const request = productionCanvasSkillExecuteRequest({
      context: emptyProductionCanvasContext,
      currentRunId: "run-single-video",
      executionScope: "node",
      node,
      prompt: "generate",
    });

    assert.equal(request.planning_mode, "single_video");
  });

  it("does not revive a stale Run ID from node outputs", () => {
    const node: ProductionCanvasNode = {
      id: "stale",
      label: "Stale",
      title: "Old saved node",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "brief.compose",
      outputs: { canvas_run_id: "stale-run" },
    };

    const request = productionCanvasSkillExecuteRequest({
      context: emptyProductionCanvasContext,
      currentRunId: null,
      executionScope: "node",
      node,
      prompt: "generate",
    });

    assert.equal(request.run_id, undefined);
    assert.equal(productionCanvasSavedNodeMatchesRun(node, ""), false);
    assert.equal(
      productionCanvasSavedNodeMatchesRun(node, "different-run"),
      false,
    );
    assert.equal(productionCanvasSavedNodeMatchesRun(node, "stale-run"), true);
  });

  it("drops reference artifacts from a previously selected IP or environment", () => {
    const node: ProductionCanvasNode = {
      id: "video",
      label: "Video",
      title: "Video",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "video.candidates",
      outputs: {
        reference_artifacts: [
          "virtual_ip_image:84:148",
          "virtual_ip_image:11:149",
          "environment_images:13:1",
          "environment_images:22:2",
          "timeline:70:v6",
        ],
      },
    };

    const request = productionCanvasSkillExecuteRequest({
      context: {
        ...emptyProductionCanvasContext,
        virtual_ip_id: "11",
        environment_id: "22",
      },
      currentRunId: "run-1",
      executionScope: "node",
      node,
      prompt: "generate",
    });

    assert.deepEqual(request.reference_artifacts, [
      "virtual_ip_image:11:149",
      "environment_images:22:2",
      "timeline:70:v6",
    ]);
  });

  it("drops typed reference artifacts when their matching scope is unbound", () => {
    const node: ProductionCanvasNode = {
      id: "image",
      label: "Image",
      title: "Image",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "image.candidates",
      outputs: {
        reference_artifacts: [
          "virtual_ip_image:84:148",
          "environment_images:13:1",
        ],
      },
    };
    const ipOnly = productionCanvasSkillExecuteRequest({
      context: { ...emptyProductionCanvasContext, virtual_ip_id: "84" },
      currentRunId: "run-1",
      executionScope: "node",
      node,
      prompt: "generate",
    });
    const environmentOnly = productionCanvasSkillExecuteRequest({
      context: { ...emptyProductionCanvasContext, environment_id: "13" },
      currentRunId: "run-1",
      executionScope: "node",
      node,
      prompt: "generate",
    });

    assert.deepEqual(ipOnly.reference_artifacts, ["virtual_ip_image:84:148"]);
    assert.deepEqual(environmentOnly.reference_artifacts, [
      "environment_images:13:1",
    ]);
  });

  it("does not revive cleared descendants from stale node outputs", () => {
    const node: ProductionCanvasNode = {
      id: "video",
      label: "Video",
      title: "Video",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "video.candidates",
      outputs: {
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
    const cases = [
      { virtual_ip_id: "85" },
      { virtual_ip_id: "84", story_id: "62" },
      { virtual_ip_id: "84", story_id: "61", episode_id: "175" },
    ];

    for (const patch of cases) {
      const request = productionCanvasSkillExecuteRequest({
        context: { ...emptyProductionCanvasContext, ...patch },
        currentRunId: "run-1",
        executionScope: "node",
        node,
        prompt: "generate",
      });
      for (const key of [
        "environment_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
      ] as const) {
        assert.equal(
          request[key],
          undefined,
          `${JSON.stringify(patch)} ${key}`,
        );
      }
      if (!("episode_id" in patch)) assert.equal(request.episode_id, undefined);
      if (!("story_id" in patch)) assert.equal(request.story_id, undefined);
    }
  });

  it("executes frame-scoped media with its own Script Timeline and clip", () => {
    const node: ProductionCanvasNode = {
      id: "video-a",
      label: "Video",
      title: "Video A",
      status: "ready",
      x: 0,
      y: 0,
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
      },
    };

    const request = productionCanvasSkillExecuteRequest({
      context: {
        ...emptyProductionCanvasContext,
        story_id: "61",
        episode_id: "175",
        script_id: "301",
        timeline_id: "502",
        timeline_version: "3",
        clip_id: "clip-b",
      },
      currentRunId: "run-1",
      executionScope: "node",
      node,
      prompt: "generate",
    });

    assert.equal(request.virtual_ip_id, 84);
    assert.equal(request.environment_id, 13);
    assert.equal(request.story_id, 60);
    assert.equal(request.episode_id, 170);
    assert.equal(request.script_id, 140);
    assert.equal(request.timeline_id, 501);
    assert.equal(request.timeline_version, 7);
    assert.equal(request.clip_id, "clip-a");
  });
});
