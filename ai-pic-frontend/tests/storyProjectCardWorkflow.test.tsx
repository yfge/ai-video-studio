import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryProjectCard } from "../src/components/features/stories/StoryProjectCard";
import type { Story } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

describe("StoryProjectCard workflow entry", () => {
  afterEach(() => cleanup());

  it("routes novel workflows to the novel gate", () => {
    const utils = renderCard("novel_adaptation_v1");
    const link = utils.getByRole("link", { name: "小说与改编" });
    assert.equal(link.getAttribute("href"), "/stories/story-1#novel-workflow");
    assert.equal(utils.queryByRole("link", { name: "生成剧集" }), null);
  });

  it("preserves the explicit direct workflow entry", () => {
    const utils = renderCard("direct");
    const link = utils.getByRole("link", { name: "生成剧集" });
    assert.equal(
      link.getAttribute("href"),
      "/stories/story-1?generate=episodes#episode-generation",
    );
  });
});

function renderCard(workflowMode: Story["workflow_mode"]) {
  return render(
    <StoryProjectCard
      story={{
        id: 1,
        business_id: "story-1",
        title: "入口边界",
        genre: "drama",
        workflow_mode: workflowMode,
        status: "draft",
        is_public: false,
        created_at: "2026-07-24T00:00:00Z",
        updated_at: "2026-07-24T00:00:00Z",
      }}
      onDelete={() => undefined}
    />,
    { container: dom.window.document.body },
  );
}
