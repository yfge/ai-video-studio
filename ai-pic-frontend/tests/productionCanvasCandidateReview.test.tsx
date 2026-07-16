import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import { createElement } from "react";

import { ProductionCanvasCandidateReview } from "../src/components/features/canvas/ProductionCanvasCandidateReview";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import type { ProductionCanvasRunResponse } from "../src/utils/api/types";
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
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const imageNode: ProductionCanvasNode = {
  id: "image-review",
  kind: "pipeline",
  label: "Image Candidates",
  skill: "image.candidates",
  status: "review",
  title: "图片候选",
  width: 220,
  x: 0,
  y: 0,
};

function runResponse(candidateId: number | null): ProductionCanvasRunResponse {
  const url =
    candidateId === 11
      ? "https://example.com/old.png"
      : "https://example.com/latest.png";
  return {
    prompt: "评审图片",
    run_id: "canvas-review-run",
    nodes: [],
    selected_assets: { virtual_ips: [], environments: [] },
    skill_manifest: { version: "production_canvas.v1" },
    saved_state: {
      edges: [],
      nodes: [
        {
          id: "image-review",
          kind: "pipeline",
          label: "Image Candidates",
          skill: "image.candidates",
          status: candidateId ? "approved" : "review",
          title: "图片候选",
          width: 220,
          x: 0,
          y: 0,
          ...(candidateId
            ? { selected_output_id: candidateId, selected_output_url: url }
            : {}),
        },
      ],
      selected_node_id: "image-review",
      viewport: { x: 0, y: 0, zoom: 1 },
    },
  } as ProductionCanvasRunResponse;
}

