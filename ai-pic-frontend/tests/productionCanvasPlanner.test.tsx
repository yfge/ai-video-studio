import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import {
  installAutoSkillFetch,
  installMediaPlannerFetch,
} from "./productionCanvasPlannerAutoFixtures";
import { installCanvasPlanExecutionFetch } from "./productionCanvasPlannerExecutionFixture";
import {
  jsonResponse,
  parseRequestBody,
  skillNode,
  taskData,
  type FetchInit,
  type FetchInput,
} from "./productionCanvasPlannerFetchCommon";

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

describe("ProductionCanvasPlanner", () => {
  afterEach(() => cleanup());

  it("creates dynamic canvas nodes from a chat skill execution result", async () => {
    const fetchStub = installCanvasPlanExecutionFetch();

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
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

      await waitFor(() =>
        assert.ok(utils.getAllByText("Asset Selection").length >= 1),
      );
      assert.equal(fetchStub.planRequests[0]?.episode_id, 123);
      assert.equal(fetchStub.planRequests[0]?.task_id, 44);
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

      await waitFor(() =>
        assert.equal(fetchStub.executeRequests.length >= 1, true),
      );
      assert.equal(fetchStub.executeRequests[0]?.skill, "script.generate");
      assert.equal(fetchStub.executeRequests[0]?.episode_id, 123);
      assert.equal(fetchStub.executeRequests[0]?.task_id, 44);
      assert.equal(fetchStub.executeRequests[0]?.run_id, "canvas-run-123");
      assert.ok(utils.getByLabelText("Task #77 已提交现有剧本生成任务"));
      fireEvent.click(utils.getByLabelText("Task #77 已提交现有剧本生成任务"));
      assert.equal(
        utils
          .getByLabelText("Task #77 已提交现有剧本生成任务")
          .getAttribute("aria-pressed"),
        "true",
      );
      assert.ok(
        utils
          .getAllByRole("link", { name: "查看任务" })
          .some((link) => link.getAttribute("href") === "/tasks?task_id=77"),
      );
      fireEvent.click(utils.getByRole("button", { name: "刷新任务状态" }));
      await waitFor(() => assert.equal(fetchStub.taskRequests.length, 1));
      await waitFor(() => assert.ok(utils.getByText("task_status: completed")));
      assert.ok(utils.getByText("task_title: 剧本生成已完成"));
      assert.ok(utils.getByText("任务 #77 当前状态 已完成；进度：100%"));
      assert.ok(utils.getByText("任务证据"));
      assert.ok(
        Number(
          utils.container
            .querySelector("[data-canvas-task-summary='true']")
            ?.getAttribute("data-completed-tasks"),
        ) >= 1,
      );
      fireEvent.click(
        utils.getByLabelText("Asset Selection 已选择林妹妹和共享办公区"),
      );
      assert.ok(utils.getByText("candidate_environment_ids: 2"));
      assert.equal(
        utils.getByRole("link", { name: "查看任务 77" }).getAttribute("href"),
        "/tasks?task_id=77",
      );
      fireEvent.click(
        utils.getByRole("button", { name: "定位并筛选已完成任务" }),
      );
      await waitFor(() =>
        assert.equal(
          utils
            .getByLabelText("Task #44 已汇总现有任务证据")
            .getAttribute("aria-pressed"),
          "true",
        ),
      );
      fireEvent.click(utils.getByRole("button", { name: "筛选全部任务" }));
      fireEvent.click(
        utils.getByLabelText("Asset Selection 已选择林妹妹和共享办公区"),
      );
      fireEvent.click(utils.getByRole("button", { name: "定位任务 77" }));
      await waitFor(() =>
        assert.ok(utils.getByText("task_title: 剧本生成已完成")),
      );
      assert.notEqual(
        utils.container.querySelector<HTMLElement>(
          "[data-production-canvas-world='true']",
        )?.style.transform,
        "translate(0px, 0px) scale(1)",
      );

      await waitFor(() =>
        assert.equal(fetchStub.executeRequests.length >= 2, true),
      );
      assert.equal(fetchStub.executeRequests[1]?.skill, "storyboard.plan");
      assert.equal(fetchStub.executeRequests[1]?.script_id, 321);
      assert.equal(fetchStub.executeRequests[1]?.task_id, 77);
      assert.equal(fetchStub.executeRequests[1]?.run_id, "canvas-run-123");
      assert.ok(utils.getByLabelText("Task #88 已提交现有分镜生成任务"));
      fireEvent.click(utils.getByRole("button", { name: "刷新全部任务" }));
      await waitFor(() =>
        assert.ok(
          fetchStub.taskRequests.some((url) =>
            url.includes("/api/v1/tasks/88"),
          ),
        ),
      );
      await waitFor(() =>
        assert.equal(
          utils.container
            .querySelector("[data-canvas-task-summary='true']")
            ?.getAttribute("data-failed-tasks"),
          "1",
        ),
      );
      assert.ok(utils.getByText("Task #88 · 失败 · 分镜生成失败"));
      assert.ok(utils.getByText("错误：缺少分镜输入"));

      await waitFor(() =>
        assert.equal(fetchStub.executeRequests.length >= 3, true),
      );
      fireEvent.click(utils.getByLabelText("Report Skill 已汇总现有任务证据"));
      await waitFor(() =>
        assert.ok(utils.getByText("source_kind: production_canvas_run")),
      );
      assert.equal(fetchStub.executeRequests[2]?.skill, "report.summarize");
      assert.equal(fetchStub.executeRequests[2]?.task_id, 88);
      assert.equal(fetchStub.executeRequests[2]?.run_id, "canvas-run-123");
      assert.ok(utils.getByText("Task audit endpoint"));
    } finally {
      fetchStub.restore();
    }
  });

  it("automatically executes ready skill nodes after whole-canvas creation", async () => {
    const fetchStub = installAutoSkillFetch();

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于林妹妹整体创建短剧" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => assert.equal(fetchStub.executeRequests.length, 1));
      assert.equal(fetchStub.executeRequests[0]?.skill, "script.generate");
      assert.equal(fetchStub.executeRequests[0]?.run_id, "canvas-run-auto");
      assert.ok(utils.getByLabelText("Task #77 已提交现有剧本生成任务"));
    } finally {
      fetchStub.restore();
    }
  });

  it("keeps keyboard control after whole-canvas creation", async () => {
    const fetchStub = installAutoSkillFetch();

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const createButton = utils.getByRole("button", { name: "整体创建" });

      assert.ok(canvas);
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于林妹妹整体创建短剧" },
      });
      createButton.focus();
      fireEvent.click(createButton);

      await waitFor(() => assert.equal(fetchStub.executeRequests.length, 1));
      const scriptNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='skill-script-generate']",
      );

      assert.ok(scriptNode);
      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(scriptNode.style.left, "436px");
    } finally {
      fetchStub.restore();
    }
  });

  it("keeps keyboard control after copying a created run id", async () => {
    const fetchStub = installAutoSkillFetch();
    const clipboardDescriptor = Object.getOwnPropertyDescriptor(
      globalThis.navigator,
      "clipboard",
    );
    let clipboardText = "";
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: {
        writeText: async (text: string) => {
          clipboardText = text;
        },
      },
      configurable: true,
    });

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );

      assert.ok(canvas);
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于林妹妹整体创建短剧" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("Run ID") as HTMLInputElement).value,
          "canvas-run-auto",
        ),
      );
      const scriptNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='skill-script-generate']",
      );
      const copyButton = utils.getByRole("button", { name: "复制 Run ID" });

      assert.ok(scriptNode);
      copyButton.focus();
      fireEvent.click(copyButton);

      await waitFor(() => assert.equal(clipboardText, "canvas-run-auto"));
      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(scriptNode.style.left, "436px");
    } finally {
      fetchStub.restore();
      if (clipboardDescriptor) {
        Object.defineProperty(
          globalThis.navigator,
          "clipboard",
          clipboardDescriptor,
        );
      }
    }
  });

  it("paints whole-canvas creation busy before sending the plan request", async () => {
    const fetchStub = installAutoSkillFetch();

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于林妹妹整体创建短剧" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      assert.equal(fetchStub.planRequests.length, 0);
      const busyButton = utils.getByRole("button", { name: "执行中" });
      assert.equal(busyButton.getAttribute("aria-busy"), "true");
      assert.equal(busyButton.hasAttribute("disabled"), true);

      await waitFor(() => assert.equal(fetchStub.planRequests.length, 1));
    } finally {
      fetchStub.restore();
    }
  });

  it("keeps manual execution errors scoped to the failed node", async () => {
    const originalFetch = globalThis.fetch;
    const executeRequests: unknown[] = [];
    globalThis.fetch = async (input: FetchInput, init?: FetchInit) => {
      const url = String(input);
      if (url.includes("/production-canvas/execute")) {
        executeRequests.push(parseRequestBody(init));
        return Promise.resolve(
          new Response(
            JSON.stringify({ success: false, error: "手动执行失败" }),
            {
              headers: { "content-type": "application/json" },
            },
          ),
        );
      }
      return jsonResponse({
        run_id: "canvas-run-error",
        task_id: 45,
        nodes: [
          skillNode({
            id: "manual-skill",
            label: "Manual Skill",
            title: "需要手动执行的节点",
            status: "review",
            x: 420,
            y: 360,
            skill: "script.generate",
            detail: "用于验证错误只显示在当前节点。",
            outputs: {},
          }),
        ],
        selected_assets: { virtual_ips: [], environments: [] },
        skill_manifest: { version: "production_canvas.v1" },
      });
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "生成一个手动执行节点" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() =>
        assert.ok(utils.getAllByText("Manual Skill").length >= 1),
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const executeButton = utils.getByRole("button", { name: "运行节点" });

      assert.ok(canvas);
      executeButton.focus();
      fireEvent.click(executeButton);
      await waitFor(() =>
        assert.equal(utils.getByRole("alert").textContent, "手动执行失败"),
      );
      assert.equal(dom.window.document.activeElement, canvas);
      assert.equal(executeRequests.length, 1);

      const manualNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='manual-skill']",
      );
      const nodeExecuteButton = utils.getByRole("button", {
        name: "后台执行 Manual Skill",
      });

      assert.ok(manualNode);
      nodeExecuteButton.focus();
      fireEvent.click(nodeExecuteButton);
      await waitFor(() => assert.equal(executeRequests.length, 2));
      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(manualNode.style.left, "436px");

      fireEvent.click(utils.getByLabelText("Brief IP、受众、题材和单集目标"));
      assert.equal(utils.queryByRole("alert"), null);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("keeps task refresh errors scoped to the failed task node", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input: FetchInput) => {
      const url = String(input);
      if (url.includes("/api/v1/tasks/101")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({ success: false, error: "任务刷新失败" }),
            {
              headers: { "content-type": "application/json" },
            },
          ),
        );
      }
      if (url.includes("/api/v1/tasks/102")) {
        return jsonResponse(
          taskData({
            id: 102,
            progress: "100%",
            status: "completed",
            taskType: "script",
            title: "任务二完成",
            updatedAt: "2026-07-02T18:10:00Z",
          }),
        );
      }
      return jsonResponse({
        run_id: "canvas-run-task-error",
        task_id: 45,
        nodes: [
          skillNode({
            id: "task-101",
            label: "Task #101",
            title: "任务一",
            status: "review",
            x: 420,
            y: 360,
            kind: "note",
            outputs: {
              task_id: 101,
              task_status: "running",
              task_title: "任务一",
            },
          }),
          skillNode({
            id: "task-102",
            label: "Task #102",
            title: "任务二",
            status: "review",
            x: 680,
            y: 360,
            kind: "note",
            outputs: {
              task_id: 102,
              task_status: "running",
              task_title: "任务二",
            },
          }),
        ],
        selected_assets: { virtual_ips: [], environments: [] },
        skill_manifest: { version: "production_canvas.v1" },
      });
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "生成两个任务节点" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() =>
        assert.ok(utils.getAllByText("Task #101").length >= 1),
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );

      assert.ok(canvas);
      fireEvent.click(utils.getByLabelText("Task #101 任务一"));
      const refreshButton = utils.getByRole("button", { name: "刷新任务状态" });
      refreshButton.focus();
      fireEvent.click(refreshButton);
      await waitFor(() =>
        assert.deepEqual(
          utils.getAllByRole("alert").map((alert) => alert.textContent),
          ["任务刷新失败"],
        ),
      );
      assert.equal(dom.window.document.activeElement, canvas);
      await waitFor(() =>
        assert.ok(utils.getByText("任务 #101 刷新失败：任务刷新失败")),
      );
      assert.equal(
        utils.getByLabelText("Task #101 任务一").textContent?.includes("异常"),
        true,
      );

      fireEvent.click(utils.getByLabelText("Task #102 任务二"));
      assert.equal(utils.queryAllByRole("alert").length, 0);

      fireEvent.click(utils.getByRole("button", { name: "刷新全部任务" }));
      await waitFor(() =>
        assert.ok(utils.getByText("Task #102 · 已完成 · 任务二完成")),
      );
      assert.equal(utils.getByRole("alert").textContent, "任务刷新失败");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("locks other manual execute actions while a node is executing", async () => {
    const originalFetch = globalThis.fetch;
    let resolveExecute: ((response: Response) => void) | null = null;
    globalThis.fetch = async (input: FetchInput, init?: FetchInit) => {
      const url = String(input);
      if (url.includes("/production-canvas/execute")) {
        parseRequestBody(init);
        return new Promise<Response>((resolve) => {
          resolveExecute = resolve;
        });
      }
      return jsonResponse({
        run_id: "canvas-run-execute-lock",
        task_id: 45,
        nodes: [
          skillNode({
            id: "first-skill",
            label: "First Skill",
            title: "第一个手动节点",
            status: "review",
            x: 420,
            y: 360,
            skill: "script.generate",
            outputs: {},
          }),
          skillNode({
            id: "second-skill",
            label: "Second Skill",
            title: "第二个手动节点",
            status: "review",
            x: 680,
            y: 360,
            skill: "storyboard.plan",
            outputs: {},
          }),
        ],
        selected_assets: { virtual_ips: [], environments: [] },
        skill_manifest: { version: "production_canvas.v1" },
      });
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "生成两个手动执行节点" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() =>
        assert.ok(utils.getByRole("button", { name: "后台执行 First Skill" })),
      );
      fireEvent.click(
        utils.getByRole("button", { name: "后台执行 First Skill" }),
      );
      await waitFor(() =>
        assert.equal(
          utils
            .getByRole("button", { name: "执行中 First Skill" })
            .getAttribute("aria-busy"),
          "true",
        ),
      );
      assert.equal(
        utils
          .getByRole("button", { name: "后台执行 Second Skill" })
          .hasAttribute("disabled"),
        true,
      );

      fireEvent.click(utils.getByLabelText("Second Skill 第二个手动节点"));
      assert.equal(
        utils
          .getByRole("button", { name: "运行节点" })
          .hasAttribute("disabled"),
        true,
      );
    } finally {
      resolveExecute?.(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              skill_result: {
                label: "First Skill",
                title: "第一个手动节点",
                status: "review",
                detail: "done",
                outputs: {},
                reuse_targets: [],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ),
      );
      globalThis.fetch = originalFetch;
    }
  });

  it("locks other task refresh actions while a task is syncing", async () => {
    const originalFetch = globalThis.fetch;
    let resolveTaskRefresh: ((response: Response) => void) | null = null;
    globalThis.fetch = async (input: FetchInput) => {
      const url = String(input);
      if (url.includes("/api/v1/tasks/101")) {
        return new Promise<Response>((resolve) => {
          resolveTaskRefresh = resolve;
        });
      }
      return jsonResponse({
        run_id: "canvas-run-task-lock",
        task_id: 45,
        nodes: [
          skillNode({
            id: "task-101",
            label: "Task #101",
            title: "任务一",
            status: "review",
            x: 420,
            y: 360,
            kind: "note",
            outputs: {
              task_id: 101,
              task_status: "running",
              task_title: "任务一",
            },
          }),
          skillNode({
            id: "task-102",
            label: "Task #102",
            title: "任务二",
            status: "review",
            x: 680,
            y: 360,
            kind: "note",
            outputs: {
              task_id: 102,
              task_status: "running",
              task_title: "任务二",
            },
          }),
        ],
        selected_assets: { virtual_ips: [], environments: [] },
        skill_manifest: { version: "production_canvas.v1" },
      });
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "生成两个可刷新的任务节点" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() =>
        assert.ok(utils.getAllByText("Task #101").length >= 1),
      );
      fireEvent.click(utils.getByLabelText("Task #101 任务一"));
      fireEvent.click(utils.getByRole("button", { name: "刷新任务状态" }));
      await waitFor(() =>
        assert.equal(
          utils
            .getByRole("button", { name: "刷新中" })
            .getAttribute("aria-busy"),
          "true",
        ),
      );
      assert.equal(
        utils
          .getByRole("button", { name: "刷新全部任务" })
          .hasAttribute("disabled"),
        true,
      );

      fireEvent.click(utils.getByLabelText("Task #102 任务二"));
      assert.equal(
        utils
          .getByRole("button", { name: "刷新任务状态" })
          .hasAttribute("disabled"),
        true,
      );
    } finally {
      resolveTaskRefresh?.(
        new Response(
          JSON.stringify({
            success: true,
            data: taskData({
              id: 101,
              progress: "100%",
              status: "completed",
              taskType: "script",
              title: "任务一完成",
              updatedAt: "2026-07-02T18:40:00Z",
            }),
          }),
          { headers: { "content-type": "application/json" } },
        ),
      );
      globalThis.fetch = originalFetch;
    }
  });

  it("automatically executes ready image and video candidate nodes", async () => {
    const fetchStub = installMediaPlannerFetch();

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );

      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "基于已有分镜整体生成图片和视频候选" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => assert.equal(fetchStub.executeRequests.length, 2));
      assert.deepEqual(
        fetchStub.executeRequests.map((request) => request.skill),
        ["image.candidates", "video.candidates"],
      );
      assert.equal(fetchStub.executeRequests[0]?.script_id, 321);
      assert.deepEqual(fetchStub.executeRequests[0]?.frame_indexes, [1]);
      assert.equal(fetchStub.executeRequests[0]?.run_id, "canvas-run-media");
      assert.ok(utils.getByLabelText("Task #91 已提交现有分镜图片候选任务"));
      assert.ok(utils.getByLabelText("Task #92 已提交现有分镜视频候选任务"));
    } finally {
      fetchStub.restore();
    }
  });
});
