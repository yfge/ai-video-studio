import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { useEffect } from "react";
import {
  act,
  cleanup,
  fireEvent,
  render,
  waitFor,
} from "@testing-library/react";
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
    reference_artifacts: ["virtual_ip_image:84:148", "environment_images:13:1"],
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
        nodes: [staleRunNode],
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
            onClick={() => {
              planner.setContextValue("story_id", "33");
              planner.setContextValue("episode_id", "44");
              planner.setContextValue("script_id", "55");
              planner.setContextValue("timeline_id", "66");
              planner.setContextValue("timeline_version", "7");
              planner.setContextValue("clip_id", "clip-8");
            }}
          >
            select production lineage
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
      fireEvent.click(
        utils.getByRole("button", { name: "select production lineage" }),
      );
      fireEvent.click(utils.getByRole("button", { name: "execute" }));

      await waitFor(() => assert.equal(executeRequests.length, 1));
      assert.equal(executeRequests[0]?.run_id, "current-run");
      assert.equal(executeRequests[0]?.virtual_ip_id, 11);
      assert.equal(executeRequests[0]?.environment_id, 22);
      assert.equal(executeRequests[0]?.story_id, 33);
      assert.equal(executeRequests[0]?.episode_id, 44);
      assert.equal(executeRequests[0]?.script_id, 55);
      assert.equal(executeRequests[0]?.timeline_id, 66);
      assert.equal(executeRequests[0]?.timeline_version, 7);
      assert.equal(executeRequests[0]?.clip_id, "clip-8");
      assert.deepEqual(executeRequests[0]?.reference_artifacts, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("does not publish a late Run A execute response into Run B", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    let resolveExecute: ((response: Response) => void) | undefined;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/")) {
        const runId = url.endsWith("run-a") ? "run-a" : "run-b";
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: runId,
              task_id: 1,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      return new Promise<Response>((resolve) => {
        resolveExecute = resolve;
      });
    };

    function Harness({ runId }: { runId: string }) {
      const planner = useProductionCanvasSkillPlanner({
        currentRunId: runId,
        getCurrentRunId: () => runId,
        nodes: [staleRunNode],
        onNodesCreated: (nodes) => updates.push(nodes),
      });
      return (
        <button
          type="button"
          onClick={() => void planner.executeSkillNode(staleRunNode)}
        >
          execute {runId}
        </button>
      );
    }

    try {
      const utils = render(<Harness runId="run-a" />, {
        container: dom.window.document.body,
      });
      fireEvent.click(utils.getByRole("button", { name: "execute run-a" }));
      await waitFor(() => assert.ok(resolveExecute));
      utils.rerender(<Harness runId="run-b" />);
      await act(async () => {
        resolveExecute?.(
          new Response(
            JSON.stringify({
              success: true,
              data: {
                skill_result: {
                  label: "Asset Selection",
                  title: "Run A late result",
                  status: "review",
                  outputs: { canvas_run_id: "run-a" },
                  reuse_targets: [],
                },
              },
            }),
            { headers: { "content-type": "application/json" } },
          ),
        );
      });
      assert.deepEqual(updates, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("does not adopt a late Run A plan after routing to Run B", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const resolvedContexts: unknown[] = [];
    const createdRuns: string[] = [];
    let resolvePlan: ((response: Response) => void) | undefined;
    let createPlan: (() => Promise<void>) | undefined;
    let setPrompt: ((value: string) => void) | undefined;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/")) {
        const runId = url.endsWith("run-a") ? "run-a" : "run-b";
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: runId,
              task_id: 1,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      return new Promise<Response>((resolve) => {
        resolvePlan = resolve;
      });
    };

    function Harness({ runId }: { runId: string }) {
      const planner = useProductionCanvasSkillPlanner({
        currentRunId: runId,
        getCurrentRunId: () => runId,
        nodes: [staleRunNode],
        onDomainContextResolved: (context) => resolvedContexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        onRunCreated: (createdRunId) => createdRuns.push(createdRunId),
      });
      useEffect(() => {
        createPlan = planner.createFromPrompt;
        setPrompt = planner.setPrompt;
      });
      return (
        <>
          <input
            aria-label="prompt"
            value={planner.prompt}
            onChange={(event) => planner.setPrompt(event.target.value)}
          />
          <button type="button" onClick={() => void planner.createFromPrompt()}>
            create {runId}
          </button>
        </>
      );
    }

    try {
      const utils = render(<Harness runId="run-a" />, {
        container: dom.window.document.body,
      });
      act(() => setPrompt?.("Run A plan"));
      act(() => void createPlan?.());
      await waitFor(() => assert.ok(resolvePlan));
      utils.rerender(<Harness runId="run-b" />);
      await act(async () => {
        resolvePlan?.(
          new Response(
            JSON.stringify({
              success: true,
              data: {
                run_id: "run-a-new",
                task_id: 9,
                resolved_context: { story_id: 10 },
                nodes: [],
                selected_assets: { virtual_ips: [], environments: [] },
                skill_manifest: { version: "production_canvas.v1" },
              },
            }),
            { headers: { "content-type": "application/json" } },
          ),
        );
      });
      assert.deepEqual(updates, []);
      assert.deepEqual(resolvedContexts, []);
      assert.deepEqual(createdRuns, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("does not adopt a late fresh-canvas plan after reset keeps a null Run", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const contexts: unknown[] = [];
    const runs: string[] = [];
    let resolvePlan: ((response: Response) => void) | undefined;
    let createPlan: (() => Promise<void>) | undefined;
    let setPrompt: ((value: string) => void) | undefined;
    globalThis.fetch = async () =>
      new Promise<Response>((resolve) => {
        resolvePlan = resolve;
      });

    function Harness({ epoch }: { epoch: number }) {
      const planner = useProductionCanvasSkillPlanner({
        captureStateIdentity: () => ({ runId: "", epoch }),
        currentRunId: null,
        getCurrentRunId: () => null,
        nodes: [],
        onDomainContextResolved: (context) => contexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        onRunCreated: (runId) => runs.push(runId),
      });
      useEffect(() => {
        createPlan = planner.createFromPrompt;
        setPrompt = planner.setPrompt;
      });
      return (
        <>
          <input
            aria-label="fresh prompt"
            value={planner.prompt}
            onChange={(event) => planner.setPrompt(event.target.value)}
          />
          <button type="button" onClick={() => void planner.createFromPrompt()}>
            create fresh
          </button>
          <span data-testid="running">{String(planner.running)}</span>
        </>
      );
    }

    try {
      const utils = render(<Harness epoch={0} />, {
        container: dom.window.document.body,
      });
      act(() => setPrompt?.("fresh plan"));
      act(() => void createPlan?.());
      await waitFor(() => assert.ok(resolvePlan));
      utils.rerender(<Harness epoch={1} />);
      await waitFor(() =>
        assert.equal(utils.getByTestId("running").textContent, "false"),
      );
      await act(
        async () =>
          resolvePlan?.(
            new Response(
              JSON.stringify({
                success: true,
                data: {
                  run_id: "late-created-run",
                  task_id: 9,
                  resolved_context: { story_id: 10 },
                  nodes: [],
                  selected_assets: { virtual_ips: [], environments: [] },
                  skill_manifest: { version: "production_canvas.v1" },
                },
              }),
              { headers: { "content-type": "application/json" } },
            ),
          ),
      );
      assert.deepEqual(updates, []);
      assert.deepEqual(contexts, []);
      assert.deepEqual(runs, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
