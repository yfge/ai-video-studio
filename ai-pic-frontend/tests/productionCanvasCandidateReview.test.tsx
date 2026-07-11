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

function runResponse(candidateId: number): ProductionCanvasRunResponse {
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
          status: "approved",
          title: "图片候选",
          width: 220,
          x: 0,
          y: 0,
          selected_output_id: candidateId,
          selected_output_url: url,
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
          node: imageNode,
          runId: "canvas-review-run",
          onCanvasStateUpdated: (state) => {
            updatedState = state;
          },
        }),
        { container: dom.window.document.body },
      );

      await waitFor(() => assert.equal(utils.getAllByRole("img").length, 2));
      assert.ok(utils.getAllByText("帧 2 · Clip clip-001 · gpt-image-2"));

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
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
