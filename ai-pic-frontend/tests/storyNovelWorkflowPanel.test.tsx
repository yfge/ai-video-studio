import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { parseCharacterArcs } from "../src/components/features/story-detail/StoryNovelAdaptationEpisodeCard";
import { StoryNovelWorkflowPanel } from "../src/components/features/story-detail/StoryNovelWorkflowPanel";
import type { Story, StoryNovelRevision } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).HTMLTextAreaElement = dom.window.HTMLTextAreaElement;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).localStorage = dom.window.localStorage;

describe("StoryNovelWorkflowPanel", () => {
  afterEach(() => cleanup());

  it("loads a draft, saves a chapter with optimistic timestamp, and keeps paid checks explicit", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({ url, init });
      if (init?.method === "PATCH" && url.includes("/chapters/")) {
        const body = JSON.parse(String(init.body));
        return response({
          ...revision.chapters[0],
          ...body,
          updated_at: "2026-07-22T01:00:01Z",
        });
      }
      return response({ items: [revision], canonical_business_id: null });
    };
    try {
      const utils = render(
        <StoryNovelWorkflowPanel
          story={story}
          onEpisodesApplied={async () => undefined}
        />,
        { container: dom.window.document.body },
      );
      await waitFor(() => assert.ok(utils.getByDisplayValue("第一章")));
      assert.ok(utils.getByText("2. 小说版本与章节编辑"));
      assert.ok(utils.getByRole("button", { name: "运行连续性检查" }));

      fireEvent.input(utils.getByLabelText("第1章正文"), {
        target: { value: "编辑后的正文" },
      });
      assert.equal(
        (utils.getByLabelText("第1章正文") as HTMLTextAreaElement).value,
        "编辑后的正文",
      );
      fireEvent.click(utils.getByRole("button", { name: "保存章节" }));
      await waitFor(() =>
        assert.ok(requests.some((item) => item.init?.method === "PATCH")),
      );
      const save = requests.find((item) => item.init?.method === "PATCH");
      const payload = JSON.parse(String(save?.init?.body));
      assert.equal(payload.content_text, "编辑后的正文");
      assert.equal(payload.expected_updated_at, "2026-07-22T01:00:00Z");
      assert.equal(
        requests.filter((item) => item.url.includes("continuity-check")).length,
        0,
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("parses editable character arcs as simple per-line mappings", () => {
    assert.deepEqual(parseCharacterArcs("主角: 接受责任\n反派: 暴露弱点"), {
      主角: "接受责任",
      反派: "暴露弱点",
    });
  });
});

const story: Story = {
  id: 1,
  business_id: "story-business-id",
  title: "链路故事",
  genre: "drama",
  workflow_mode: "novel_adaptation_v1",
  status: "draft",
  is_public: false,
  created_at: "2026-07-22T00:00:00Z",
  updated_at: "2026-07-22T00:00:00Z",
};

const revision: StoryNovelRevision = {
  id: 10,
  business_id: "revision-business-id",
  story_business_id: story.business_id,
  style: "prose",
  target_words: 10000,
  chapter_count: 1,
  total_words: 4,
  revision_number: 1,
  lifecycle_status: "draft",
  continuity_status: "unchecked",
  adaptation_plan_status: "empty",
  created_at: "2026-07-22T00:00:00Z",
  updated_at: "2026-07-22T01:00:00Z",
  chapters: [
    {
      business_id: "chapter-business-id",
      position: 1,
      title: "第一章",
      content_text: "原始正文",
      summary: "摘要",
      review_status: "ready",
      updated_at: "2026-07-22T01:00:00Z",
    },
  ],
};

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    headers: { "content-type": "application/json" },
  });
}
