import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { useProductionCanvasSkillPlanner } from "../src/components/features/canvas/useProductionCanvasSkillPlanner";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas?run_id=current-run",
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

const staleRunNode: ProductionCanvasNode = {
  id: "skill-asset-select",
  kind: "skill_result",
  label: "Asset Selection",
  outputs: {
    canvas_run_id: "stale-run",
    environment_ids: [2],
    task_id: 6267,
    virtual_ip_ids: [1],
  },
  reuse_targets: [],
  skill: "asset.select",
  status: "review",
  title: "复用资产",
  width: 220,
  x: 160,
  y: 360,
};

describe("useProductionCanvasSkillPlanner run id routing", () => {
  afterEach(() => cleanup());

  it("prefers active run and draft context over stale node output", async () => {
    const originalFetch = globalThis.fetch;
    const executeRequests: Record<string, unknown>[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (!url.includes("/production-canvas/execute")) {
        throw new Error(`Unexpected request ${url}`);
      }
      const body = JSON.parse(String(init?.body || "{}")) as Record<
        string,
        unknown
      >;
      executeRequests.push(body);
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            skill_result: {
              ...staleRunNode,
              outputs: { canvas_run_id: body.run_id },
            },
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      const planner = useProductionCanvasSkillPlanner({
        currentRunId: "current-run",
        onNodesCreated: () => {},
      });
      return (
        <>
          <button
            type="button"
            onClick={() => planner.setContextValue("virtual_ip_id", "11")}
          >
            select ip
          </button>
          <button
            type="button"
            onClick={() => planner.setContextValue("environment_id", "22")}
          >
            select environment
          </button>
          <button
            type="button"
            onClick={() => void planner.executeSkillNode(staleRunNode)}
          >
            execute
          </button>
        </>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });

      fireEvent.click(utils.getByRole("button", { name: "select ip" }));
      fireEvent.click(
        utils.getByRole("button", { name: "select environment" }),
      );
      fireEvent.click(utils.getByRole("button", { name: "execute" }));

      await waitFor(() => assert.equal(executeRequests.length, 1));
      assert.equal(executeRequests[0]?.run_id, "current-run");
      assert.equal(executeRequests[0]?.virtual_ip_id, 11);
      assert.equal(executeRequests[0]?.environment_id, 22);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
