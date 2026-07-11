import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasCollaborationPanel } from "../src/components/features/canvas/ProductionCanvasCollaborationPanel";
import type { ProductionCanvasCollaborationResponse } from "../src/utils/api/types";

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

const baseData: ProductionCanvasCollaborationResponse = {
  access_role: "owner",
  collaborators: [],
  comments: [],
  activity: [],
};

describe("ProductionCanvasCollaborationPanel", () => {
  afterEach(() => cleanup());

  it("comments on canvas identities and manages collaborators", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ body?: any; method?: string; url: string }> = [];
    let data = baseData;
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      requests.push({ body, method: init?.method, url });
      if (url.endsWith("/candidates")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              candidates: [
                {
                  asset_business_id: "asset-81",
                  asset_id: 81,
                  frame_index: 0,
                  media_type: "image",
                  review_state: "pending",
                  selected: false,
                  url: "https://example.com/81.png",
                },
              ],
              node_id: "image-review",
              stale_impact: [],
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url.endsWith("/comments") && init?.method === "POST") {
        data = {
          ...data,
          comments: [
            {
              author_id: 1,
              author_username: "owner",
              body: body.body,
              comment_id: "comment-1",
              created_at: "2026-07-11T17:00:00Z",
              target_id: body.target_id,
              target_type: body.target_type,
            },
          ],
        };
      }
      if (url.endsWith("/collaborators") && init?.method === "PUT") {
        data = {
          ...data,
          collaborators: [
            {
              added_at: "2026-07-11T17:00:00Z",
              added_by: 1,
              role: body.role,
              user_id: 2,
              username: body.username,
            },
          ],
        };
      }
      return new Response(JSON.stringify({ success: true, data }), {
        headers: { "content-type": "application/json" },
      });
    };

    try {
      const utils = render(
        <ProductionCanvasCollaborationPanel
          accessRole="owner"
          edges={[
            {
              edgeId: "image-to-video",
              from: "image-review",
              to: "video-review",
            },
          ]}
          node={{
            id: "image-review",
            kind: "pipeline",
            label: "图片候选",
            skill: "image.candidates",
            status: "review",
            title: "图片候选",
            width: 220,
            x: 0,
            y: 0,
          }}
          nodes={[
            {
              id: "image-review",
              label: "图片候选",
              status: "review",
              title: "图片候选",
              width: 220,
              x: 0,
              y: 0,
            },
          ]}
          runId="canvas-collaboration"
          sections={[
            {
              height: 300,
              id: "scene-1",
              nodeIds: ["image-review"],
              scope: "scene",
              title: "场景一",
              width: 400,
              x: 0,
              y: 0,
            },
          ]}
        />,
        { container: dom.window.document.body },
      );

      await waitFor(() => assert.ok(utils.getByText("所有者")));
      await waitFor(() =>
        assert.ok(utils.getByRole("option", { name: "图片候选 · #81" })),
      );
      assert.ok(utils.getByRole("option", { name: "节点 · 图片候选" }));
      assert.ok(
        utils.getByRole("option", {
          name: "连线 · image-review → video-review",
        }),
      );
      assert.ok(utils.getByRole("option", { name: "分区 · 场景一" }));

      fireEvent.change(utils.getByLabelText("评论目标"), {
        target: { value: "candidate:81" },
      });
      fireEvent.input(utils.getByLabelText("协作评论"), {
        target: { value: "保留角色一致性" },
      });
      fireEvent.click(utils.getByRole("button", { name: "发表评论" }));
      await waitFor(() => assert.ok(utils.getByText("保留角色一致性")));
      const commentRequest = requests.find((item) =>
        item.url.endsWith("/comments"),
      );
      assert.deepEqual(commentRequest?.body, {
        body: "保留角色一致性",
        target_id: "81",
        target_type: "candidate",
      });

      fireEvent.click(utils.getByRole("button", { name: "成员" }));
      fireEvent.input(utils.getByLabelText("协作者用户名"), {
        target: { value: "reviewer" },
      });
      fireEvent.change(utils.getByLabelText("协作者角色"), {
        target: { value: "approver" },
      });
      fireEvent.click(utils.getByRole("button", { name: "添加" }));
      await waitFor(() => assert.ok(utils.getByText("reviewer")));
      const memberRequest = requests.find(
        (item) => item.url.endsWith("/collaborators") && item.method === "PUT",
      );
      assert.deepEqual(memberRequest?.body, {
        role: "approver",
        username: "reviewer",
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
