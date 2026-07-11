import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import {
  jsonResponse,
  parseRequestBody,
  skillNode,
  type FetchInit,
  type FetchInput,
  type RequestPayload,
} from "./productionCanvasPlannerFetchCommon";

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

const planData = {
  run_id: "canvas-run-downstream",
  task_id: 45,
  nodes: [
    skillNode({
      id: "root-skill",
      label: "Root Skill",
      title: "等待运行起点",
      status: "review",
      x: 420,
      y: 360,
      skill: "brief.compose",
      outputs: {},
    }),
    skillNode({
      id: "leaf-skill",
      label: "Leaf Skill",
      title: "等待上游输入",
      status: "draft",
      x: 680,
      y: 360,
      skill: "brief.compose",
      outputs: {},
    }),
  ],
  selected_assets: { virtual_ips: [], environments: [] },
  skill_manifest: { version: "production_canvas.v1" },
};

function execution(nodeId: string, label: string, title: string) {
  return {
    node_id: nodeId,
    resolved_inputs:
      nodeId === "leaf-skill" ? { production_brief: "真实图输入" } : {},
    skill_result: {
      skill: "brief.compose",
      label,
      title,
      status: "ready",
      detail: `${label} 已按类型图执行`,
      outputs: { prompt: "真实图输入" },
      reuse_targets: [],
    },
  };
}

describe("ProductionCanvas downstream execution", () => {
  afterEach(() => cleanup());

  it("saves the graph, sends node scope, and publishes every execution", async () => {
    const originalFetch = globalThis.fetch;
    const requestOrder: string[] = [];
    let executeRequest: RequestPayload | null = null;
    globalThis.fetch = async (input: FetchInput, init?: FetchInit) => {
      const url = String(input);
      if (url.endsWith("/production-canvas/plan")) {
        return jsonResponse(planData);
      }
      if (url.endsWith("/state")) {
        requestOrder.push("save");
        return jsonResponse({ run_id: planData.run_id });
      }
      if (url.endsWith("/production-canvas/execute")) {
        requestOrder.push("execute");
        executeRequest = parseRequestBody(init);
        const root = execution("root-skill", "Root Skill", "Root completed");
        const leaf = execution("leaf-skill", "Leaf Skill", "Leaf completed");
        return jsonResponse({
          ...root,
          execution_order: ["root-skill", "leaf-skill"],
          executions: [root, leaf],
        });
      }
      if (url.includes("/production-canvas/runs/")) {
        return jsonResponse(planData);
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "验证真实下游执行" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));
      await waitFor(() => assert.ok(utils.getAllByText("Root Skill").length));

      fireEvent.click(utils.getByLabelText("Root Skill 等待运行起点"));
      fireEvent.click(utils.getByRole("button", { name: "运行下游" }));

      await waitFor(() =>
        assert.ok(utils.getAllByText("Leaf completed").length),
      );
      assert.deepEqual(requestOrder, ["save", "execute"]);
      assert.equal(executeRequest?.node_id, "root-skill");
      assert.equal(executeRequest?.execution_scope, "downstream");
      assert.ok(utils.getAllByText("Root completed").length);
      assert.ok(utils.getAllByText("Leaf completed").length);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
