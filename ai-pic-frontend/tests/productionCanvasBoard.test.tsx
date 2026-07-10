import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { productionNavItems } from "../src/components/shared/operator/OperatorShell";
import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import {
  addProductionCanvasEdge,
  removeProductionCanvasEdge,
} from "../src/components/features/canvas/productionCanvasGraphState";
import {
  addProductionCanvasNote,
  createProductionCanvasState,
  moveProductionCanvasNode,
  zoomProductionCanvas,
} from "../src/components/features/canvas/productionCanvasState";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvasBoard", () => {
  afterEach(() => cleanup());

  it("adds the creative canvas as a first-class production navigation entry", () => {
    const canvasIndex = productionNavItems.findIndex(
      (item) => item.href === "/canvas",
    );

    assert.equal(productionNavItems[canvasIndex]?.label, "创作画布");
    assert.equal(productionNavItems[canvasIndex]?.icon, "canvas");
    assert.equal(
      productionNavItems[canvasIndex - 1]?.href,
      "/",
      "canvas entry should sit immediately after the workbench",
    );
  });

  it("renders the short-drama production chain on an interactive canvas", () => {
    const utils = render(<ProductionCanvasContent />, {
      container: dom.window.document.body,
    });

    assert.ok(utils.getByText("短剧生产链路"));
    assert.ok(
      utils.getByText(
        "Brief -> Script -> Audio + Timeline -> Storyboard Support -> Image Candidates -> Video Candidates -> Render -> Export -> Report",
      ),
    );

    for (const label of [
      "Brief",
      "Script",
      "Storyboard",
      "Image Candidates",
      "Video Candidates",
      "Timeline",
      "Report",
    ]) {
      assert.ok(utils.getAllByText(label).length >= 1);
    }

    const canvas = utils.container.querySelector(
      "[data-production-canvas='infinite-canvas']",
    );
    assert.ok(canvas);
    assert.match(canvas.className, /touch-none/);
    assert.ok(utils.getByRole("button", { name: "添加便签" }));
    assert.ok(utils.getByRole("button", { name: "适配" }));
    assert.ok(utils.getByText("100%"));
  });

  it("selects a node and exposes its details in the inspector", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    utils.getByLabelText("Script 短剧节拍、对白和质量门禁").click();

    assert.ok(utils.getByText("节点详情"));
    assert.ok(utils.getAllByText("Script").length >= 1);
    assert.ok(utils.getByText("短剧节拍、对白和质量门禁"));
  });

  it("updates reusable canvas state for drag, zoom, and notes", () => {
    const state = createProductionCanvasState();
    const defaultTimeline = state.nodes.find((node) => node.id === "timeline");
    const movedNodes = moveProductionCanvasNode(state.nodes, "script", 24, -12);
    const movedScript = movedNodes.find((node) => node.id === "script");

    assert.equal(defaultTimeline?.status, "blocked");
    assert.equal(movedScript?.x, 294);
    assert.equal(movedScript?.y, 52);

    assert.equal(zoomProductionCanvas(state.viewport, 10).zoom, 1.6);
    assert.equal(zoomProductionCanvas(state.viewport, -10).zoom, 0.5);

    const withNote = addProductionCanvasNote(state.nodes, 1);
    const note = withNote.find((node) => node.id === "note-1");

    assert.equal(note?.kind, "note");
    assert.equal(note?.label, "便签");
  });

  it("edits dynamic canvas edges from the selected node", () => {
    const state = createProductionCanvasState();
    const withEdge = addProductionCanvasEdge(state.edges, "brief", "report");

    assert.ok(
      withEdge.some((edge) => edge.from === "brief" && edge.to === "report"),
    );
    assert.equal(
      addProductionCanvasEdge(withEdge, "brief", "report").length,
      withEdge.length,
    );
    assert.equal(
      addProductionCanvasEdge(withEdge, "brief", "brief").length,
      withEdge.length,
    );
    assert.ok(
      !removeProductionCanvasEdge(withEdge, "brief", "report").some(
        (edge) => edge.from === "brief" && edge.to === "report",
      ),
    );

    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    assert.equal(
      utils.container.querySelector("[data-canvas-edge='brief-report']"),
      null,
    );

    fireEvent.change(utils.getByLabelText("连线目标"), {
      target: { value: "report" },
    });
    fireEvent.click(utils.getByRole("button", { name: "添加连线" }));

    assert.ok(
      utils.container.querySelector("[data-canvas-edge='brief-report']"),
    );
    fireEvent.click(utils.getByRole("button", { name: "移除连线 Report" }));
    assert.equal(
      utils.container.querySelector("[data-canvas-edge='brief-report']"),
      null,
    );
  });

  it("creates dynamic canvas nodes from a chat skill execution result", async () => {
    const originalFetch = globalThis.fetch;
    const planRequests: Record<string, unknown>[] = [];
    const executeRequests: Record<string, unknown>[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/execute")) {
        const executeRequest = JSON.parse(String(init?.body));
        executeRequests.push(executeRequest);
        if (executeRequest.skill === "report.summarize") {
          return new Response(
            JSON.stringify({
              success: true,
              data: {
                task_id: 44,
                task_status: "completed",
                skill_result: {
                  skill: "report.summarize",
                  label: "Report Skill",
                  title: "已汇总现有任务证据",
                  status: "review",
                  detail:
                    "任务 #44《生产画布整体创建》当前状态 completed；可继续在任务页检查参数。",
                  outputs: {
                    task_id: 44,
                    task_type: "text_generation",
                    task_status: "completed",
                    source_kind: "production_canvas_run",
                    canvas_run_id: "canvas-run-123",
                  },
                  reuse_targets: [
                    {
                      kind: "api",
                      label: "Task audit endpoint",
                      target: "app.api.v1.endpoints.tasks",
                    },
                  ],
                },
              },
            }),
            { headers: { "content-type": "application/json" } },
          ) as Promise<Response>;
        }
        if (executeRequest.skill === "storyboard.plan") {
          return new Response(
            JSON.stringify({
              success: true,
              data: {
                task_id: 88,
                task_status: "pending",
                skill_result: {
                  skill: "storyboard.plan",
                  label: "Storyboard Skill",
                  title: "已提交现有分镜生成任务",
                  status: "running",
                  detail:
                    "后台已通过现有 STORYBOARD_GENERATION Celery worker 执行。",
                  outputs: {
                    script_id: 321,
                    dispatched_task_id: 88,
                    task_status: "pending",
                    canvas_run_id: "canvas-run-123",
                  },
                  reuse_targets: [
                    {
                      kind: "worker",
                      label: "Storyboard Celery worker",
                      target:
                        "app.services.task_worker.storyboard_generate_task",
                    },
                  ],
                },
              },
            }),
            { headers: { "content-type": "application/json" } },
          ) as Promise<Response>;
        }
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              task_id: 77,
              task_status: "pending",
              skill_result: {
                skill: "script.generate",
                label: "Script Skill",
                title: "已提交现有剧本生成任务",
                status: "running",
                detail: "后台已通过现有 SCRIPT_GENERATION Celery worker 执行。",
                outputs: {
                  episode_id: 123,
                  script_id: 321,
                  dispatched_task_id: 77,
                  task_status: "pending",
                  canvas_run_id: "canvas-run-123",
                },
                reuse_targets: [
                  {
                    kind: "worker",
                    label: "Script Celery worker",
                    target: "app.services.task_worker.script_generate_task",
                  },
                ],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      const planRequest = JSON.parse(String(init?.body));
      planRequests.push(planRequest);
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            run_id: "canvas-run-123",
            task_id: 44,
            nodes: [
              {
                id: "skill-assets",
                label: "Asset Selection",
                title: "已选择林妹妹和共享办公区",
                status: "review",
                x: 160,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "asset.select",
                detail: "复用现有 IP：林妹妹；环境：共享办公区",
                outputs: {
                  virtual_ip_ids: [1],
                  environment_ids: [2],
                  candidate_environment_ids: [2],
                },
                reuse_targets: [
                  {
                    kind: "repository",
                    label: "Environment repository",
                    target:
                      "app.repositories.environment_repository.EnvironmentRepository",
                  },
                ],
              },
              {
                id: "skill-script-generate",
                label: "Script Skill",
                title: "现有剧本生成入口已就绪",
                status: "ready",
                x: 420,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "script.generate",
                detail: "后台复用现有剧本生成队列。",
                outputs: {
                  episode_id: 123,
                },
                reuse_targets: [
                  {
                    kind: "api",
                    label: "Script async endpoint",
                    target:
                      "app.api.v1.endpoints.scripts_generation_queue.generate_script_async",
                  },
                ],
              },
              {
                id: "skill-storyboard-plan",
                label: "Storyboard Skill",
                title: "现有分镜生成入口已就绪",
                status: "ready",
                x: 680,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "storyboard.plan",
                detail: "需要先补齐执行上下文，之后才会调用现有生成 worker。",
                outputs: {
                  required_inputs: ["script_id"],
                },
                reuse_targets: [
                  {
                    kind: "worker",
                    label: "Storyboard task processor",
                    target:
                      "app.api.v1.endpoints.storyboard.task_processors._process_storyboard_generation_task",
                  },
                ],
              },
              {
                id: "skill-report-summarize",
                label: "Report Skill",
                title: "等待汇总画布执行证据",
                status: "blocked",
                x: 960,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "report.summarize",
                detail: "需要 task_id 后汇总任务证据。",
                outputs: {
                  required_inputs: ["task_id"],
                },
                reuse_targets: [
                  {
                    kind: "api",
                    label: "Task audit endpoint",
                    target: "app.api.v1.endpoints.tasks",
                  },
                ],
              },
            ],
            selected_assets: {
              virtual_ips: [{ id: 1, name: "林妹妹" }],
              environments: [{ id: 2, name: "共享办公区" }],
            },
            skill_manifest: { version: "production_canvas.v1" },
          },
        }),
        { headers: { "content-type": "application/json" } },
      ) as Promise<Response>;
    };

    try {
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });

      const promptInput = utils.getByLabelText("生产目标");
      fireEvent.input(promptInput, {
        target: { value: "基于林妹妹做第 4 集，办公室轻喜剧" },
      });
      fireEvent.input(utils.getByLabelText("剧集 ID"), {
        target: { value: "123" },
      });
      fireEvent.input(utils.getByLabelText("任务 ID"), {
        target: { value: "44" },
      });
      await waitFor(() =>
        assert.equal(
          utils
            .getByRole("button", { name: "整体创建" })
            .hasAttribute("disabled"),
          false,
        ),
      );
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => {
        assert.ok(utils.getAllByText("Asset Selection").length >= 1);
      });
      assert.equal(planRequests[0]?.episode_id, 123);
      assert.equal(planRequests[0]?.task_id, 44);
      assert.ok(utils.getAllByText("已选择林妹妹和共享办公区").length >= 1);
      fireEvent.click(
        utils.getByLabelText("Asset Selection 已选择林妹妹和共享办公区"),
      );
      assert.ok(
        utils.getAllByText("复用现有 IP：林妹妹；环境：共享办公区").length >= 1,
      );
      assert.ok(utils.getByText("后台复用"));
      assert.ok(utils.getByText("Environment repository"));
      assert.ok(utils.getByText("candidate_environment_ids: 2"));
      assert.ok(utils.getByText("canvas_run_id: canvas-run-123"));
      assert.ok(utils.getByText("canvas_task_id: 44"));

      await waitFor(() => assert.equal(executeRequests.length >= 1, true));
      assert.equal(executeRequests[0]?.skill, "script.generate");
      assert.equal(executeRequests[0]?.episode_id, 123);
      assert.equal(executeRequests[0]?.task_id, 44);
      assert.equal(executeRequests[0]?.run_id, "canvas-run-123");
      assert.ok(utils.getByLabelText("Task #77 已提交现有剧本生成任务"));

      await waitFor(() => assert.equal(executeRequests.length >= 2, true));
      assert.equal(executeRequests[1]?.skill, "storyboard.plan");
      assert.equal(executeRequests[1]?.script_id, 321);
      assert.equal(executeRequests[1]?.task_id, 77);
      assert.equal(executeRequests[1]?.run_id, "canvas-run-123");
      assert.ok(utils.getByLabelText("Task #88 已提交现有分镜生成任务"));

      await waitFor(() => assert.equal(executeRequests.length >= 3, true));
      fireEvent.click(utils.getByLabelText("Report Skill 已汇总现有任务证据"));
      await waitFor(() =>
        assert.ok(utils.getByText("source_kind: production_canvas_run")),
      );
      assert.equal(executeRequests[2]?.skill, "report.summarize");
      assert.equal(executeRequests[2]?.task_id, 88);
      assert.equal(executeRequests[2]?.run_id, "canvas-run-123");
      assert.ok(utils.getByText("Task audit endpoint"));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("automatically executes ready skill nodes after whole-canvas creation", async () => {
    const originalFetch = globalThis.fetch;
    const executeRequests: Record<string, unknown>[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/execute")) {
        const executeRequest = JSON.parse(String(init?.body));
        executeRequests.push(executeRequest);
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              task_id: 77,
              task_status: "pending",
              skill_result: {
                skill: "script.generate",
                label: "Script Skill",
                title: "已提交现有剧本生成任务",
                status: "running",
                detail: "后台已通过现有 SCRIPT_GENERATION Celery worker 执行。",
                outputs: {
                  episode_id: 123,
                  dispatched_task_id: 77,
                  task_status: "pending",
                  canvas_run_id: "canvas-run-auto",
                },
                reuse_targets: [
                  {
                    kind: "worker",
                    label: "Script Celery worker",
                    target: "app.services.task_worker.script_generate_task",
                  },
                ],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            run_id: "canvas-run-auto",
            task_id: 44,
            nodes: [
              {
                id: "skill-script-generate",
                label: "Script Skill",
                title: "现有剧本生成入口已就绪",
                status: "ready",
                x: 420,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "script.generate",
                detail: "后台复用现有剧本生成队列。",
                outputs: { episode_id: 123 },
                reuse_targets: [
                  {
                    kind: "api",
                    label: "Script async endpoint",
                    target:
                      "app.api.v1.endpoints.scripts_generation_queue.generate_script_async",
                  },
                ],
              },
            ],
            selected_assets: { virtual_ips: [], environments: [] },
            skill_manifest: { version: "production_canvas.v1" },
          },
        }),
        { headers: { "content-type": "application/json" } },
      ) as Promise<Response>;
    };

    try {
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于林妹妹整体创建短剧" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => {
        assert.equal(executeRequests.length, 1);
      });
      assert.equal(executeRequests[0]?.skill, "script.generate");
      assert.equal(executeRequests[0]?.run_id, "canvas-run-auto");
      assert.ok(utils.getByLabelText("Task #77 已提交现有剧本生成任务"));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("automatically executes ready image and video candidate nodes", async () => {
    const originalFetch = globalThis.fetch;
    const executeRequests: Record<string, unknown>[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/execute")) {
        const executeRequest = JSON.parse(String(init?.body));
        executeRequests.push(executeRequest);
        const taskId = executeRequest.skill === "image.candidates" ? 91 : 92;
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              task_id: taskId,
              task_status: "pending",
              skill_result: {
                skill: executeRequest.skill,
                label:
                  executeRequest.skill === "image.candidates"
                    ? "Image Candidates"
                    : "Video Candidates",
                title:
                  executeRequest.skill === "image.candidates"
                    ? "已提交现有分镜图片候选任务"
                    : "已提交现有分镜视频候选任务",
                status: "running",
                detail: "后台已通过现有 worker 执行。",
                outputs: {
                  script_id: 321,
                  dispatched_task_id: taskId,
                  task_status: "pending",
                  canvas_run_id: "canvas-run-media",
                },
                reuse_targets: [],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            run_id: "canvas-run-media",
            task_id: 44,
            nodes: [
              {
                id: "skill-image-candidates",
                label: "Image Candidates",
                title: "现有分镜图片候选入口已就绪",
                status: "ready",
                x: 420,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "image.candidates",
                detail: "后台复用现有分镜图片生成队列。",
                outputs: { script_id: 321, frame_indexes: [1] },
                reuse_targets: [],
              },
              {
                id: "skill-video-candidates",
                label: "Video Candidates",
                title: "现有分镜视频候选入口已就绪",
                status: "ready",
                x: 700,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "video.candidates",
                detail: "后台复用现有分镜视频生成队列。",
                outputs: { script_id: 321, frame_indexes: [1] },
                reuse_targets: [],
              },
            ],
            selected_assets: { virtual_ips: [], environments: [] },
            skill_manifest: { version: "production_canvas.v1" },
          },
        }),
        { headers: { "content-type": "application/json" } },
      ) as Promise<Response>;
    };

    try {
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于已有分镜整体生成图片和视频候选" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => {
        assert.equal(executeRequests.length, 2);
      });
      assert.deepEqual(
        executeRequests.map((request) => request.skill),
        ["image.candidates", "video.candidates"],
      );
      assert.equal(executeRequests[0]?.script_id, 321);
      assert.deepEqual(executeRequests[0]?.frame_indexes, [1]);
      assert.equal(executeRequests[0]?.run_id, "canvas-run-media");
      assert.ok(utils.getByLabelText("Task #91 已提交现有分镜图片候选任务"));
      assert.ok(utils.getByLabelText("Task #92 已提交现有分镜视频候选任务"));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
