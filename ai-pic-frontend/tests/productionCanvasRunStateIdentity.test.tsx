import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { useRef, useState } from "react";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { productionCanvasAPI } from "../src/utils/api/endpoints";
import type { ProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";
import type { ProductionCanvasStateIdentity } from "../src/components/features/canvas/productionCanvasStateIdentity";
import { useProductionCanvasRunPersistence } from "../src/components/features/canvas/useProductionCanvasRunPersistence";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

const canvasState = (label: string): ProductionCanvasState => ({
  edges: [],
  nodes: [
    {
      id: label,
      kind: "note",
      label,
      status: "ready",
      title: label,
      width: 220,
      x: 0,
      y: 0,
    },
  ],
  selectedNodeId: null,
  viewport: { x: 0, y: 0, zoom: 1 },
});
const originalGetRun = productionCanvasAPI.getRun;
const originalSaveRunState = productionCanvasAPI.saveRunState;

afterEach(() => {
  productionCanvasAPI.getRun = originalGetRun;
  productionCanvasAPI.saveRunState = originalSaveRunState;
  cleanup();
  dom.window.history.replaceState(null, "", "/canvas");
  dom.window.document.body.replaceChildren();
});

describe("ProductionCanvas Run state identity", () => {
  it("rejects state captured before switching to another Run", () => {
    function Harness() {
      const [state, setState] = useState(() => canvasState("current"));
      const captured = useRef<ProductionCanvasStateIdentity | null>(null);
      const [adopted, setAdopted] = useState<boolean | null>(null);
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: state,
        replaceCanvasState: setState,
      });
      return (
        <>
          <button onClick={() => persistence.setRunId("run-a", "owner")}>
            use A
          </button>
          <button
            onClick={() => {
              captured.current = persistence.captureStateIdentity();
            }}
          >
            capture
          </button>
          <button onClick={() => persistence.setRunId("run-b", "owner")}>
            use B
          </button>
          <button
            onClick={() =>
              setAdopted(
                persistence.adoptServerState(
                  canvasState("stale"),
                  captured.current!,
                ),
              )
            }
          >
            adopt stale
          </button>
          <output data-testid="node">{state.nodes[0]?.label}</output>
          <output data-testid="adopted">{String(adopted)}</output>
        </>
      );
    }

    const utils = render(<Harness />, { container: dom.window.document.body });
    fireEvent.click(utils.getByRole("button", { name: "use A" }));
    fireEvent.click(utils.getByRole("button", { name: "capture" }));
    fireEvent.click(utils.getByRole("button", { name: "use B" }));
    fireEvent.click(utils.getByRole("button", { name: "adopt stale" }));

    assert.equal(utils.getByTestId("node").textContent, "current");
    assert.equal(utils.getByTestId("adopted").textContent, "false");
  });

  it("keeps the confirmed Run identity when restoring another Run fails", async () => {
    productionCanvasAPI.getRun = async () => ({
      success: false,
      error: "restore failed",
    });

    function Harness() {
      const [state, setState] = useState(() => canvasState("current"));
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: state,
        replaceCanvasState: setState,
      });
      return (
        <>
          <button onClick={() => persistence.setRunId("run-a", "owner")}>
            use A
          </button>
          <button onClick={() => void persistence.restoreCanvas("run-b")}>
            restore B
          </button>
          <output data-testid="active">{persistence.runId}</output>
          <output data-testid="identity">
            {persistence.captureStateIdentity().runId}
          </output>
          <output data-testid="status">{persistence.status}</output>
        </>
      );
    }

    const utils = render(<Harness />, { container: dom.window.document.body });
    fireEvent.click(utils.getByRole("button", { name: "use A" }));
    fireEvent.click(utils.getByRole("button", { name: "restore B" }));
    await waitFor(() =>
      assert.equal(utils.getByTestId("status").textContent, "restore failed"),
    );
    assert.equal(utils.getByTestId("active").textContent, "run-a");
    assert.equal(utils.getByTestId("identity").textContent, "run-a");
  });

  it("does not invalidate the canvas session identity when saving", async () => {
    productionCanvasAPI.saveRunState = async (runId) => ({
      success: true,
      data: { run_id: runId, access_role: "owner" } as any,
    });

    function Harness() {
      const [state, setState] = useState(() => canvasState("current"));
      const [sameIdentity, setSameIdentity] = useState<boolean | null>(null);
      const persistence = useProductionCanvasRunPersistence({
        autosaveDelayMs: null,
        canvasState: state,
        replaceCanvasState: setState,
      });
      return (
        <>
          <button onClick={() => persistence.setRunId("run-a", "owner")}>
            use A
          </button>
          <button
            onClick={async () => {
              const before = persistence.captureStateIdentity();
              await persistence.saveCanvas();
              const after = persistence.captureStateIdentity();
              setSameIdentity(
                before.runId === after.runId && before.epoch === after.epoch,
              );
            }}
          >
            save
          </button>
          <output data-testid="same">{String(sameIdentity)}</output>
        </>
      );
    }

    const utils = render(<Harness />, { container: dom.window.document.body });
    fireEvent.click(utils.getByRole("button", { name: "use A" }));
    fireEvent.click(utils.getByRole("button", { name: "save" }));
    await waitFor(() =>
      assert.equal(utils.getByTestId("same").textContent, "true"),
    );
  });
});
