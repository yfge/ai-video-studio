import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasStateFromRun } from "../src/components/features/canvas/productionCanvasPersistence";

describe("productionCanvasStateFromRun", () => {
  it("reconciles a restored skill node with its completed task evidence", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run-current",
      task_id: 6266,
      nodes: [],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [],
        nodes: [
          {
            id: "skill-virtual-ip-image",
            label: "Virtual IP Image",
            title: "Image task queued",
            status: "running",
            x: 100,
            y: 100,
            width: 220,
            kind: "skill_result",
            skill: "virtual_ip.image",
            outputs: {
              canvas_run_id: "canvas-run-current",
              dispatched_task_id: 99,
              task_status: "pending",
            },
          },
          {
            id: "skill-virtual-ip-image-task-99",
            label: "Task #99",
            title: "Image task complete",
            status: "review",
            x: 120,
            y: 240,
            width: 220,
            kind: "note",
            detail: "任务 #99 已完成；产物：virtual_ip_image:84:148",
            outputs: {
              canvas_run_id: "canvas-run-current",
              source_node_id: "skill-virtual-ip-image",
              task_id: 99,
              task_status: "completed",
              result_file_path: "virtual_ip_image:84:148",
            },
          },
          {
            id: "skill-virtual-ip-image-task-98",
            label: "Task #98",
            title: "Older image task failed",
            status: "blocked",
            x: 120,
            y: 360,
            width: 220,
            kind: "note",
            outputs: {
              source_node_id: "skill-virtual-ip-image",
              task_id: 98,
              task_status: "failed",
            },
          },
          {
            id: "skill-image-candidates",
            label: "Image Candidates",
            title: "Create storyboard candidates",
            status: "ready",
            x: 420,
            y: 100,
            width: 220,
            kind: "skill_result",
            skill: "image.candidates",
            outputs: { script_id: 42 },
          },
        ],
        selected_node_id: "skill-virtual-ip-image",
        viewport: { x: 0, y: 0, zoom: 1 },
      },
    } as any);

    const skill = restored.nodes.find(
      (node) => node.id === "skill-virtual-ip-image",
    );
    assert.equal(skill?.status, "review");
    assert.equal(skill?.outputs?.task_status, "completed");
    assert.equal(skill?.outputs?.result_file_path, "virtual_ip_image:84:148");
    const candidates = restored.nodes.find(
      (node) => node.id === "skill-image-candidates",
    );
    assert.deepEqual(candidates?.outputs?.reference_artifacts, [
      "virtual_ip_image:84:148",
    ]);
  });

  it("does not promote the canvas run task into skill task context", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run",
      task_id: 44,
      nodes: [
        {
          id: "report",
          label: "Report",
          title: "Report",
          status: "blocked",
          x: 0,
          y: 0,
          width: 220,
          kind: "skill_result",
          skill: "report.summarize",
          outputs: { required_inputs: ["task_id"] },
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
    } as any);

    const report = restored.nodes[0];
    assert.equal(report?.outputs?.canvas_task_id, 44);
    assert.equal(report?.outputs?.task_id, undefined);
    assert.deepEqual(report?.outputs?.required_inputs, ["task_id"]);
  });

  it("does not share current canvas task evidence as skill task input", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run-current",
      task_id: 6266,
      nodes: [
        {
          id: "skill-asset-select",
          label: "Asset Selection",
          title: "Asset plan",
          status: "blocked",
          x: 200,
          y: 100,
          width: 220,
          kind: "skill_result",
          skill: "asset.select",
          outputs: { required_inputs: ["virtual_ip_id"] },
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [],
        nodes: [
          {
            id: "skill-report-summarize-task-6266",
            label: "Task #6266",
            title: "Current canvas task",
            status: "review",
            x: 100,
            y: 220,
            width: 220,
            kind: "note",
            outputs: {
              canvas_run_id: "canvas-run-current",
              canvas_task_id: 6266,
              task_id: 6266,
            },
            action_href: "/tasks?task_id=6266",
          },
          {
            id: "skill-asset-select",
            label: "Asset Selection",
            title: "Asset saved",
            status: "blocked",
            x: 240,
            y: 160,
            width: 240,
            kind: "skill_result",
            skill: "asset.select",
            outputs: {
              canvas_run_id: "canvas-run-current",
              canvas_task_id: 6266,
              required_inputs: ["virtual_ip_id"],
            },
          },
        ],
        selected_node_id: "skill-asset-select",
        viewport: { x: 0, y: 0, zoom: 1 },
      },
    } as any);

    const taskEvidence = restored.nodes.find(
      (node) => node.id === "skill-report-summarize-task-6266",
    );
    assert.equal(taskEvidence?.outputs?.task_id, 6266);

    const asset = restored.nodes.find(
      (node) => node.id === "skill-asset-select",
    );
    assert.equal(asset?.outputs?.canvas_task_id, 6266);
    assert.equal(asset?.outputs?.task_id, undefined);
    assert.deepEqual(asset?.outputs?.required_inputs, ["virtual_ip_id"]);
  });

  it("drops unscoped saved task evidence from server run restore", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run-current",
      task_id: 6266,
      nodes: [
        {
          id: "skill-asset-select",
          label: "Asset Selection",
          title: "Asset plan",
          status: "blocked",
          x: 200,
          y: 100,
          width: 220,
          kind: "skill_result",
          skill: "asset.select",
          outputs: { required_inputs: ["virtual_ip_id", "environment_id"] },
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [],
        nodes: [
          {
            id: "summary-task-2",
            label: "Task #102",
            title: "Unscoped task",
            status: "blocked",
            x: 100,
            y: 220,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 102,
              task_status: "failed",
              task_title: "Unscoped task",
            },
          },
          {
            id: "skill-asset-select",
            label: "Asset Selection",
            title: "Stale unscoped asset result",
            status: "review",
            x: 240,
            y: 160,
            width: 240,
            kind: "skill_result",
            skill: "asset.select",
            outputs: {
              task_id: 102,
              required_inputs: ["virtual_ip_id", "environment_id"],
            },
          },
        ],
        selected_node_id: "summary-task-2",
        viewport: { x: 0, y: 0, zoom: 1 },
      },
    } as any);

    assert.deepEqual(
      restored.nodes.map((node) => node.id),
      ["skill-asset-select"],
    );
    assert.equal(restored.selectedNodeId, "skill-asset-select");

    const asset = restored.nodes[0];
    assert.equal(asset?.title, "Asset plan");
    assert.equal(asset?.x, 240);
    assert.equal(asset?.outputs?.canvas_run_id, "canvas-run-current");
    assert.equal(asset?.outputs?.canvas_task_id, 6266);
    assert.equal(asset?.outputs?.task_id, undefined);
    assert.deepEqual(asset?.outputs?.required_inputs, [
      "virtual_ip_id",
      "environment_id",
    ]);
  });

  it("drops saved task evidence from another canvas run", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run-current",
      task_id: 1,
      nodes: [
        {
          id: "skill-report-summarize",
          label: "Report Skill",
          title: "Report plan",
          status: "blocked",
          x: 100,
          y: 100,
          width: 220,
          kind: "skill_result",
          skill: "report.summarize",
          outputs: { required_inputs: ["task_id"] },
        },
        {
          id: "skill-asset-select",
          label: "Asset Selection",
          title: "Asset plan",
          status: "blocked",
          x: 200,
          y: 100,
          width: 220,
          kind: "skill_result",
          skill: "asset.select",
          outputs: { required_inputs: ["virtual_ip_id"] },
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [],
        nodes: [
          {
            id: "skill-report-summarize-task-999",
            label: "Task #999",
            title: "Stale task",
            status: "review",
            x: 100,
            y: 220,
            width: 220,
            kind: "note",
            outputs: {
              canvas_run_id: "canvas-run-stale",
              canvas_task_id: 999,
              task_id: 999,
            },
            action_href: "/tasks?task_id=999",
          },
          {
            id: "skill-report-summarize",
            label: "Report Skill",
            title: "Stale report result",
            status: "review",
            x: 140,
            y: 160,
            width: 240,
            kind: "skill_result",
            skill: "report.summarize",
            outputs: {
              canvas_run_id: "canvas-run-stale",
              canvas_task_id: 999,
              task_id: 999,
            },
            action_href: "/tasks?task_id=999",
          },
          {
            id: "skill-asset-select",
            label: "Asset Selection",
            title: "Asset saved",
            status: "blocked",
            x: 240,
            y: 160,
            width: 240,
            kind: "skill_result",
            skill: "asset.select",
            outputs: {
              canvas_run_id: "canvas-run-current",
              canvas_task_id: 999,
              task_id: 999,
              required_inputs: ["virtual_ip_id"],
            },
          },
        ],
        selected_node_id: "skill-report-summarize-task-999",
        viewport: { x: 0, y: 0, zoom: 1 },
      },
    } as any);

    assert.deepEqual(
      restored.nodes.map((node) => node.id),
      ["skill-report-summarize", "skill-asset-select"],
    );
    assert.equal(restored.selectedNodeId, "skill-report-summarize");

    const report = restored.nodes.find(
      (node) => node.id === "skill-report-summarize",
    );
    assert.equal(report?.title, "Report plan");
    assert.equal(report?.x, 140);
    assert.equal(report?.outputs?.canvas_run_id, "canvas-run-current");
    assert.equal(report?.outputs?.canvas_task_id, 1);
    assert.equal(report?.outputs?.task_id, undefined);
    assert.equal(report?.actionHref, undefined);

    const asset = restored.nodes.find(
      (node) => node.id === "skill-asset-select",
    );
    assert.equal(asset?.outputs?.canvas_run_id, "canvas-run-current");
    assert.equal(asset?.outputs?.canvas_task_id, 1);
    assert.equal(asset?.outputs?.task_id, undefined);
    assert.deepEqual(asset?.outputs?.required_inputs, ["virtual_ip_id"]);
  });

  it("sanitizes server plan nodes", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run",
      task_id: 1,
      nodes: [
        {
          id: "brief",
          label: "Brief",
          title: "Brief",
          status: "review",
          x: Number.NaN,
          y: Number.POSITIVE_INFINITY,
          width: Number.NaN,
          height: Number.NaN,
        },
      ],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
    } as any);

    assert.equal(restored.nodes[0]?.x, 0);
    assert.equal(restored.nodes[0]?.y, 0);
    assert.equal(restored.nodes[0]?.width, 220);
    assert.equal(restored.nodes[0]?.height, 118);
  });

  it("sanitizes saved server canvas state", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run",
      task_id: 1,
      nodes: [],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [
          { from: "brief", to: "script" },
          { from: "brief", to: "script" },
          { from: "brief", to: "brief" },
          { from: "brief", to: "missing" },
        ],
        nodes: [
          {
            id: "brief",
            label: "Brief",
            title: "Brief",
            status: "review",
            x: Number.NaN,
            y: Number.POSITIVE_INFINITY,
            width: 0,
            height: -1,
          },
          {
            id: "brief",
            label: "Brief duplicate",
            title: "Duplicate",
            status: "review",
            x: 10,
            y: 10,
            width: 220,
          },
          {
            id: "script",
            label: "Script",
            title: "Script",
            status: "review",
            x: 300,
            y: 0,
            width: 220,
          },
        ],
        selected_node_id: "missing",
        viewport: { x: Number.NaN, y: Number.POSITIVE_INFINITY, zoom: 0 },
      },
    } as any);

    assert.deepEqual(
      restored.nodes.map((node) => node.id),
      ["brief", "script"],
    );
    assert.equal(restored.nodes[0]?.x, 0);
    assert.equal(restored.nodes[0]?.y, 0);
    assert.equal(restored.nodes[0]?.width, 190);
    assert.equal(restored.nodes[0]?.height, undefined);
    assert.deepEqual(restored.edges, [{ from: "brief", to: "script" }]);
    assert.deepEqual(restored.viewport, { x: 0, y: 0, zoom: 0.5 });
    assert.equal(restored.selectedNodeId, "brief");
  });
});
