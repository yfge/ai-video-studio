import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import { createElement, useState } from "react";

import {
  productionCanvasRunIdFromInput,
  useProductionCanvasRunPersistence,
} from "../src/components/features/canvas/useProductionCanvasRunPersistence";
import type { ProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
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

const emptyCanvasState: ProductionCanvasState = {
  edges: [],
  nodes: [],
  selectedNodeId: "",
  viewport: { x: 0, y: 0, zoom: 1 },
};

describe("productionCanvasRunIdFromInput", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState(null, "", "/canvas");
  });

  it("normalizes raw run ids and pasted canvas links", () => {
    assert.equal(
      productionCanvasRunIdFromInput(" canvas-run-123 "),
      "canvas-run-123",
    );
    assert.equal(
      productionCanvasRunIdFromInput(
        "http://localhost/canvas?run_id=canvas-run-123",
      ),
      "canvas-run-123",
    );
    assert.equal(
      productionCanvasRunIdFromInput("/canvas?run_id=canvas-run-456"),
      "canvas-run-456",
    );
    assert.equal(productionCanvasRunIdFromInput("/canvas?run_id="), "");
    assert.equal(productionCanvasRunIdFromInput("/canvas"), "");
    assert.equal(productionCanvasRunIdFromInput("http://localhost/canvas"), "");
    assert.equal(productionCanvasRunIdFromInput("http://["), "http://[");
  });

  it("restores an initial run before autosave starts", async () => {
    let restoredState: ProductionCanvasState | null = null;
    let resolveRun: ((response: Response) => void) | null = null;
    const saveRequests: string[] = [];
    const runResponse = new Promise<Response>((resolve) => {
      resolveRun = resolve;
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/canvas-run-linked/state")) {
        saveRequests.push(String(init?.body || ""));
        return new Response(JSON.stringify({ success: true, data: null }), {
          headers: { "content-type": "application/json" },
        });
      }
      if (url.includes("/production-canvas/runs/canvas-run-linked")) {
        return runResponse;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    function Harness() {
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: 5,
        canvasState: emptyCanvasState,
        initialRunId: "/canvas?run_id=canvas-run-linked",
        replaceCanvasState: (state) => {
          restoredState = state;
        },
      });
      return createElement("output", {}, persistence.status || "");
    }

    try {
      render(createElement(Harness), { container: dom.window.document.body });
      await new Promise((resolve) => setTimeout(resolve, 20));
      assert.equal(saveRequests.length, 0);

      resolveRun?.(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-linked",
              task_id: 77,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: {
                edges: [],
                nodes: [
                  {
                    id: "linked-note",
                    kind: "note",
                    label: "便签",
                    status: "review",
                    title: "链接恢复备注",
                    width: 190,
                    x: 240,
                    y: 180,
                  },
                ],
                selected_node_id: "linked-note",
                viewport: { x: 20, y: 30, zoom: 0.9 },
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ),
      );

      await waitFor(() =>
        assert.equal(restoredState?.nodes[0]?.id, "linked-note"),
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("syncs run id changes into the canvas URL", async () => {
    function Harness() {
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: emptyCanvasState,
        replaceCanvasState: () => {},
      });
      return createElement(
        "div",
        {},
        createElement(
          "button",
          {
            onClick: () =>
              persistence.setRunId("/canvas?run_id=canvas-run-url"),
            type: "button",
          },
          "set run",
        ),
        createElement(
          "button",
          { onClick: persistence.resetRun, type: "button" },
          "reset run",
        ),
      );
    }

    const utils = render(createElement(Harness), {
      container: dom.window.document.body,
    });
    fireEvent.click(utils.getByRole("button", { name: "set run" }));
    await waitFor(() =>
      assert.equal(
        window.location.href,
        "http://localhost/canvas?run_id=canvas-run-url",
      ),
    );

    fireEvent.click(utils.getByRole("button", { name: "reset run" }));
    await waitFor(() =>
      assert.equal(window.location.href, "http://localhost/canvas"),
    );
  });

  it("adopts stale runtime state returned by save without replacing local layout", async () => {
    const originalFetch = globalThis.fetch;
    let savedRequest: Record<string, any> | null = null;
    globalThis.fetch = async (_input, init) => {
      savedRequest = JSON.parse(String(init?.body));
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            run_id: "canvas-run-stale",
            nodes: [],
            selected_assets: { virtual_ips: [], environments: [] },
            skill_manifest: { version: "production_canvas.v1" },
            saved_state: {
              edges: [],
              nodes: [
                {
                  id: "downstream",
                  kind: "skill_result",
                  label: "Downstream",
                  skill: "asset.select",
                  status: "stale",
                  title: "Select assets",
                  width: 220,
                  x: 10,
                  y: 20,
                  execution_input_fingerprint: "server-fingerprint",
                  outputs: { canvas_run_id: "canvas-run-stale" },
                },
              ],
              selected_node_id: "downstream",
              viewport: { x: 0, y: 0, zoom: 1 },
            },
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      const [state, setState] = useState<ProductionCanvasState>({
        edges: [],
        nodes: [
          {
            id: "downstream",
            kind: "skill_result",
            label: "Downstream",
            skill: "asset.select",
            status: "blocked",
            title: "Select assets",
            width: 220,
            x: 400,
            y: 500,
            executionInputFingerprint: "client-fingerprint",
            outputs: { canvas_run_id: "canvas-run-stale" },
          },
        ],
        selectedNodeId: "downstream",
        viewport: { x: 0, y: 0, zoom: 1 },
      });
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: state,
        replaceCanvasState: setState,
      });
      return createElement(
        "div",
        {},
        createElement(
          "button",
          { onClick: () => void persistence.saveCanvas(), type: "button" },
          "save",
        ),
        createElement(
          "output",
          {},
          state.nodes[0]?.status === "stale" ? "已过期" : "未过期",
        ),
        createElement("data", {}, String(state.nodes[0]?.x)),
      );
    }

    try {
      const utils = render(createElement(Harness), {
        container: dom.window.document.body,
      });
      fireEvent.click(utils.getByRole("button", { name: "save" }));

      await waitFor(() => assert.ok(utils.getByText("已过期")));
      assert.equal(utils.getByText("400").textContent, "400");
      assert.equal(
        savedRequest?.nodes?.[0]?.execution_input_fingerprint,
        "client-fingerprint",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
