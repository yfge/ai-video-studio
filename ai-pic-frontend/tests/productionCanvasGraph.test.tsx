import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { ProductionCanvasEdgeControls } from "../src/components/features/canvas/ProductionCanvasEdgeControls";
import { ProductionCanvasTaskSummary } from "../src/components/features/canvas/ProductionCanvasTaskSummary";
import {
  addProductionCanvasEdge,
  removeProductionCanvasEdge,
  removeProductionCanvasNode,
} from "../src/components/features/canvas/productionCanvasGraphState";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

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

describe("ProductionCanvasGraph", () => {
  afterEach(() => cleanup());

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
    const withoutReport = removeProductionCanvasNode(
      state.nodes,
      withEdge,
      "report",
    );
    assert.ok(!withoutReport.nodes.some((node) => node.id === "report"));
    assert.ok(
      !withoutReport.edges.some(
        (edge) => edge.from === "report" || edge.to === "report",
      ),
    );
    assert.ok(
      !removeProductionCanvasEdge(withEdge, "brief", "report").some(
        (edge) => edge.from === "brief" && edge.to === "report",
      ),
    );

    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    assert.ok(canvas);
    fireEvent.click(
      utils.getByLabelText("Image Candidates 角色、环境和关键帧候选"),
    );
    assert.ok(
      utils.container.querySelector("[data-canvas-edge='image-video']"),
    );
    fireEvent.click(
      utils.getByRole("button", {
        name: /移除 选用图片 → Video Candidates.*起始帧/,
      }),
    );
    assert.equal(
      utils.container.querySelector("[data-canvas-edge='image-video']"),
      null,
    );
    const select = utils.getByLabelText("连线目标") as HTMLSelectElement;
    const binding = [...select.options].find(
      (option) =>
        option.textContent?.includes("选用图片 → Video Candidates· 起始帧"),
    );
    assert.ok(binding);
    fireEvent.change(select, { target: { value: binding.value } });
    fireEvent.click(utils.getByRole("button", { name: "添加连线" }));
    assert.ok(
      utils.container.querySelector("[data-canvas-edge='image-video']"),
    );
    assert.equal(dom.window.document.activeElement, canvas);
  });

  it("expands long task evidence summaries on demand", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[1, 2, 3, 4, 5].map((taskId) => ({
          id: `task-${taskId}`,
          label: `Task #${taskId}`,
          title: `任务 ${taskId}`,
          status: "review",
          x: taskId * 10,
          y: taskId * 10,
          width: 220,
          kind: "note",
          outputs: {
            task_id: taskId,
            task_status: "completed",
            task_title: `任务 ${taskId}`,
          },
        }))}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.queryByText("Task #1 · 已完成 · 任务 1"), null);
    const toggle = utils.getByRole("button", { name: "展开全部任务" });
    assert.equal(toggle.getAttribute("aria-expanded"), "false");
    assert.ok(utils.getByText("展开全部任务（还有 1 条）"));
    fireEvent.click(toggle);
    assert.ok(utils.getByText("Task #1 · 已完成 · 任务 1"));
    assert.equal(
      utils
        .getByRole("button", { name: "收起任务列表" })
        .getAttribute("aria-expanded"),
      "true",
    );
    fireEvent.click(utils.getByRole("button", { name: "收起任务列表" }));
    assert.equal(utils.queryByText("Task #1 · 已完成 · 任务 1"), null);
    assert.equal(toggle.getAttribute("aria-expanded"), "false");
  });

  it("caps expanded task evidence summaries to recent tasks", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={Array.from({ length: 25 }, (_, index) => {
          const taskId = index + 1;
          return {
            id: `task-${taskId}`,
            label: `Task #${taskId}`,
            title: `任务 ${taskId}`,
            status: "review" as const,
            x: taskId * 10,
            y: taskId * 10,
            width: 220,
            kind: "note" as const,
            outputs: {
              task_id: taskId,
              task_status: "completed",
              task_title: `任务 ${taskId}`,
            },
          };
        })}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.queryByText("Task #6 · 已完成 · 任务 6"), null);

    assert.equal(utils.queryByText("展开最近任务（还有 21 条）"), null);

    fireEvent.click(utils.getByRole("button", { name: "展开最近 20 条任务" }));

    assert.ok(utils.getByText("Task #6 · 已完成 · 任务 6"));
    assert.equal(utils.queryByText("Task #5 · 已完成 · 任务 5"), null);
    assert.equal(
      utils
        .getByRole("button", { name: "收起任务列表" })
        .getAttribute("aria-expanded"),
      "true",
    );
  });

  it("refreshes only recent task evidence on large summaries", () => {
    let refreshedIds: string[] = [];
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={Array.from({ length: 25 }, (_, index) => {
          const taskId = index + 1;
          return {
            id: `task-${taskId}`,
            label: `Task #${taskId}`,
            title: `任务 ${taskId}`,
            status: "review" as const,
            x: taskId * 10,
            y: taskId * 10,
            width: 220,
            kind: "note" as const,
            outputs: {
              task_id: taskId,
              task_status: "completed",
              task_title: `任务 ${taskId}`,
            },
          };
        })}
        onRefreshTasks={(nodes) => {
          refreshedIds = nodes.map((node) => node.id);
        }}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "刷新最近任务" }));

    assert.deepEqual(
      refreshedIds,
      Array.from({ length: 20 }, (_, index) => `task-${index + 6}`),
    );
  });

  it("announces task summary refresh failures", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[
          {
            id: "task-1",
            label: "Task #1",
            title: "任务 1",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "note",
            outputs: { task_id: 1 },
          },
        ]}
        refreshError="任务状态刷新失败"
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getByRole("alert").textContent, "任务状态刷新失败");
  });

  it("jumps status summary pills to the newest matching task", () => {
    let selectedNodeId = "";
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[1, 2, 3].map((taskId) => ({
          id: `task-${taskId}`,
          label: `Task #${taskId}`,
          title: `任务 ${taskId}`,
          status: "review",
          x: taskId * 10,
          y: taskId * 10,
          width: 220,
          kind: "note",
          outputs: {
            task_id: taskId,
            task_status: taskId === 2 ? "pending" : "completed",
            task_title: `任务 ${taskId}`,
          },
        }))}
        onSelectNode={(nodeId) => {
          selectedNodeId = nodeId;
        }}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(
      utils.getByRole("button", { name: "定位并筛选已完成任务" }),
    );

    assert.equal(selectedNodeId, "task-3");
  });

  it("filters task evidence rows from the status summary pills", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[
          {
            id: "task-1",
            label: "Task #1",
            title: "任务 1",
            status: "review",
            x: 10,
            y: 10,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 1,
              task_status: "completed",
              task_title: "任务 1",
            },
          },
          {
            id: "task-2",
            label: "Task #2",
            title: "任务 2",
            status: "review",
            x: 20,
            y: 20,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 2,
              task_status: "failed",
              task_title: "任务 2",
            },
          },
          {
            id: "task-3",
            label: "Task #3",
            title: "任务 3",
            status: "review",
            x: 30,
            y: 30,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 3,
              task_status: "pending",
              task_title: "任务 3",
            },
          },
        ]}
      />,
      { container: dom.window.document.body },
    );

    assert.match(
      utils.getByRole("button", { name: "筛选全部任务" }).className,
      /ring-blue-300/,
    );

    fireEvent.click(utils.getByRole("button", { name: "筛选异常任务" }));

    assert.doesNotMatch(
      utils.getByRole("button", { name: "筛选全部任务" }).className,
      /ring-blue-300/,
    );
    assert.match(
      utils.getByRole("button", { name: "筛选异常任务" }).className,
      /ring-blue-300/,
    );
    assert.ok(utils.getByText("Task #2 · 失败 · 任务 2"));
    assert.equal(utils.queryByText("Task #1 · 已完成 · 任务 1"), null);
    assert.equal(utils.queryByText("Task #3 · 等待中 · 任务 3"), null);
    assert.equal(utils.queryByRole("button", { name: "展开全部任务" }), null);

    fireEvent.click(utils.getByRole("button", { name: "筛选全部任务" }));

    assert.ok(utils.getByText("Task #1 · 已完成 · 任务 1"));
    assert.ok(utils.getByText("Task #3 · 等待中 · 任务 3"));
  });

  it("keeps recent-only refresh while a large summary is filtered", () => {
    let refreshedIds: string[] = [];
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={Array.from({ length: 25 }, (_, index) => {
          const taskId = index + 1;
          return {
            id: `task-${taskId}`,
            label: `Task #${taskId}`,
            title: `任务 ${taskId}`,
            status: "review" as const,
            x: taskId * 10,
            y: taskId * 10,
            width: 220,
            kind: "note" as const,
            outputs: {
              task_id: taskId,
              task_status: taskId === 2 ? "failed" : "completed",
              task_title: `任务 ${taskId}`,
            },
          };
        })}
        onRefreshTasks={(nodes) => {
          refreshedIds = nodes.map((node) => node.id);
        }}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "筛选异常任务" }));
    fireEvent.click(utils.getByRole("button", { name: "刷新最近任务" }));

    assert.deepEqual(
      refreshedIds,
      Array.from({ length: 20 }, (_, index) => `task-${index + 6}`),
    );
  });

  it("shows an empty state when a task summary filter has no matches", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[
          {
            id: "task-1",
            label: "Task #1",
            title: "任务 1",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 1,
              task_status: "completed",
              task_title: "任务 1",
            },
          },
        ]}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "筛选异常任务" }));

    assert.ok(utils.getByText("暂无匹配任务"));
    assert.equal(utils.queryByText("Task #1 · 已完成 · 任务 1"), null);
  });

  it("marks the task summary refresh button busy while refreshing", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[
          {
            id: "task-1",
            label: "Task #1",
            title: "任务 1",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "note",
            outputs: { task_id: 1 },
          },
        ]}
        onRefreshTasks={() => {}}
        refreshingTasks
      />,
      { container: dom.window.document.body },
    );
    const button = utils.getByRole("button", { name: "刷新全部任务" });

    assert.equal(button.getAttribute("aria-busy"), "true");
    assert.equal(button.hasAttribute("disabled"), true);
    assert.equal(button.textContent, "刷新中");
  });

  it("keeps keyboard control after refreshing task evidence from the summary", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          success: true,
          data: {
            id: 77,
            title: "任务 77",
            status: "completed",
            task_type: "canvas",
          },
        }),
        { headers: { "content-type": "application/json" } },
      ) as Promise<Response>;
    window.localStorage.setItem(
      "canvas-task-summary-focus-test",
      JSON.stringify({
        edges: [],
        nodes: [
          ...createProductionCanvasState().nodes,
          {
            id: "task-77",
            label: "Task #77",
            title: "任务 77",
            status: "review",
            x: 40,
            y: 400,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 77,
              task_status: "pending",
              task_title: "任务 77",
            },
          },
        ],
        selectedNodeId: "brief",
        viewport: { x: 0, y: 0, zoom: 1 },
      }),
    );

    try {
      const utils = render(
        <ProductionCanvasContent storageKey="canvas-task-summary-focus-test" />,
        { container: dom.window.document.body },
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const briefNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='brief']",
      );
      const refreshButton = await utils.findByRole("button", {
        name: "刷新全部任务",
      });

      refreshButton.focus();
      fireEvent.click(refreshButton);

      assert.equal(dom.window.document.activeElement, canvas);
      assert.ok(briefNode);
      fireEvent.keyDown(canvas!, { key: "ArrowRight" });
      assert.equal(briefNode.style.left, "56px");
    } finally {
      globalThis.fetch = originalFetch;
      window.localStorage.removeItem("canvas-task-summary-focus-test");
    }
  });

  it("keeps keyboard control after expanding task evidence from the summary", async () => {
    window.localStorage.setItem(
      "canvas-task-summary-expand-focus-test",
      JSON.stringify({
        edges: [],
        nodes: [
          ...createProductionCanvasState().nodes,
          ...[1, 2, 3, 4, 5].map((taskId) => ({
            id: `task-${taskId}`,
            label: `Task #${taskId}`,
            title: `任务 ${taskId}`,
            status: "review",
            x: taskId * 10,
            y: 400 + taskId * 10,
            width: 220,
            kind: "note",
            outputs: {
              task_id: taskId,
              task_status: "completed",
              task_title: `任务 ${taskId}`,
            },
          })),
        ],
        selectedNodeId: "brief",
        viewport: { x: 0, y: 0, zoom: 1 },
      }),
    );

    try {
      const utils = render(
        <ProductionCanvasContent storageKey="canvas-task-summary-expand-focus-test" />,
        { container: dom.window.document.body },
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const briefNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='brief']",
      );
      const expandButton = await utils.findByRole("button", {
        name: "展开全部任务",
      });

      expandButton.focus();
      fireEvent.click(expandButton);

      assert.equal(dom.window.document.activeElement, canvas);
      assert.ok(briefNode);
      fireEvent.keyDown(canvas!, { key: "ArrowRight" });
      assert.equal(briefNode.style.left, "56px");
    } finally {
      window.localStorage.removeItem("canvas-task-summary-expand-focus-test");
    }
  });

  it("keeps keyboard control after filtering task evidence from the summary", async () => {
    window.localStorage.setItem(
      "canvas-task-summary-filter-focus-test",
      JSON.stringify({
        edges: [],
        nodes: [
          ...createProductionCanvasState().nodes,
          {
            id: "task-88",
            label: "Task #88",
            title: "任务 88",
            status: "review",
            x: 40,
            y: 400,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 88,
              task_status: "completed",
              task_title: "任务 88",
            },
          },
        ],
        selectedNodeId: "brief",
        viewport: { x: 0, y: 0, zoom: 1 },
      }),
    );

    try {
      const utils = render(
        <ProductionCanvasContent storageKey="canvas-task-summary-filter-focus-test" />,
        { container: dom.window.document.body },
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const briefNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='brief']",
      );
      const filterButton = await utils.findByRole("button", {
        name: "筛选异常任务",
      });

      filterButton.focus();
      fireEvent.click(filterButton);

      assert.equal(dom.window.document.activeElement, canvas);
      assert.ok(briefNode);
      fireEvent.keyDown(canvas!, { key: "ArrowRight" });
      assert.equal(briefNode.style.left, "56px");
    } finally {
      window.localStorage.removeItem("canvas-task-summary-filter-focus-test");
    }
  });

  it("disables target selection when every node already has an edge", () => {
    const state = createProductionCanvasState();
    const node = state.nodes.find((item) => item.id === "brief");
    assert.ok(node);
    const edges = state.nodes
      .filter((item) => item.id !== node.id)
      .map((item) => ({ from: node.id, to: item.id }));

    const utils = render(
      <ProductionCanvasEdgeControls
        edges={edges}
        node={node}
        nodes={state.nodes}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    const select = utils.getByLabelText("连线目标") as HTMLSelectElement;
    assert.equal(select.disabled, true);
    assert.equal(select.options[0]?.textContent, "没有兼容端口");
    assert.equal(
      utils.getByRole("button", { name: "添加连线" }).hasAttribute("disabled"),
      true,
    );
  });

  it("keeps task evidence nodes out of edge targets", () => {
    const source = {
      id: "source",
      label: "Source",
      title: "Source",
      status: "review" as const,
      x: 0,
      y: 0,
      width: 220,
    };
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[]}
        node={source}
        nodes={[
          source,
          {
            id: "manual-note",
            label: "Manual Note",
            title: "Manual Note",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "note",
          },
          {
            id: "task-77",
            label: "Task #77",
            title: "Task evidence",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "note",
            outputs: { task_id: 77 },
          },
          {
            id: "report",
            label: "Report Skill",
            title: "Report Skill",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "skill_result",
            outputs: { canvas_task_id: 77 },
          },
        ]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    const optionLabels = [
      ...utils.getByLabelText("连线目标").querySelectorAll("option"),
    ].map((option) => option.textContent);

    assert.equal(
      optionLabels.some((label) => label?.includes("Manual Note")),
      false,
    );
    assert.ok(optionLabels.some((label) => label?.includes("Report Skill")));
    assert.equal(
      optionLabels.some((label) => label?.includes("Task #77")),
      false,
    );
  });

  it("disambiguates duplicate edge target labels", () => {
    const source = {
      id: "source",
      label: "Source",
      title: "Source",
      status: "review" as const,
      x: 0,
      y: 0,
      width: 220,
    };
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[]}
        node={source}
        nodes={[
          source,
          {
            id: "pipeline-image",
            label: "Image Candidates",
            title: "角色、环境和关键帧候选",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
          },
          {
            id: "skill-image",
            label: "Image Candidates",
            title: "Create or reuse storyboard/keyframe image candidates.",
            status: "blocked",
            x: 0,
            y: 0,
            width: 220,
            kind: "skill_result",
          },
          {
            id: "video",
            label: "Video Candidates",
            title: "图生视频",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
          },
        ]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    const optionLabels = [
      ...utils.getByLabelText("连线目标").querySelectorAll("option"),
    ].map((option) => option.textContent);

    assert.deepEqual(optionLabels, [
      "选择兼容端口",
      "输出 → Image Candidates · 角色、环境和关键帧候选· 输入",
      "输出 → Image Candidates · Create or reuse storyboard/keyframe image candidates.· 输入",
      "输出 → Video Candidates· 输入",
    ]);
  });

  it("disambiguates duplicate outgoing edge labels", () => {
    const source = {
      id: "source",
      label: "Source",
      title: "Source",
      status: "review" as const,
      x: 0,
      y: 0,
      width: 220,
    };
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[
          { from: "source", to: "pipeline-image" },
          { from: "source", to: "skill-image" },
        ]}
        node={source}
        nodes={[
          source,
          {
            id: "pipeline-image",
            label: "Image Candidates",
            title: "角色、环境和关键帧候选",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
          },
          {
            id: "skill-image",
            label: "Image Candidates",
            title: "Create or reuse storyboard/keyframe image candidates.",
            status: "blocked",
            x: 0,
            y: 0,
            width: 220,
            kind: "skill_result",
          },
        ]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(
      utils.getByRole("button", {
        name: "移除 默认 → Image Candidates · 角色、环境和关键帧候选· 默认",
      }),
    );
    assert.ok(
      utils.getByRole("button", {
        name: "移除 默认 → Image Candidates · Create or reuse storyboard/keyframe image candidates.· 默认",
      }),
    );
  });

  it("hides edge controls for task evidence nodes", () => {
    const taskNode = {
      id: "task-77",
      label: "Task #77",
      title: "Task evidence",
      status: "review" as const,
      x: 0,
      y: 0,
      width: 220,
      kind: "note" as const,
      outputs: { task_id: 77 },
    };
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[]}
        node={taskNode}
        nodes={[
          taskNode,
          {
            id: "report",
            label: "Report Skill",
            title: "Report Skill",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
          },
        ]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.queryByText("连线编辑"), null);
  });

  it("shows an empty state when the selected node has no outgoing edges", () => {
    const state = createProductionCanvasState();
    const node = state.nodes.find((item) => item.id === "report");
    assert.ok(node);
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={state.edges.filter((edge) => edge.from !== node.id)}
        node={node}
        nodes={state.nodes}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("暂无连线"));
    assert.equal(utils.queryByRole("button", { name: /移除连线/ }), null);
  });
});
