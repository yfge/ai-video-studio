import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasNodeTools } from "../src/components/features/canvas/ProductionCanvasNodeTools";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).Event = dom.window.Event;

const taskNode = {
  id: "task-node-909",
  label: "Task #909",
  title: "汇总任务",
  status: "review" as const,
  x: 0,
  y: 0,
  width: 220,
  kind: "note" as const,
  outputs: {
    task_id: 909,
    task_status: "completed",
    task_title: "汇总任务",
  },
};

describe("ProductionCanvasNodeTools", () => {
  afterEach(() => cleanup());

  it("surfaces task evidence summary above node tools", () => {
    const utils = render(
      <ProductionCanvasNodeTools
        edges={[]}
        node={undefined}
        nodes={[taskNode]}
        onAddEdge={() => undefined}
        onDuplicateNote={() => undefined}
        onRemoveEdge={() => undefined}
        onUpdateNode={() => undefined}
        onUpdateNodeOutputs={() => undefined}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("任务证据"));
    assert.ok(utils.getByText("Task #909 · 已完成 · 汇总任务"));
  });
});
