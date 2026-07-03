import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";

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

const storageKey = "canvas-board-task-summary-select-test";

describe("ProductionCanvasBoard task summary", () => {
  afterEach(() => {
    cleanup();
    window.localStorage.removeItem(storageKey);
  });

  it("selects task evidence nodes from the side summary", async () => {
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({
        edges: [],
        nodes: [
          {
            id: "brief",
            label: "Brief",
            title: "Brief",
            status: "ready",
            x: 40,
            y: 40,
            width: 180,
          },
          {
            id: "task-909",
            label: "Task #909",
            title: "侧栏选择任务",
            status: "review",
            x: 280,
            y: 40,
            width: 220,
            kind: "note",
            outputs: {
              task_id: 909,
              task_status: "completed",
              task_title: "侧栏选择任务",
            },
          },
        ],
        selectedNodeId: "brief",
        viewport: { x: 0, y: 0, zoom: 1 },
      }),
    );

    const utils = render(<ProductionCanvasContent storageKey={storageKey} />, {
      container: dom.window.document.body,
    });

    await waitFor(() => utils.getByText("任务证据"));
    fireEvent.click(utils.getByRole("button", { name: "定位任务 909" }));

    await waitFor(() =>
      assert.match(
        utils.container.querySelector("[data-canvas-node='task-909']")
          ?.className || "",
        /ring-blue-500/,
      ),
    );
  });
});
