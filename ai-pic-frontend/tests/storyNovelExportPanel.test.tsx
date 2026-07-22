import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryNovelExportPanel } from "../src/components/features/story-detail/StoryNovelExportPanel";
import type { Story } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

describe("StoryNovelExportPanel", () => {
  afterEach(() => cleanup());

  it("keeps the novel entry visible and creates an async export task", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({ url, init });
      const data = url.endsWith("/novel/generate-async")
        ? { success: true, data: { task_id: 55, status: "pending" } }
        : {
            success: true,
            data: {
              id: 55,
              status: "pending",
              title: "导出知乎体小说",
              business_id: "task-55",
              created_at: "2026-07-19T00:00:00Z",
              user_id: 1,
            },
          };
      return new Response(JSON.stringify(data), {
        headers: { "content-type": "application/json" },
      });
    };

    try {
      const utils = render(<StoryNovelExportPanel story={story()} />, {
        container: dom.window.document.body,
      });
      assert.ok(utils.getByText("故事导成小说"));
      fireEvent.click(utils.getByRole("button", { name: "生成小说" }));

      await waitFor(() => assert.ok(utils.getByText(/任务 #55/)));
      assert.ok(requests[0]?.url.endsWith("/novel/generate-async"));
      assert.equal(
        JSON.parse(String(requests[0]?.init?.body)).target_words,
        20000,
      );
      assert.equal(
        utils.getByRole("link", { name: "查看任务" }).getAttribute("href"),
        "/tasks?task_id=55",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

function story(): Story {
  return {
    id: 1,
    business_id: "story-1",
    title: "测试故事",
    genre: "drama",
    status: "draft",
    is_public: false,
    created_at: "2026-07-19T00:00:00Z",
    updated_at: "2026-07-19T00:00:00Z",
  };
}
