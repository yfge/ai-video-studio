import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  loadProductionCanvasHistory,
  ProductionCanvasHistoryContent,
} from "../src/components/features/canvas/ProductionCanvasHistory";
import type { Task } from "../src/utils/api/types/task.types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).localStorage = dom.window.localStorage;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const task = (
  id: number,
  businessId: string,
  kind: string,
  prompt: string,
  updatedAt: string,
  nodeCount = 0,
): Task => ({
  id,
  business_id: businessId,
  title: "生产画布整体创建",
  task_type: "text_generation",
  prompt,
  parameters: {
    kind,
    prompt,
    saved_state: { nodes: Array.from({ length: nodeCount }) },
  },
  status: "completed",
  created_at: "2026-07-01T00:00:00Z",
  updated_at: updatedAt,
  user_id: 1,
});

describe("ProductionCanvasHistory", () => {
  afterEach(() => cleanup());

  it("loads every task page, keeps canvas runs, and sorts by last update", async () => {
    const originalFetch = globalThis.fetch;
    const requestedUrls: string[] = [];
    globalThis.fetch = async (input) => {
      const url = String(input);
      requestedUrls.push(url);
      const secondPage = url.includes("skip=100");
      const tasks = secondPage
        ? [
            task(
              1,
              "canvas-old",
              "production_canvas_run",
              "旧画布",
              "2026-07-15T10:00:00Z",
              2,
            ),
          ]
        : [
            task(
              3,
              "not-canvas",
              "script_generation",
              "非画布任务",
              "2026-07-17T10:00:00Z",
            ),
            task(
              2,
              "canvas-new",
              "production_canvas_run",
              "新画布",
              "2026-07-16T10:00:00Z",
              4,
            ),
          ];
      return new Response(
        JSON.stringify({
          tasks,
          total: 101,
          page: secondPage ? 2 : 1,
          size: 100,
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    try {
      const history = await loadProductionCanvasHistory();

      assert.equal(requestedUrls.length, 2);
      assert.ok(
        requestedUrls.every((url) => url.includes("task_type=text_generation")),
      );
      assert.deepEqual(
        history.map((item) => [item.runId, item.title, item.nodeCount]),
        [
          ["canvas-new", "新画布", 4],
          ["canvas-old", "旧画布", 2],
        ],
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("renders history rows and the new blank canvas action", () => {
    const utils = render(
      <ProductionCanvasHistoryContent
        error={null}
        items={[
          {
            nodeCount: 4,
            runId: "canvas-new",
            title: "新画布",
            updatedAt: "2026-07-16T10:00:00Z",
          },
        ]}
        loading={false}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(
      utils.getByRole("link", { name: "新建空白画布" }).getAttribute("href"),
      "/canvas?new=1",
    );
    const row = utils.container.querySelector(
      "[data-canvas-history-run='canvas-new']",
    );
    assert.equal(row?.getAttribute("href"), "/canvas?run_id=canvas-new");
    assert.ok(utils.getByText("4 个节点"));
  });
});
