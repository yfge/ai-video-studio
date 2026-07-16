import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  addProductionCanvasNote,
  applyProductionCanvasContext,
  createProductionCanvasState,
  moveProductionCanvasNode,
  zoomProductionCanvas,
} from "../src/components/features/canvas/productionCanvasState";
import { collectProductionCanvasContext } from "../src/components/features/canvas/productionCanvasSharedContext";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import {
  centerProductionCanvasOnNode,
  displayProductionCanvasNodeTitle,
  getWorldBounds,
} from "../src/components/features/canvas/productionCanvasViewModel";

describe("productionCanvasState", () => {
  it("propagates only completed source artifacts into downstream context", () => {
    const nodes = applyProductionCanvasContext([
      {
        id: "skill-virtual-ip-image",
        label: "Virtual IP Image",
        title: "角色图已完成",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        skill: "virtual_ip.image",
        outputs: {
          virtual_ip_ids: [84],
          task_status: "completed",
          result_file_path: "virtual_ip_image:84:148",
        },
      },
      {
        id: "skill-environment-image",
        label: "Environment Image",
        title: "环境图已完成",
        status: "review",
        x: 260,
        y: 0,
        width: 220,
        skill: "environment.image",
        outputs: {
          environment_ids: [13],
          task_status: "completed",
          result_file_path: "environment_images:13:1",
        },
      },
      {
        id: "skill-environment-image-task-98",
        kind: "note",
        label: "Task #98",
        title: "旧环境图任务",
        status: "review",
        x: 260,
        y: 120,
        width: 220,
        outputs: {
          task_status: "completed",
          result_file_path: "environment_images:13:4",
        },
      },
      {
        id: "skill-image-candidates",
        label: "Image Candidates",
        title: "生成分镜候选",
        status: "ready",
        x: 520,
        y: 0,
        width: 220,
        skill: "image.candidates",
        outputs: {
          script_id: 42,
          timeline_id: 71,
          timeline_version: 8,
          placed_timeline_clip_id: "clip-8",
          frame_indexes: [0],
        },
      },
      {
        id: "skill-report",
        label: "Report",
        title: "共享最新剧本",
        status: "ready",
        x: 780,
        y: 0,
        width: 220,
        skill: "report.summarize",
        outputs: {
          story_id: 9,
          episode_id: 19,
          script_id: 130,
          timeline_id: 71,
          timeline_version: 7,
          clip_id: "clip-9",
        },
      },
    ]);

    const candidates = nodes.find((node) => node.skill === "image.candidates");
    assert.equal(candidates?.outputs?.script_id, 42);
    assert.equal(candidates?.outputs?.timeline_version, 8);
    assert.equal(candidates?.outputs?.story_id, 9);
    assert.equal(candidates?.outputs?.episode_id, 19);
    assert.equal(candidates?.outputs?.clip_id, "clip-8");
    assert.deepEqual(collectProductionCanvasContext(nodes), {
      virtual_ip_id: 84,
      environment_id: 13,
      story_id: 9,
      episode_id: 19,
      script_id: 130,
      timeline_id: 71,
      timeline_version: 7,
      clip_id: "clip-9",
      reference_artifacts: [
        "virtual_ip_image:84:148",
        "environment_images:13:1",
      ],
    });
    assert.deepEqual(candidates?.outputs?.reference_artifacts, [
      "virtual_ip_image:84:148",
      "environment_images:13:1",
    ]);

    const retrying = applyProductionCanvasContext(
      nodes.map((node) =>
        node.id === "skill-virtual-ip-image" ||
        node.id === "skill-environment-image"
          ? {
              ...node,
              status: "running",
              outputs: { ...node.outputs, task_status: "pending" },
            }
          : node,
      ),
    );
    assert.equal(
      retrying.find((node) => node.skill === "image.candidates")?.outputs
        ?.reference_artifacts,
      undefined,
    );
  });

  it("does not promote historical task evidence over global context", () => {
    const nodes: ProductionCanvasNode[] = [
      {
        id: "placed-clip",
        label: "Placed clip",
        title: "旧分镜",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        skill: "video.candidates",
        outputs: {
          script_id: 300,
          timeline_id: 501,
          timeline_version: 7,
          placed_timeline_clip_id: "clip-old",
          frame_indexes: [0],
        },
      },
      {
        id: "script-task-200",
        kind: "note",
        label: "Task #200",
        title: "新剧本任务",
        status: "review",
        x: 240,
        y: 0,
        width: 220,
        outputs: {
          task_id: 200,
          task_status: "completed",
          script_id: 301,
        },
      },
    ];
    const expected = {};
    assert.deepEqual(collectProductionCanvasContext(nodes), expected);
    assert.deepEqual(
      collectProductionCanvasContext(applyProductionCanvasContext(nodes)),
      expected,
    );
  });

  it("does not reuse a reference artifact from a different IP branch", () => {
    const nodes = applyProductionCanvasContext([
      {
        id: "old-ip-reference",
        label: "Virtual IP Image",
        title: "旧 IP 角色图",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        skill: "virtual_ip.image",
        outputs: {
          virtual_ip_ids: [84],
          task_status: "completed",
          result_file_path: "virtual_ip_image:84:148",
        },
      },
      {
        id: "current-context",
        label: "Report",
        title: "当前 IP 主链",
        status: "ready",
        x: 240,
        y: 0,
        width: 220,
        skill: "report.summarize",
        outputs: { virtual_ip_ids: [85], story_id: 10 },
      },
      {
        id: "image-candidates",
        label: "Image Candidates",
        title: "生成当前 IP 分镜",
        status: "blocked",
        x: 480,
        y: 0,
        width: 220,
        skill: "image.candidates",
        outputs: { required_inputs: ["reference_artifacts"] },
      },
    ]);

    const candidates = nodes.find((node) => node.id === "image-candidates");
    assert.equal(candidates?.status, "blocked");
    assert.deepEqual(candidates?.outputs?.required_inputs, [
      "reference_artifacts",
    ]);
    assert.equal(candidates?.outputs?.reference_artifacts, undefined);
  });

  it("does not derive global context from frame-scoped media node order", () => {
    const globalNode: ProductionCanvasNode = {
      id: "render",
      label: "Render",
      title: "全局成片",
      status: "ready",
      x: 0,
      y: 0,
      width: 220,
      skill: "timeline.render",
      outputs: {
        script_id: 301,
        timeline_id: 502,
        timeline_version: 3,
        clip_id: "clip-global",
      },
    };
    const scoped = (id: string, clipId: string): ProductionCanvasNode => ({
      id,
      label: "Video",
      title: id,
      status: "review",
      x: 0,
      y: 0,
      width: 220,
      skill: "video.candidates",
      outputs: {
        frame_indexes: [id === "video-a" ? 0 : 1],
        script_id: 140,
        timeline_id: 501,
        timeline_version: 1,
        clip_id: clipId,
      },
    });
    const videoA = scoped("video-a", "clip-a");
    const videoB = scoped("video-b", "clip-b");
    const expected = {
      script_id: 301,
      timeline_id: 502,
      timeline_version: 3,
      clip_id: "clip-global",
    };

    assert.deepEqual(
      collectProductionCanvasContext([globalNode, videoA, videoB]),
      expected,
    );
    assert.deepEqual(
      collectProductionCanvasContext([globalNode, videoB, videoA]),
      expected,
    );
  });

  it("does not infer global Timeline state from placed scoped nodes", () => {
    const placed = (
      id: string,
      version: number,
      clipId: string,
    ): ProductionCanvasNode => ({
      id,
      label: "Video",
      title: id,
      status: "approved",
      x: 0,
      y: 0,
      width: 220,
      skill: "video.candidates",
      outputs: {
        frame_indexes: [version],
        script_id: 301,
        timeline_id: 502,
        timeline_version: version,
        clip_id: clipId,
        placed_timeline_clip_id: clipId,
      },
    });
    const videoA = placed("video-a", 2, "clip-a");
    const videoB = placed("video-b", 3, "clip-b");
    const expected = {};

    assert.deepEqual(
      collectProductionCanvasContext([videoA, videoB]),
      expected,
    );
    assert.deepEqual(
      collectProductionCanvasContext([videoB, videoA]),
      expected,
    );
  });

  it("does not compare placed versions across different Timelines", () => {
    const node = (
      id: string,
      scriptId: number,
      timelineId: number,
      version: number,
      clipId: string,
      scoped = true,
    ): ProductionCanvasNode => ({
      id,
      label: "Video",
      title: id,
      status: "approved",
      x: 0,
      y: 0,
      width: 220,
      skill: scoped ? "video.candidates" : "timeline.render",
      outputs: {
        ...(scoped ? { frame_indexes: [version] } : {}),
        script_id: scriptId,
        timeline_id: timelineId,
        timeline_version: version,
        clip_id: clipId,
        ...(scoped ? { placed_timeline_clip_id: clipId } : {}),
      },
    });
    const global = node("render", 302, 600, 1, "clip-new", false);
    const oldPlaced = node("old", 301, 502, 9, "clip-old");
    const currentPlaced = node("current", 302, 600, 1, "clip-new");
    const expected = {
      script_id: 302,
      timeline_id: 600,
      timeline_version: 1,
      clip_id: "clip-new",
    };

    assert.deepEqual(
      collectProductionCanvasContext([global, oldPlaced, currentPlaced]),
      expected,
    );
    assert.deepEqual(
      collectProductionCanvasContext([global, currentPlaced, oldPlaced]),
      expected,
    );
  });

  it("dedupes restored canvas nodes by id", () => {
    const state = createProductionCanvasState();
    const restored = createProductionCanvasState([
      state.nodes[0]!,
      { ...state.nodes[0]!, title: "Duplicate brief" },
      state.nodes[1]!,
    ]);

    assert.deepEqual(
      restored.nodes.map((node) => node.id),
      [state.nodes[0]!.id, state.nodes[1]!.id],
    );
    assert.equal(restored.nodes[0]?.title, state.nodes[0]?.title);
  });

  it("normalizes restored canvas node dimensions", () => {
    const state = createProductionCanvasState();
    const restored = createProductionCanvasState([
      { ...state.nodes[0]!, width: 0, height: -12 },
    ]);

    assert.equal(restored.nodes[0]?.width, 190);
    assert.equal(restored.nodes[0]?.height, undefined);
    assert.equal(
      displayProductionCanvasNodeTitle({
        ...state.nodes[0]!,
        kind: "note",
        title: " ",
      }),
      "未命名便签",
    );
  });

  it("updates reusable canvas state for drag, zoom, and notes", () => {
    const state = createProductionCanvasState();
    const defaultTimeline = state.nodes.find((node) => node.id === "timeline");
    const movedNodes = moveProductionCanvasNode(state.nodes, "script", 24, -12);
    const movedScript = movedNodes.find((node) => node.id === "script");
    const report = state.nodes.find((node) => node.id === "report");

    assert.equal(defaultTimeline?.status, "blocked");
    assert.equal(movedScript?.x, 294);
    assert.equal(movedScript?.y, 52);
    assert.deepEqual(
      createProductionCanvasState(state.nodes, [
        { from: "brief", to: "script" },
        { from: "brief", to: "script" },
        { from: "brief", to: "brief" },
        { from: "brief", to: "missing-node" },
      ]).edges,
      [{ from: "brief", to: "script" }],
    );

    assert.equal(zoomProductionCanvas(state.viewport, 10).zoom, 1.6);
    assert.equal(zoomProductionCanvas(state.viewport, -10).zoom, 0.5);
    assert.deepEqual(
      zoomProductionCanvas(
        { x: Number.NaN, y: Number.POSITIVE_INFINITY, zoom: Number.NaN },
        1,
      ),
      { x: 0, y: 0, zoom: 1.1 },
    );

    const withNote = addProductionCanvasNote(state.nodes, 1);
    const note = withNote.find((node) => node.id === "note-1");
    const safeNote = addProductionCanvasNote(state.nodes, 1, {
      x: Number.NaN,
      y: Number.POSITIVE_INFINITY,
    }).find((node) => node.id === "note-1");

    assert.equal(note?.kind, "note");
    assert.equal(note?.label, "便签");
    assert.equal(safeNote?.x, 160);
    assert.equal(safeNote?.y, 340);
    assert.deepEqual(
      getWorldBounds([
        {
          ...state.nodes[0]!,
          height: Number.NaN,
          width: Number.NaN,
          x: Number.NaN,
          y: Number.NaN,
        },
      ]),
      { minX: 0, minY: 0, width: 1260, height: 600 },
    );
    assert.deepEqual(
      getWorldBounds([
        {
          ...state.nodes[0]!,
          height: -30,
          width: -100,
          x: 1200,
          y: 500,
        },
      ]),
      { minX: 0, minY: 0, width: 1470, height: 666 },
    );

    assert.ok(report);
    assert.deepEqual(
      centerProductionCanvasOnNode(state.viewport, report, {
        width: 1180,
        height: 520,
      }),
      { x: -495, y: -43, zoom: 1 },
    );
    assert.deepEqual(
      centerProductionCanvasOnNode({ x: 0, y: 0, zoom: 0 }, report, {
        width: 1180,
        height: 520,
      }),
      { x: 48, y: 109, zoom: 0.5 },
    );
  });
});
