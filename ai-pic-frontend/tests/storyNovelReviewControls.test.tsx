import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryNovelReviewControls } from "../src/components/features/story-detail/StoryNovelReviewControls";
import { checkStoryNovelContinuity } from "../src/utils/api/endpoints/story-novel.endpoints";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

describe("StoryNovelReviewControls", () => {
  afterEach(() => cleanup());

  it("defaults the final review to GPT-5.6 without changing generation policy", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      response({
        models: [
          {
            id: "gpt-5.6-sol",
            model_id: "codex:gpt-5.6-sol",
            name: "GPT-5.6 Sol",
            provider: "codex",
            model_type: "text",
          },
        ],
        default: "codex:gpt-5.6-sol",
      });
    let selected: string | undefined;
    try {
      const utils = render(
        <StoryNovelReviewControls
          disabled={false}
          onRun={(value) => {
            selected = value;
          }}
        />,
        { container: dom.window.document.body },
      );
      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("全书审读模型") as HTMLSelectElement).value,
          "codex:gpt-5.6-sol",
        ),
      );
      fireEvent.click(utils.getByRole("button", { name: "运行连续性检查" }));
      assert.equal(selected, "codex:gpt-5.6-sol");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("sends the selected review model in the official API request", async () => {
    const originalFetch = globalThis.fetch;
    let body: unknown;
    globalThis.fetch = async (_input, init) => {
      body = JSON.parse(String(init?.body));
      return response({ task_id: 99, status: "pending" });
    };
    try {
      await checkStoryNovelContinuity("revision-1", "codex:gpt-5.6-sol");
      assert.deepEqual(body, { review_model: "codex:gpt-5.6-sol" });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
