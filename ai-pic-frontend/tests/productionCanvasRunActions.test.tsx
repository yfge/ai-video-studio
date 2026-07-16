import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { productionCanvasAPI } from "../src/utils/api/endpoints";
import type { ProductionCanvasRunActionRequest } from "../src/utils/api/types";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";
import { toProductionCanvasSavedState } from "../src/components/features/canvas/productionCanvasPersistence";
import { useProductionCanvasRunActions } from "../src/components/features/canvas/useProductionCanvasRunActions";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

const originalControlRun = productionCanvasAPI.controlRun;

describe("production canvas run actions", () => {
  afterEach(() => {
    productionCanvasAPI.controlRun = originalControlRun;
    cleanup();
  });

  it("saves before execution, adopts server state, and cancels immediately", async () => {
    const calls: string[] = [];
    const requests: ProductionCanvasRunActionRequest[] = [];
    const state = createProductionCanvasState();
    const serverRun = {
      prompt: "恢复运行",
      run_id: "canvas-run-1",
      skill_manifest: { version: "1" },
      selected_assets: { virtual_ips: [], environments: [] },
      nodes: [],
      saved_state: toProductionCanvasSavedState(state),
    };
    productionCanvasAPI.controlRun = async (_runId, request) => {
      calls.push("control");
      requests.push(request);
      return {
        success: true,
        data: {
          action: request.action,
          definition_mode: request.definition_mode || "current",
          run: serverRun,
          executions: [],
          execution_order: [],
          skipped_node_ids: [],
          cancelled_task_ids: [],
        },
      };
    };
    let adoptedNodeCount = 0;
    function Harness() {
      const actions = useProductionCanvasRunActions({
        captureStateIdentity: () => ({
          epoch: 0,
          runId: "canvas-run-1",
        }),
        runId: "canvas-run-1",
        saveCanvas: async () => {
          calls.push("save");
          return true;
        },
        onStateUpdated: (next) => {
          adoptedNodeCount = next.nodes.length;
          return true;
        },
      });
      return (
        <>
          <button onClick={() => void actions.runReady()}>ready</button>
          <button onClick={() => void actions.cancel()}>cancel</button>
          <button
            onClick={() => void actions.retry(state.nodes[0], "original")}
          >
            retry
          </button>
          <span>{actions.status}</span>
        </>
      );
    }
    const utils = render(<Harness />, { container: dom.window.document.body });

    fireEvent.click(utils.getByRole("button", { name: "ready" }));
    await waitFor(() =>
      assert.match(utils.getByText(/已运行/).textContent || "", /已运行/),
    );
    assert.deepEqual(calls, ["save", "control"]);
    assert.equal(adoptedNodeCount, state.nodes.length);

    calls.length = 0;
    fireEvent.click(utils.getByRole("button", { name: "cancel" }));
    await waitFor(() => assert.equal(requests.at(-1)?.action, "cancel"));
    assert.deepEqual(calls, ["control"]);

    calls.length = 0;
    fireEvent.click(utils.getByRole("button", { name: "retry" }));
    await waitFor(() => assert.equal(requests.at(-1)?.action, "retry"));
    assert.deepEqual(calls, ["save", "control"]);
    assert.equal(requests.at(-1)?.definition_mode, "original");
  });

  it("ignores a Run response after the active Run identity changes", async () => {
    type ControlRunResult = Awaited<
      ReturnType<typeof productionCanvasAPI.controlRun>
    >;
    let resolveControl!: (result: ControlRunResult) => void;
    productionCanvasAPI.controlRun = () =>
      new Promise((resolve) => {
        resolveControl = resolve;
      });
    let currentIdentity = { epoch: 1, runId: "run-a" };
    let adoptAttempts = 0;

    function Harness({ runId }: { runId: string }) {
      const actions = useProductionCanvasRunActions({
        captureStateIdentity: () => ({ ...currentIdentity }),
        onStateUpdated: (_state, identity) => {
          adoptAttempts += 1;
          return (
            identity.runId === currentIdentity.runId &&
            identity.epoch === currentIdentity.epoch
          );
        },
        runId,
        saveCanvas: async () => true,
      });
      return (
        <>
          <button
            disabled={Boolean(actions.busyAction)}
            onClick={() => void actions.cancel()}
          >
            cancel
          </button>
          <span data-testid="status">{actions.status}</span>
        </>
      );
    }

    const utils = render(<Harness runId="run-a" />, {
      container: dom.window.document.body,
    });
    fireEvent.click(utils.getByRole("button", { name: "cancel" }));
    await waitFor(() => assert.ok(resolveControl));
    currentIdentity = { epoch: 2, runId: "run-b" };
    utils.rerender(<Harness runId="run-b" />);
    await waitFor(() =>
      assert.equal(
        utils.getByRole("button", { name: "cancel" }).hasAttribute("disabled"),
        false,
      ),
    );
    resolveControl({
      success: true,
      data: {
        action: "cancel",
        definition_mode: "current",
        run: {
          prompt: "stale Run",
          run_id: "run-a",
          skill_manifest: { version: "1" },
          selected_assets: { virtual_ips: [], environments: [] },
          nodes: [],
          saved_state: toProductionCanvasSavedState(
            createProductionCanvasState(),
          ),
        },
        executions: [],
        execution_order: [],
        skipped_node_ids: [],
        cancelled_task_ids: [],
      },
    });

    await waitFor(() =>
      assert.equal(
        utils.getByRole("button", { name: "cancel" }).hasAttribute("disabled"),
        false,
      ),
    );
    assert.equal(adoptAttempts, 1);
    assert.equal(utils.getByTestId("status").textContent, "");
  });
});
