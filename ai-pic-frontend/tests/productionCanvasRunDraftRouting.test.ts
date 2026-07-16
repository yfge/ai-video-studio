import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { createElement, useState } from "react";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { useProductionCanvasRunPersistence } from "../src/components/features/canvas/useProductionCanvasRunPersistence";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const originalFetch = globalThis.fetch;
const emptyCanvasState = {
  edges: [],
  nodes: [],
  selectedNodeId: null,
  viewport: { x: 0, y: 0, zoom: 1 },
};
let createdSessions = 0;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function json(data: unknown) {
  return new Response(JSON.stringify(data), {
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  cleanup();
  globalThis.fetch = originalFetch;
  dom.window.history.replaceState(null, "", "/canvas");
  dom.window.document.body.replaceChildren();
  createdSessions = 0;
});

describe("ProductionCanvas Run draft routing", () => {
  it("syncs the URL only after restore and does not restore again on URL echo", async () => {
    let restoreCount = 0;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/confirmed-run")) {
        restoreCount += 1;
        return json({
          success: true,
          data: {
            run_id: "confirmed-run",
            task_id: 1,
            nodes: [],
            selected_assets: { virtual_ips: [], environments: [] },
            skill_manifest: { version: "production_canvas.v1" },
            saved_state: emptyCanvasState,
            access_role: "owner",
          },
        });
      }
      throw new Error(`Unexpected request ${url}`);
    };

    function Harness({ initialRunId }: { initialRunId?: string }) {
      const [sessionId] = useState(() => ++createdSessions);
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: emptyCanvasState,
        initialRunId,
        replaceCanvasState: () => {},
      });
      return createElement(
        "div",
        {},
        createElement("span", { "data-testid": "session" }, sessionId),
        createElement(
          "span",
          { "data-testid": "draft" },
          persistence.runIdDraft,
        ),
        createElement("span", { "data-testid": "active" }, persistence.runId),
        createElement("span", { "data-testid": "status" }, persistence.status),
        createElement(
          "button",
          {
            onClick: () => persistence.setRunIdDraft("confirmed-run"),
            type: "button",
          },
          "stage run",
        ),
        createElement(
          "button",
          {
            onClick: () =>
              void persistence.restoreCanvas(persistence.runIdDraft),
            type: "button",
          },
          "restore run",
        ),
      );
    }

    const utils = render(createElement(Harness), {
      container: dom.window.document.body,
    });
    fireEvent.click(utils.getByRole("button", { name: "stage run" }));
    assert.equal(utils.getByTestId("draft").textContent, "confirmed-run");
    assert.equal(utils.getByTestId("active").textContent, "");
    assert.equal(dom.window.location.href, "http://localhost/canvas");

    fireEvent.click(utils.getByRole("button", { name: "restore run" }));
    await waitFor(() =>
      assert.equal(utils.getByTestId("status").textContent, "已恢复"),
    );
    assert.equal(restoreCount, 1);
    await waitFor(() =>
      assert.equal(
        dom.window.location.href,
        "http://localhost/canvas?run_id=confirmed-run",
      ),
    );

    utils.rerender(createElement(Harness, { initialRunId: "confirmed-run" }));
    await new Promise((resolve) => setTimeout(resolve, 20));
    assert.equal(restoreCount, 1);
    assert.equal(utils.getByTestId("session").textContent, "1");
  });

  it("lets a newer route supersede an in-flight restore", async () => {
    const first = deferred<Response>();
    const second = deferred<Response>();
    const requests: string[] = [];
    globalThis.fetch = async (input) => {
      const url = String(input);
      requests.push(url);
      if (url.includes("/production-canvas/runs/run-a")) return first.promise;
      if (url.includes("/production-canvas/runs/run-b")) return second.promise;
      throw new Error(`Unexpected request ${url}`);
    };

    function Harness({ initialRunId }: { initialRunId: string }) {
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: emptyCanvasState,
        initialRunId,
        replaceCanvasState: () => {},
      });
      return createElement(
        "div",
        {},
        createElement("span", { "data-testid": "active" }, persistence.runId),
        createElement(
          "span",
          { "data-testid": "draft" },
          persistence.runIdDraft,
        ),
        createElement("span", { "data-testid": "status" }, persistence.status),
      );
    }

    const utils = render(createElement(Harness, { initialRunId: "run-a" }), {
      container: dom.window.document.body,
    });
    await waitFor(() => assert.equal(requests.length, 1));

    dom.window.history.replaceState(null, "", "/canvas?run_id=run-b");
    utils.rerender(createElement(Harness, { initialRunId: "run-b" }));
    await waitFor(() => assert.equal(requests.length, 2));
    assert.equal(utils.getByTestId("draft").textContent, "run-b");

    first.resolve(
      json({
        success: true,
        data: {
          run_id: "run-a",
          task_id: 1,
          nodes: [],
          selected_assets: { virtual_ips: [], environments: [] },
          skill_manifest: { version: "production_canvas.v1" },
          saved_state: emptyCanvasState,
          access_role: "owner",
        },
      }),
    );
    await new Promise((resolve) => setTimeout(resolve, 20));
    assert.equal(utils.getByTestId("active").textContent, "run-a");
    assert.equal(
      dom.window.location.href,
      "http://localhost/canvas?run_id=run-b",
    );

    second.resolve(
      json({
        success: true,
        data: {
          run_id: "run-b",
          task_id: 2,
          nodes: [],
          selected_assets: { virtual_ips: [], environments: [] },
          skill_manifest: { version: "production_canvas.v1" },
          saved_state: emptyCanvasState,
          access_role: "owner",
        },
      }),
    );
    await waitFor(() =>
      assert.equal(utils.getByTestId("status").textContent, "已恢复"),
    );
    assert.equal(utils.getByTestId("active").textContent, "run-b");
    assert.equal(
      dom.window.location.href,
      "http://localhost/canvas?run_id=run-b",
    );
  });
});
