import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { installHierarchyFetch } from "./productionCanvasHierarchyFixture";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).Element = dom.window.Element;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const storageKey = "production-canvas-view-isolation-test";
const originalFetch = globalThis.fetch;

function json(data: unknown) {
  return new Response(JSON.stringify(data), {
    headers: { "content-type": "application/json" },
  });
}

function canvasNode(runId: string, outputs: Record<string, unknown> = {}) {
  return {
    id: "brief",
    label: "Brief",
    title: "路由隔离测试",
    status: "review",
    x: 0,
    y: 0,
    width: 220,
    kind: "skill_result",
    skill: "brief.compose",
    outputs: { ...outputs, canvas_run_id: runId },
  };
}

function storedCanvas(runId: string, outputs: Record<string, unknown> = {}) {
  return {
    edges: [],
    nodes: [canvasNode(runId, outputs)],
    selectedNodeId: "brief",
    viewport: { x: 0, y: 0, zoom: 1 },
  };
}

function runResponse(runId: string, savedState: unknown) {
  return {
    success: true,
    data: {
      run_id: runId,
      task_id: 1,
      nodes: [],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: savedState,
      access_role: "owner",
    },
  };
}

afterEach(() => {
  cleanup();
  globalThis.fetch = originalFetch;
  dom.window.localStorage.clear();
  dom.window.history.replaceState(null, "", "/canvas");
  dom.window.document.body.replaceChildren();
});

