import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { CanvasInspector } from "../src/components/features/canvas/ProductionCanvasElements";
import { CanvasNodeCard } from "../src/components/features/canvas/ProductionCanvasNodeCard";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const skillNode: ProductionCanvasNode = {
  id: "skill-1",
  label: "Script",
  title: "生成剧本",
  status: "running",
  x: 0,
  y: 0,
  width: 220,
  kind: "skill_result",
  skill: "script.generate",
};

describe("ProductionCanvasBusyActions", () => {
  afterEach(() => cleanup());

  it("marks inspector execute and refresh actions busy", () => {
    const utils = render(
      <CanvasInspector node={skillNode} executingNodeId="skill-1" />,
      { container: dom.window.document.body },
    );

    assert.equal(
      utils
        .getByRole("button", { name: "节点执行中" })
        .getAttribute("aria-busy"),
      "true",
    );
    assert.equal(
      utils
        .getByRole("button", { name: "下游执行中" })
        .getAttribute("aria-busy"),
      "true",
    );

    utils.rerender(
      <CanvasInspector
        node={{
          ...skillNode,
          id: "task-1",
          kind: "note",
          outputs: { task_id: 7 },
          skill: undefined,
        }}
        taskSyncingNodeId="task-1"
      />,
    );

    assert.equal(
      utils.getByRole("button", { name: "刷新中" }).getAttribute("aria-busy"),
      "true",
    );
  });

  it("announces inspector action failures", () => {
    const utils = render(
      <CanvasInspector node={skillNode} executionError="后台执行失败" />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getByRole("alert").textContent, "后台执行失败");

    utils.rerender(
      <CanvasInspector
        node={{
          ...skillNode,
          id: "task-1",
          kind: "note",
          outputs: { task_id: 7 },
          skill: undefined,
        }}
        taskSyncError="任务刷新失败"
      />,
    );

    assert.equal(utils.getByRole("alert").textContent, "任务刷新失败");
  });

  it("marks node-card execution busy", () => {
    const utils = render(
      <CanvasNodeCard
        executing
        node={skillNode}
        selected={false}
        onExecuteNode={() => {}}
        onPointerDown={() => {}}
        onSelect={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(
      utils
        .getByRole("button", { name: "执行中 Script" })
        .getAttribute("aria-busy"),
      "true",
    );
  });

  it("shows task status on task evidence cards and inspector", () => {
    const taskNode: ProductionCanvasNode = {
      id: "task-7",
      label: "Task #7",
      title: "生成剧本任务",
      status: "review",
      x: 0,
      y: 0,
      width: 220,
      kind: "note",
      outputs: { task_id: 7, task_status: "completed" },
    };

    const utils = render(
      <CanvasNodeCard
        node={taskNode}
        selected={false}
        onPointerDown={() => {}}
        onSelect={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("已完成"));
    assert.equal(utils.queryByText("待选择"), null);

    utils.rerender(<CanvasInspector node={taskNode} />);

    assert.ok(utils.getByText("已完成"));
    assert.equal(utils.queryByText("待选择"), null);
  });
});
