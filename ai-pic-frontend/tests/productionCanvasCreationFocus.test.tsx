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

describe("ProductionCanvas creation focus", () => {
  afterEach(() => cleanup());

  it("keeps keyboard control after creating a production plan", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (!url.includes("/production-canvas/plan")) {
        throw new Error(`Unexpected request ${url}`);
      }
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            run_id: "canvas-run-creation-focus",
            task_id: 45,
            nodes: [
              {
                id: "created-node",
                label: "Created Node",
                title: "创建后的首个节点",
                status: "review",
                x: 420,
                y: 360,
                width: 220,
                kind: "skill_result",
                skill: "script.generate",
                outputs: {},
              },
            ],
            selected_assets: { virtual_ips: [], environments: [] },
            skill_manifest: { version: "production_canvas.v1" },
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "创建一条生产链路" },
      });

      const createButton = utils.getByRole("button", { name: "整体创建" });
      createButton.focus();
      fireEvent.click(createButton);

      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      assert.ok(canvas);
      assert.equal(dom.window.document.activeElement, canvas);

      await waitFor(() => assert.ok(utils.getAllByText("Created Node").length));
      const createdNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='created-node']",
      );
      assert.ok(createdNode);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(createdNode.style.left, "436px");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
