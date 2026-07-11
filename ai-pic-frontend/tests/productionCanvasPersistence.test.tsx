import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { productionCanvasStateFromRun } from "../src/components/features/canvas/productionCanvasPersistence";
import { readStoredCanvasState } from "../src/components/features/canvas/productionCanvasViewModel";
import { productionCanvasRunIdFromInput } from "../src/components/features/canvas/useProductionCanvasRunPersistence";

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

describe("ProductionCanvasPersistence", () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState(null, "", "/");
  });

  it("normalizes pasted canvas links into run ids", () => {
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

  it("reapplies context when restoring saved canvas nodes", () => {
    const savedNodes = [
      {
        id: "script",
        label: "Script",
        title: "已有剧本",
        status: "review",
        x: 0,
        y: 0,
        width: 220,
        skill: "script.generate",
        kind: "skill_result",
        outputs: { script_id: 123 },
      },
      {
        id: "timeline",
        label: "Timeline",
        title: "生成时间线",
        status: "blocked",
        x: 260,
        y: 0,
        width: 220,
        skill: "timeline.build",
        kind: "skill_result",
        outputs: { required_inputs: ["script_id"] },
      },
    ];

    window.localStorage.setItem(
      "canvas-context-restore-test",
      JSON.stringify({
        edges: [],
        nodes: savedNodes,
        selectedNodeId: "timeline",
        viewport: { x: 0, y: 0, zoom: 1 },
      }),
    );

    try {
      const localTimeline = readStoredCanvasState(
        "canvas-context-restore-test",
      ).nodes.find((node) => node.id === "timeline");
      const serverTimeline = productionCanvasStateFromRun({
        run_id: "canvas-run-context",
        task_id: 1,
        nodes: [],
        selected_assets: { virtual_ips: [], environments: [] },
        skill_manifest: { version: "production_canvas.v1" },
        saved_state: {
          edges: [],
          nodes: savedNodes,
          selected_node_id: "timeline",
          viewport: { x: 0, y: 0, zoom: 1 },
        },
      } as any).nodes.find((node) => node.id === "timeline");

      assert.equal(localTimeline?.status, "ready");
      assert.equal(localTimeline?.outputs?.script_id, 123);
      assert.equal(localTimeline?.outputs?.required_inputs, undefined);
      assert.equal(serverTimeline?.status, "ready");
      assert.equal(serverTimeline?.outputs?.script_id, 123);
      assert.equal(serverTimeline?.outputs?.required_inputs, undefined);
    } finally {
      window.localStorage.removeItem("canvas-context-restore-test");
    }
  });

  it("preserves an intentionally empty saved edge list", () => {
    window.localStorage.setItem(
      "canvas-empty-edges-test",
      JSON.stringify({
        edges: [],
        nodes: [
          {
            id: "brief",
            label: "Brief",
            title: "Brief",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
            kind: "skill_result",
            skill: "brief.compose",
          },
        ],
        selectedNodeId: "brief",
        viewport: { x: 0, y: 0, zoom: 1 },
      }),
    );

    try {
      assert.deepEqual(
        readStoredCanvasState("canvas-empty-edges-test").edges,
        [],
      );
    } finally {
      window.localStorage.removeItem("canvas-empty-edges-test");
    }
  });

  it("clamps restored local canvas zoom to a visible range", () => {
    window.localStorage.setItem(
      "canvas-local-zoom-test",
      JSON.stringify({
        edges: [],
        nodes: [
          {
            id: "brief",
            label: "Brief",
            title: "Brief",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
          },
        ],
        selectedNodeId: "brief",
        viewport: { x: 0, y: 0, zoom: 0 },
      }),
    );

    try {
      assert.equal(
        readStoredCanvasState("canvas-local-zoom-test").viewport.zoom,
        0.5,
      );
    } finally {
      window.localStorage.removeItem("canvas-local-zoom-test");
    }
  });

  it("clamps restored server canvas zoom to a visible range", () => {
    const restored = productionCanvasStateFromRun({
      run_id: "canvas-run-zoom",
      task_id: 1,
      nodes: [],
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
      saved_state: {
        edges: [],
        nodes: [
          {
            id: "brief",
            label: "Brief",
            title: "Brief",
            status: "review",
            x: 0,
            y: 0,
            width: 220,
          },
        ],
        selected_node_id: "brief",
        viewport: { x: 0, y: 0, zoom: 0 },
      },
    } as any);

    assert.equal(restored.viewport.zoom, 0.5);
  });

  it("saves and restores a server-backed canvas run", async () => {
    const originalFetch = globalThis.fetch;
    const savedBodies: Record<string, unknown>[] = [];
    let clipboardText = "";
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: {
        writeText: async (value: string) => {
          clipboardText = value;
        },
      },
      configurable: true,
    });
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/plan")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-123",
              task_id: 44,
              nodes: [
                {
                  id: "skill-brief",
                  label: "Brief Skill",
                  title: "服务端已生成 brief 节点",
                  status: "review",
                  x: 180,
                  y: 320,
                  width: 220,
                  kind: "skill_result",
                  skill: "brief.compose",
                  detail: "用于测试服务端状态保存。",
                  outputs: { prompt: "做一版短剧生产画布" },
                },
              ],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      if (url.includes("/production-canvas/runs/canvas-run-123/state")) {
        savedBodies.push(JSON.parse(String(init?.body)));
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-123",
              task_id: 44,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: savedBodies[savedBodies.length - 1],
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      if (url.includes("/production-canvas/runs/canvas-run-123")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-123",
              task_id: 55,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: {
                nodes: [
                  {
                    id: "skill-brief",
                    label: "Brief Skill",
                    title: "服务端 brief",
                    status: "review",
                    x: 120,
                    y: 160,
                    width: 220,
                    kind: "skill_result",
                    skill: "brief.compose",
                  },
                  {
                    id: "note-1",
                    label: "便签",
                    title: "服务端备注",
                    status: "review",
                    x: 320,
                    y: 260,
                    width: 190,
                    kind: "note",
                    detail: "从服务端恢复",
                  },
                ],
                viewport: { x: 12, y: 34, zoom: 0.8 },
                selected_node_id: "note-1",
                edges: [{ from: "note-1", to: "skill-brief" }],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      window.history.replaceState(null, "", "/canvas");
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "做一版短剧生产画布" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => {
        const input = utils.getByLabelText("Run ID") as HTMLInputElement;
        assert.equal(input.value, "canvas-run-123");
      });
      await waitFor(() =>
        assert.equal(
          window.location.href,
          "http://localhost/canvas?run_id=canvas-run-123",
        ),
      );
      fireEvent.click(utils.getByRole("button", { name: "复制 Run ID" }));
      await waitFor(() => assert.equal(clipboardText, "canvas-run-123"));
      assert.ok(utils.getByText("已复制 Run ID"));
      fireEvent.click(utils.getByRole("button", { name: "复制链接" }));
      await waitFor(() =>
        assert.equal(
          clipboardText,
          "http://localhost/canvas?run_id=canvas-run-123",
        ),
      );
      await waitFor(() => assert.ok(utils.getByText("已复制链接")));

      fireEvent.click(utils.getByRole("button", { name: "保存画布" }));
      await waitFor(() => assert.equal(savedBodies.length, 1));
      assert.equal(savedBodies[0]?.graph_version, 2);
      assert.equal(savedBodies[0]?.selected_node_id, "skill-brief");
      assert.ok(Array.isArray(savedBodies[0]?.nodes));
      assert.ok(Array.isArray(savedBodies[0]?.edges));
      const savedBrief = savedBodies[0]?.nodes.find(
        (node: { id: string }) => node.id === "skill-brief",
      );
      assert.equal(savedBrief?.kind, "pipeline");
      assert.equal(savedBrief?.definition_version, 1);
      assert.equal(savedBrief?.output_ports?.[0]?.id, "production_brief");
      const imageVideoEdge = savedBodies[0]?.edges.find(
        (edge: { from: string; to: string }) =>
          edge.from === "image" && edge.to === "video",
      );
      assert.equal(imageVideoEdge?.from_port, "approved_image");
      assert.equal(imageVideoEdge?.to_port, "start_frame");
      assert.equal(imageVideoEdge?.binding_type, "selected_output");
      await waitFor(() => assert.ok(utils.getByText("已保存")));

      fireEvent.click(utils.getByRole("button", { name: "恢复画布" }));

      await waitFor(() => assert.ok(utils.getAllByText("服务端备注").length));
      assert.ok(
        utils.container.querySelector(
          "[data-canvas-edge='note-1-skill-brief']",
        ),
      );
      const world = utils.container.querySelector(
        "[data-production-canvas-world='true']",
      ) as HTMLElement;
      assert.match(
        world.style.transform,
        /translate\(12px, 34px\) scale\(0.8\)/,
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("debounces autosave after a run exists and saves the latest canvas state", async () => {
    const originalFetch = globalThis.fetch;
    const savedBodies: Record<string, any>[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/plan")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-autosave",
              task_id: 66,
              nodes: [
                {
                  id: "skill-brief",
                  label: "Brief Skill",
                  title: "自动保存 brief",
                  status: "review",
                  x: 180,
                  y: 320,
                  width: 220,
                  kind: "skill_result",
                  skill: "brief.compose",
                  outputs: { prompt: "自动保存画布" },
                },
              ],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      if (url.includes("/production-canvas/runs/canvas-run-autosave/state")) {
        savedBodies.push(JSON.parse(String(init?.body)));
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-autosave",
              task_id: 66,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: savedBodies[savedBodies.length - 1],
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={5} />,
        { container: dom.window.document.body },
      );
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "自动保存画布" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() => assert.equal(savedBodies.length, 1));
      fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
      fireEvent.click(utils.getByRole("button", { name: "添加便签" }));

      await waitFor(() => {
        assert.equal(savedBodies.length, 2);
        const latestNodes = savedBodies[1].nodes as Array<{ id: string }>;
        assert.ok(latestNodes.some((node) => node.id === "note-2"));
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("clears the active run id from the URL when the canvas is reset", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/plan")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-reset",
              task_id: 67,
              nodes: [
                {
                  id: "reset-note",
                  label: "便签",
                  title: "重置前备注",
                  status: "review",
                  x: 180,
                  y: 320,
                  width: 220,
                  kind: "note",
                },
              ],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      window.history.replaceState(null, "", "/canvas");
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "验证重置清理 Run ID" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));

      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("Run ID") as HTMLInputElement).value,
          "canvas-run-reset",
        ),
      );
      fireEvent.click(utils.getByRole("button", { name: "重置" }));

      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("Run ID") as HTMLInputElement).value,
          "",
        ),
      );
      assert.equal(window.location.href, "http://localhost/canvas");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("restores a canvas run from the initial run id", async () => {
    const originalFetch = globalThis.fetch;
    const requests: string[] = [];
    globalThis.fetch = async (input) => {
      const url = String(input);
      requests.push(url);
      if (url.includes("/production-canvas/runs/canvas-run-linked")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-linked",
              task_id: 77,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: {
                nodes: [
                  {
                    id: "linked-note",
                    label: "便签",
                    title: "链接恢复备注",
                    status: "review",
                    x: 240,
                    y: 180,
                    width: 190,
                    kind: "note",
                  },
                ],
                viewport: { x: 20, y: 30, zoom: 0.9 },
                selected_node_id: "linked-note",
                edges: [],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      const utils = render(
        <ProductionCanvasContent
          storageKey={null}
          autosaveDelayMs={null}
          initialRunId="canvas-run-linked"
        />,
        { container: dom.window.document.body },
      );

      await waitFor(() => assert.ok(utils.getAllByText("链接恢复备注").length));
      assert.ok(requests.some((url) => url.includes("canvas-run-linked")));
      assert.ok(utils.getByText("已恢复"));
      assert.equal(
        (utils.getByLabelText("Run ID") as HTMLInputElement).value,
        "canvas-run-linked",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
