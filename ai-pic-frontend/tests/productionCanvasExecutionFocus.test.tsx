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
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvas execution focus", () => {
  afterEach(() => cleanup());

  it("keeps keyboard control after inspector and node-card execution", async () => {
    const originalFetch = globalThis.fetch;
    let executeCount = 0;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/plan")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-execution-focus",
              task_id: 45,
              nodes: [
                {
                  id: "manual-skill",
                  label: "Manual Skill",
                  title: "需要手动执行的节点",
                  status: "review",
                  x: 420,
                  y: 360,
                  width: 220,
                  kind: "skill_result",
                  skill: "script.generate",
                  detail: "用于验证执行后的键盘连续性。",
                  outputs: {},
                },
              ],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url.includes("/production-canvas/execute")) {
        executeCount++;
        return new Response(
          JSON.stringify({ success: false, error: "手动执行失败" }),
          { headers: { "content-type": "application/json" } },
        );
      }
      throw new Error(`Unexpected request ${url}`);
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
      await waitFor(() => assert.ok(utils.getAllByText("Manual Skill").length));

      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const manualNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='manual-skill']",
      );
      assert.ok(canvas);
      assert.ok(manualNode);
      fireEvent.click(utils.getByLabelText("Manual Skill 需要手动执行的节点"));

      const inspectorExecute = utils.getByRole("button", {
        name: "后台执行",
      });
      inspectorExecute.focus();
      fireEvent.click(inspectorExecute);
      await waitFor(() => assert.equal(executeCount, 1));
      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(manualNode.style.left, "436px");

      const nodeExecute = utils.getByRole("button", {
        name: "后台执行 Manual Skill",
      });
      await waitFor(() =>
        assert.equal(nodeExecute.hasAttribute("disabled"), false),
      );
      nodeExecute.focus();
      fireEvent.click(nodeExecute);
      await waitFor(() => assert.equal(executeCount, 2));
      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(manualNode.style.left, "452px");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