describe("ProductionCanvas view isolation", () => {
  it("enables autosave only while the execution view is active", async () => {
    const savedBodies: unknown[] = [];
    dom.window.localStorage.setItem(
      storageKey,
      JSON.stringify(storedCanvas("local-run")),
    );
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/virtual-ips/?limit=100")) {
        return json({ success: true, data: [] });
      }
      if (url.includes("/production-canvas/runs/local-run/state")) {
        const body = JSON.parse(String(init?.body));
        savedBodies.push(body);
        return json(runResponse("local-run", body));
      }
      if (url.includes("/production-canvas/runs/local-run")) {
        return json(runResponse("local-run", storedCanvas("local-run")));
      }
      throw new Error(`Unexpected request ${url}`);
    };

    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={10}
        initialRunId="local-run"
        initialView="hierarchy"
        storageKey={storageKey}
      />,
      { container: dom.window.document.body },
    );

    await waitFor(() =>
      assert.ok(utils.getByRole("region", { name: "业务实体层级无限画布" })),
    );
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(savedBodies.length, 0);
    assert.ok(utils.getByRole("group", { name: "画布视图" }));
    assert.equal(utils.queryByRole("tab"), null);
    assert.equal(
      utils
        .getByRole("button", { name: "业务层级" })
        .getAttribute("aria-pressed"),
      "true",
    );

    fireEvent.click(utils.getByRole("button", { name: "执行图" }));
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(savedBodies.length, 0);
    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    await waitFor(() => assert.equal(savedBodies.length, 1));

    fireEvent.click(utils.getByRole("button", { name: "业务层级" }));
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(savedBodies.length, 1);

    fireEvent.click(utils.getByRole("button", { name: "执行图" }));
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(savedBodies.length, 1);
    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    await waitFor(() => assert.equal(savedBodies.length, 2));
  });

  it("switches the selected view when routing props change", async () => {
    const restoredRuns: string[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/virtual-ips/?limit=100")) {
        return json({ success: true, data: [] });
      }
      if (
        url.includes("/production-canvas/runs/route-run") &&
        (init?.method || "GET") === "GET"
      ) {
        restoredRuns.push("route-run");
        return json(
          runResponse("route-run", {
            ...storedCanvas("route-run"),
            selected_node_id: "brief",
          }),
        );
      }
      throw new Error(`Unexpected request ${url}`);
    };

    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialRunId={null}
        initialView="hierarchy"
        storageKey={null}
      />,
      { container: dom.window.document.body },
    );
    await waitFor(() =>
      assert.ok(utils.getByRole("region", { name: "业务实体层级无限画布" })),
    );
    fireEvent.click(utils.getByRole("button", { name: "执行图" }));
    fireEvent.input(utils.getByLabelText("生产目标"), {
      target: { value: "路由切换保留会话" },
    });
    fireEvent.click(utils.getByRole("button", { name: "业务层级" }));

    utils.rerender(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialRunId="route-run"
        initialView="execution"
        storageKey={null}
      />,
    );
    await waitFor(() => assert.ok(restoredRuns.length >= 1));
    assert.equal(
      utils
        .getByRole("button", { name: "执行图" })
        .getAttribute("aria-pressed"),
      "true",
    );
    assert.ok(utils.getByRole("region", { name: "短剧生产链路无限画布" }));
    assert.equal(
      (utils.getByLabelText("生产目标") as HTMLTextAreaElement).value,
      "路由切换保留会话",
    );

    utils.rerender(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialRunId={null}
        initialView="hierarchy"
        storageKey={null}
      />,
    );
    await waitFor(() =>
      assert.equal(
        utils
          .getByRole("button", { name: "业务层级" })
          .getAttribute("aria-pressed"),
        "true",
      ),
    );
  });

  it("replaces restored run context without remounting the session", async () => {
    const hierarchyStub = installHierarchyFetch();
    const hierarchyFetch = globalThis.fetch;
    const executeRequests: Record<string, unknown>[] = [];
    const restoredRuns: string[] = [];
    const runContexts: Record<string, Record<string, unknown>> = {
      "run-a": {
        virtual_ip_ids: [1],
        environment_ids: [8],
        story_id: 10,
        episode_id: 100,
        script_id: 300,
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "clip-ready",
      },
      "run-b": { virtual_ip_ids: [2] },
    };
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      const runMatch = url.match(/production-canvas\/runs\/(run-[ab])$/);
      if (runMatch && (init?.method || "GET") === "GET") {
        const runId = runMatch[1];
        restoredRuns.push(runId);
        return json(
          runResponse(runId, storedCanvas(runId, runContexts[runId])),
        );
      }
      if (url.includes("/production-canvas/runs/run-b/state")) {
        return json(runResponse("run-b", JSON.parse(String(init?.body))));
      }
      if (url.includes("/production-canvas/execute")) {
        const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
        executeRequests.push(body);
        return json({
          success: true,
          data: {
            skill_result: {
              label: "Brief",
              title: "Run B 已执行",
              status: "review",
              detail: "done",
              outputs: { canvas_run_id: "run-b" },
              reuse_targets: [],
            },
          },
        });
      }
      return hierarchyFetch(input, init);
    };

    try {
      const utils = render(
        <ProductionCanvasContent
          autosaveDelayMs={null}
          initialRunId="run-a"
          initialView="hierarchy"
          storageKey={null}
        />,
        { container: dom.window.document.body },
      );
      await waitFor(() =>
        assert.ok(
          utils.container.querySelector('[data-hierarchy-node="video:901"]'),
        ),
      );
      fireEvent.click(utils.getByRole("button", { name: "执行图" }));
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "跨 Run 保留这一句话" },
      });

      utils.rerender(
        <ProductionCanvasContent
          autosaveDelayMs={null}
          initialRunId="run-b"
          initialView="execution"
          storageKey={null}
        />,
      );
      await waitFor(() => assert.ok(restoredRuns.includes("run-b")));
      assert.equal(
        (utils.getByLabelText("生产目标") as HTMLTextAreaElement).value,
        "跨 Run 保留这一句话",
      );
      fireEvent.click(utils.getByRole("button", { name: "运行节点" }));
      await waitFor(() => assert.equal(executeRequests.length, 1));
      assert.equal(executeRequests[0]?.run_id, "run-b");
      assert.equal(executeRequests[0]?.virtual_ip_id, 2);
      for (const key of [
        "environment_id",
        "story_id",
        "episode_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
      ]) {
        assert.equal(executeRequests[0]?.[key], undefined, key);
      }

      fireEvent.click(utils.getByRole("button", { name: "业务层级" }));
      await waitFor(() => {
        const runBIp = utils.container.querySelector(
          '[data-hierarchy-node="ip:2"]',
        );
        assert.equal(runBIp?.getAttribute("aria-current"), "true");
      });
      assert.equal(
        utils.container.querySelector('[data-hierarchy-node="story:10"]'),
        null,
      );
      assert.equal(
        utils.container.querySelector('[data-hierarchy-node="environment:8"]'),
        null,
      );

      utils.rerender(
        <ProductionCanvasContent
          autosaveDelayMs={null}
          initialRunId={null}
          initialView="execution"
          storageKey={null}
        />,
      );
      await waitFor(() => {
        assert.equal(
          (utils.getByLabelText("Run ID") as HTMLInputElement).value,
          "",
        );
        assert.ok(
          utils.getByRole("button", {
            name: "Brief IP、受众、题材和单集目标",
          }),
        );
      });
      assert.equal(
        utils.queryByRole("button", { name: "后台执行 Brief" }),
        null,
      );

      fireEvent.click(utils.getByRole("button", { name: "业务层级" }));
      await waitFor(() =>
        assert.notEqual(
          utils.container
            .querySelector('[data-hierarchy-node="ip:2"]')
            ?.getAttribute("aria-current"),
          "true",
        ),
      );

      const freshIp2 = utils.container.querySelector(
        '[data-hierarchy-node="ip:2"]',
      );
      assert.ok(freshIp2);
      fireEvent.click(freshIp2.querySelector("button")!);
      await waitFor(() =>
        assert.equal(freshIp2.getAttribute("aria-current"), "true"),
      );
      fireEvent.click(utils.getByRole("button", { name: "执行图" }));
      fireEvent.click(utils.getByRole("button", { name: "重置" }));
      fireEvent.click(utils.getByRole("button", { name: "业务层级" }));
      await waitFor(() =>
        assert.notEqual(
          utils.container
            .querySelector('[data-hierarchy-node="ip:2"]')
            ?.getAttribute("aria-current"),
          "true",
        ),
      );
    } finally {
      hierarchyStub.restore();
    }
  });

  it("blocks old-node execution while a routed Run is still restoring", async () => {
    const executeRequests: Record<string, unknown>[] = [];
    let resolveRunB: ((response: Response) => void) | undefined;
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (
        url.includes("/production-canvas/runs/run-a") &&
        (init?.method || "GET") === "GET"
      ) {
        return json(
          runResponse("run-a", {
            ...storedCanvas("run-a", { virtual_ip_ids: [1] }),
            selected_node_id: "brief",
          }),
        );
      }
      if (
        url.includes("/production-canvas/runs/run-b") &&
        (init?.method || "GET") === "GET"
      ) {
        return new Promise<Response>((resolve) => {
          resolveRunB = resolve;
        });
      }
      if (url.includes("/production-canvas/execute")) {
        executeRequests.push(JSON.parse(String(init?.body || "{}")));
        return json({
          success: true,
          data: {
            skill_result: {
              label: "Brief",
              title: "Run B 已执行",
              status: "review",
              detail: "done",
              outputs: { canvas_run_id: "run-b" },
              reuse_targets: [],
            },
          },
        });
      }
      throw new Error(`Unexpected request ${url}`);
    };

    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialRunId="run-a"
        initialView="execution"
        storageKey={null}
      />,
      { container: dom.window.document.body },
    );
    await waitFor(() =>
      assert.equal(
        (utils.getByLabelText("Run ID") as HTMLInputElement).value,
        "run-a",
      ),
    );

    utils.rerender(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialRunId="run-b"
        initialView="execution"
        storageKey={null}
      />,
    );
    await waitFor(() => assert.ok(resolveRunB));
    const oldRunButton = utils.getByRole("button", {
      name: "后台执行 Brief",
    });
    assert.equal(oldRunButton.hasAttribute("disabled"), true);
    fireEvent.click(oldRunButton);
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.deepEqual(executeRequests, []);

    resolveRunB?.(
      json(
        runResponse("run-b", {
          ...storedCanvas("run-b", { virtual_ip_ids: [2] }),
          selected_node_id: "brief",
        }),
      ),
    );
    await waitFor(() =>
      assert.equal(
        (utils.getByLabelText("Run ID") as HTMLInputElement).value,
        "run-b",
      ),
    );
    assert.deepEqual(executeRequests, []);
  });
});
