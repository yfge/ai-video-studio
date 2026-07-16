import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { createElement } from "react";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { productionCanvasAPI } from "../src/utils/api/endpoints";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";
import { toProductionCanvasSavedState } from "../src/components/features/canvas/productionCanvasPersistence";
import { ProductionCanvasCandidateReview } from "../src/components/features/canvas/ProductionCanvasCandidateReview";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

const originalApprove = productionCanvasAPI.approveNodeCandidate;
const originalCandidates = productionCanvasAPI.getNodeCandidates;
const node: ProductionCanvasNode = {
  id: "candidate-node",
  kind: "skill_result",
  label: "图片候选",
  outputs: {},
  skill: "image.candidates",
  status: "ready",
  title: "图片候选",
  width: 220,
  x: 0,
  y: 0,
};
const candidateResponse = {
  success: true as const,
  data: {
    candidates: [
      {
        asset_business_id: "asset-11",
        asset_id: 11,
        frame_index: 0,
        media_type: "image" as const,
        review_state: "pending" as const,
        selected: false,
        url: "https://example.com/candidate.png",
      },
    ],
    node_id: node.id,
    selected_output_id: null,
    stale_impact: [],
  },
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function runResponse(runId: string) {
  const state = createProductionCanvasState();
  return {
    prompt: "candidate review",
    run_id: runId,
    skill_manifest: { version: "1" },
    selected_assets: { virtual_ips: [], environments: [] },
    nodes: [],
    saved_state: toProductionCanvasSavedState(state),
  };
}

afterEach(() => {
  cleanup();
  productionCanvasAPI.approveNodeCandidate = originalApprove;
  productionCanvasAPI.getNodeCandidates = originalCandidates;
  dom.window.document.body.replaceChildren();
});

describe("ProductionCanvas candidate Run identity", () => {
  it("drops a mutation response after switching Runs and blocks mismatched requests", async () => {
    productionCanvasAPI.getNodeCandidates = async () => candidateResponse;
    type ApproveResult = Awaited<
      ReturnType<typeof productionCanvasAPI.approveNodeCandidate>
    >;
    const approval = deferred<ApproveResult>();
    let approvalCalls = 0;
    productionCanvasAPI.approveNodeCandidate = () => {
      approvalCalls += 1;
      return approval.promise;
    };
    let identity = { epoch: 1, runId: "run-a" };
    const captureIdentity = () => ({ ...identity });
    let adopted = 0;
    const props = () => ({
      captureCanvasStateIdentity: captureIdentity,
      node,
      onCanvasStateUpdated: () => {
        adopted += 1;
        return true;
      },
      runId: "run-a",
    });
    const utils = render(
      createElement(ProductionCanvasCandidateReview, props()),
      {
        container: dom.window.document.body,
      },
    );
    await waitFor(() => assert.ok(utils.getByRole("button", { name: "选用" })));

    fireEvent.click(utils.getByRole("button", { name: "选用" }));
    await waitFor(() => assert.equal(approvalCalls, 1));
    identity = { epoch: 2, runId: "run-b" };
    utils.rerender(createElement(ProductionCanvasCandidateReview, props()));
    approval.resolve({ success: true, data: runResponse("run-a") });
    await waitFor(() =>
      assert.equal(
        utils.getByRole("button", { name: "选用" }).hasAttribute("disabled"),
        false,
      ),
    );
    assert.equal(adopted, 0);

    fireEvent.click(utils.getByRole("button", { name: "选用" }));
    assert.equal(approvalCalls, 1);
  });

  it("drops an old candidate load without leaving the panel busy", async () => {
    type CandidateResult = Awaited<
      ReturnType<typeof productionCanvasAPI.getNodeCandidates>
    >;
    const candidates = deferred<CandidateResult>();
    productionCanvasAPI.getNodeCandidates = () => candidates.promise;
    let identity = { epoch: 1, runId: "run-a" };
    const captureIdentity = () => ({ ...identity });
    const utils = render(
      createElement(ProductionCanvasCandidateReview, {
        captureCanvasStateIdentity: captureIdentity,
        node,
        onCanvasStateUpdated: () => true,
        runId: "run-a",
      }),
      { container: dom.window.document.body },
    );
    await waitFor(() => assert.ok(utils.getByText("加载中")));
    identity = { epoch: 2, runId: "run-b" };
    candidates.resolve(candidateResponse);

    await waitFor(() => assert.ok(utils.getByText("刷新")));
    assert.equal(utils.queryByRole("button", { name: "选用" }), null);
    assert.ok(utils.getByText("暂无可评审候选。"));
  });
});