describe("ProductionCanvasCandidateReview", () => {
  afterEach(() => cleanup());

  it("previews persisted candidates and adopts an explicit approval", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ body?: string; method?: string; url: string }> = [];
    let updatedState: ProductionCanvasState | null = null;
    let approvedCandidateId: number | null = null;
    let rejectedCandidateId: number | null = null;
    let rejectionReason: string | null = null;
    let branchCandidateId: number | null = null;
    let branchInstruction: string | null = null;
    const captureCanvasStateIdentity = () => ({
      epoch: 0,
      runId: "canvas-review-run",
    });
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({
        body: String(init?.body || ""),
        method: init?.method,
        url,
      });
      if (url.endsWith("/approval")) {
        approvedCandidateId = Number(
          JSON.parse(String(init?.body)).candidate_id,
        );
        return new Response(
          JSON.stringify({
            success: true,
            data: runResponse(approvedCandidateId),
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url.endsWith("/rejection")) {
        const body = JSON.parse(String(init?.body));
        rejectedCandidateId = Number(body.candidate_id);
        rejectionReason = body.reason;
        approvedCandidateId = null;
        return new Response(
          JSON.stringify({ success: true, data: runResponse(null) }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url.endsWith("/branches")) {
        const body = JSON.parse(String(init?.body));
        branchCandidateId = Number(body.candidate_id);
        branchInstruction = body.instruction;
        return new Response(
          JSON.stringify({ success: true, data: runResponse(null) }),
          { headers: { "content-type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            node_id: "image-review",
            selected_output_id: approvedCandidateId,
            stale_impact: approvedCandidateId
              ? [
                  { node_id: "video-review", title: "视频候选" },
                  {
                    node_id: "timeline-placement",
                    title: "Timeline 放置",
                  },
                ]
              : [],
            candidates: [
              {
                asset_id: 11,
                asset_business_id: "asset-old",
                media_type: "image",
                url: "https://example.com/old.png",
                frame_index: 1,
                clip_id: "clip-001",
                model: "gpt-image-2",
                selected: approvedCandidateId === 11,
                review_state:
                  rejectedCandidateId === 11
                    ? "rejected"
                    : approvedCandidateId === 11
                    ? "approved"
                    : "pending",
                rejection_reason:
                  rejectedCandidateId === 11 ? rejectionReason : null,
              },
              {
                asset_id: 12,
                asset_business_id: "asset-latest",
                media_type: "image",
                url: "https://example.com/latest.png",
                frame_index: 1,
                clip_id: "clip-001",
                model: "gpt-image-2",
                selected: approvedCandidateId === 12,
                review_state:
                  rejectedCandidateId === 12
                    ? "rejected"
                    : approvedCandidateId === 12
                    ? "approved"
                    : "pending",
                rejection_reason:
                  rejectedCandidateId === 12 ? rejectionReason : null,
              },
            ],
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    try {
      const utils = render(
        createElement(ProductionCanvasCandidateReview, {
          captureCanvasStateIdentity,
          node: imageNode,
          runId: "canvas-review-run",
          onCanvasStateUpdated: (state) => {
            updatedState = state;
            return true;
          },
        }),
        { container: dom.window.document.body },
      );

      await waitFor(() => assert.equal(utils.getAllByRole("img").length, 2));
      assert.ok(utils.getAllByText("帧 2 · Clip clip-001 · gpt-image-2"));

      fireEvent.click(utils.getAllByRole("button", { name: "从此分支" })[0]);
      fireEvent.input(utils.getByLabelText("分支指令（可选）"), {
        target: { value: "保留构图，改成夜景" },
      });
      fireEvent.click(utils.getByRole("button", { name: "开始生成" }));
      await waitFor(() => assert.equal(branchCandidateId, 11));
      assert.equal(branchInstruction, "保留构图，改成夜景");
      assert.ok(utils.getByRole("status"));
      const branchRequest = requests.find((request) =>
        request.url.endsWith("/branches"),
      );
      assert.equal(branchRequest?.method, "POST");
      assert.deepEqual(JSON.parse(branchRequest?.body || "{}"), {
        candidate_id: 11,
        instruction: "保留构图，改成夜景",
      });
      const candidateLoadsAfterBranch = requests.filter((request) =>
        request.url.endsWith("/candidates"),
      ).length;
      utils.rerender(
        createElement(ProductionCanvasCandidateReview, {
          captureCanvasStateIdentity,
          node: { ...imageNode, status: "running" },
          runId: "canvas-review-run",
          onCanvasStateUpdated: (state) => {
            updatedState = state;
            return true;
          },
        }),
      );
      await waitFor(() => assert.ok(utils.getByRole("status")));
      assert.equal(
        requests.filter((request) => request.url.endsWith("/candidates"))
          .length,
        candidateLoadsAfterBranch,
      );

      fireEvent.click(utils.getAllByRole("button", { name: "选用" })[0]);
      await waitFor(() =>
        assert.ok(utils.getByRole("button", { name: "已选用" })),
      );
      assert.equal(
        requests.filter((request) => request.url.endsWith("/candidates"))
          .length,
        2,
      );

      fireEvent.click(utils.getByRole("button", { name: "选用" }));

      assert.ok(utils.getByText("切换后以下节点将标记为已过期："));
      assert.ok(utils.getByText("视频候选、Timeline 放置"));
      assert.equal(
        requests.filter((request) => request.url.endsWith("/approval")).length,
        1,
      );
      fireEvent.click(utils.getByRole("button", { name: "确认切换" }));

      await waitFor(() => assert.equal(approvedCandidateId, 12));
      assert.equal(updatedState?.nodes[0]?.selectedOutputId, 12);
      const approval = requests
        .filter((request) => request.url.endsWith("/approval"))
        .at(-1);
      assert.equal(approval?.method, "POST");
      assert.deepEqual(JSON.parse(approval?.body || "{}"), {
        candidate_id: 12,
      });

      fireEvent.click(utils.getAllByRole("button", { name: "拒绝" })[1]);
      fireEvent.input(utils.getByLabelText("拒绝原因（可选）"), {
        target: { value: "角色外观不一致" },
      });
      fireEvent.click(utils.getByRole("button", { name: "确认拒绝" }));

      await waitFor(() =>
        assert.ok(
          requests.find((request) => request.url.endsWith("/rejection")),
        ),
      );
      const rejection = requests.find((request) =>
        request.url.endsWith("/rejection"),
      );
      assert.equal(rejection?.method, "POST");
      assert.deepEqual(JSON.parse(rejection?.body || "{}"), {
        candidate_id: 12,
        reason: "角色外观不一致",
      });
      await waitFor(() =>
        assert.match(
          dom.window.document.body.textContent || "",
          /角色外观不一致/,
        ),
      );
      assert.equal(updatedState?.nodes[0]?.status, "review");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("keeps candidates visible without review or branch commands", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          success: true,
          data: {
            candidates: [
              {
                asset_business_id: "asset-11",
                asset_id: 11,
                frame_index: 0,
                media_type: "image",
                review_state: "pending",
                selected: false,
                url: "https://example.com/old.png",
              },
            ],
            node_id: imageNode.id,
            stale_impact: [],
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    try {
      const utils = render(
        createElement(ProductionCanvasCandidateReview, {
          canApprove: false,
          canBranch: false,
          captureCanvasStateIdentity: () => ({
            epoch: 0,
            runId: "canvas-review-readonly",
          }),
          node: imageNode,
          onCanvasStateUpdated: () => true,
          runId: "canvas-review-readonly",
        }),
        { container: dom.window.document.body },
      );
      await waitFor(() => assert.ok(utils.getByText("帧 1")));
      assert.equal(utils.queryByRole("button", { name: "选用" }), null);
      assert.equal(utils.queryByRole("button", { name: "拒绝" }), null);
      assert.equal(utils.queryByText("分支生成"), null);
      assert.ok(utils.getByText("查看原始资产"));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("publishes the authoritative Timeline context after placement", async () => {
    const originalFetch = globalThis.fetch;
    const contexts: unknown[] = [];
    const videoNode: ProductionCanvasNode = {
      ...imageNode,
      id: "video-review",
      skill: "video.candidates",
      outputs: { timeline_id: 70, timeline_version: 7 },
    };
    const resolvedContext = {
      virtual_ip_id: 84,
      environment_id: 13,
      story_id: 61,
      episode_id: 174,
      script_id: 144,
      timeline_id: 70,
      timeline_version: 8,
      clip_id: "clip-8",
      task_id: 77,
    };
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.endsWith("/candidates")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              candidates: [
                {
                  asset_business_id: "video-11",
                  asset_id: 11,
                  frame_index: 0,
                  media_type: "video",
                  review_state: "approved",
                  selected: true,
                  url: "https://example.com/video.mp4",
                },
              ],
              node_id: videoNode.id,
              selected_output_id: 11,
              stale_impact: [],
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      assert.ok(url.endsWith("/timeline-placement"));
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            ...runResponse(null),
            run_id: "canvas-place-run",
            resolved_context: resolvedContext,
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    };
    try {
      const utils = render(
        createElement(ProductionCanvasCandidateReview, {
          captureCanvasStateIdentity: () => ({
            epoch: 0,
            runId: "canvas-place-run",
          }),
          node: videoNode,
          onCanvasStateUpdated: () => true,
          onDomainContextResolved: (context) => contexts.push(context),
          runId: "canvas-place-run",
        }),
        { container: dom.window.document.body },
      );
      await waitFor(() =>
        assert.ok(utils.getByRole("button", { name: "放入 Timeline" })),
      );
      fireEvent.click(utils.getByRole("button", { name: "放入 Timeline" }));
      await waitFor(() => assert.deepEqual(contexts, [resolvedContext]));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
