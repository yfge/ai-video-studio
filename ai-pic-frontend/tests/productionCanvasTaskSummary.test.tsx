import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasTaskSummary } from "../src/components/features/canvas/ProductionCanvasTaskSummary";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).Event = dom.window.Event;

const taskNode = (taskId: number, status: string) => ({
  id: `task-${taskId}`,
  label: `Task #${taskId}`,
  title: `任务 ${taskId}`,
  status: "review" as const,
  x: 0,
  y: 0,
  width: 220,
  kind: "note" as const,
  outputs: {
    task_id: taskId,
    task_status: status,
    task_title: `任务 ${taskId}`,
  },
});

describe("ProductionCanvasTaskSummary", () => {
  afterEach(() => cleanup());

  it("clears stale filters when task evidence disappears", () => {
    const utils = render(
      <ProductionCanvasTaskSummary
        nodes={[taskNode(1, "completed"), taskNode(2, "failed")]}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "筛选异常任务" }));
    assert.ok(utils.getByText("Task #2 · 失败 · 任务 2"));

    utils.rerender(<ProductionCanvasTaskSummary nodes={[]} />);
    assert.equal(utils.queryByText("任务证据"), null);

    utils.rerender(
      <ProductionCanvasTaskSummary nodes={[taskNode(3, "completed")]} />,
    );

    assert.match(
      utils.getByRole("button", { name: "筛选全部任务" }).className,
      /ring-blue-300/,
    );
    assert.ok(utils.getByText("Task #3 · 已完成 · 任务 3"));
  });
});
