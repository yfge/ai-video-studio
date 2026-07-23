import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryOutlineSection } from "../src/components/features/stories/StoryProductionDetailParts";
import type { Story } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

describe("StoryOutlineSection", () => {
  afterEach(() => cleanup());

  it("renders the Story Seed contract for a new story", () => {
    const utils = render(<StoryOutlineSection story={newStory()} />, {
      container: dom.window.document.body,
    });

    assert.ok(utils.getByText("1. 故事大纲（Story Seed）"));
    assert.ok(utils.getByText("都市职场短剧用户"));
    assert.ok(utils.getByText("查清数据篡改真相"));
    assert.ok(utils.getByText("数据证据争夺"));
  });

  it("offers a locally editable fallback seed for a legacy story", () => {
    const utils = render(<StoryOutlineSection story={legacyStory()} />, {
      container: dom.window.document.body,
    });

    assert.ok(utils.getByText("1. 故事大纲（Story Seed）"));
    assert.ok(utils.getByText("旧故事"));
  });
});

function legacyStory(): Story {
  return {
    id: 1,
    business_id: "legacy-story",
    title: "旧故事",
    genre: "drama",
    status: "draft",
    is_public: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

function newStory(): Story {
  return {
    ...legacyStory(),
    id: 2,
    business_id: "new-story",
    title: "新故事",
    story_seed_status: "confirmed",
    story_seed: {
      schema: "story_seed_v1",
      title: "新故事",
      premise: "查清数据篡改真相",
      outline: "主角从会议录音入手追查数据篡改。",
      protagonists: [
        { virtual_ip_business_id: "vip-hero", initial_state: "尚未掌握证据" },
      ],
      world_constraints: ["证据必须来自真实业务记录"],
      central_conflict: "数据证据争夺",
      ending_direction: null,
      target_audience: "都市职场短剧用户",
      content_constraints: [],
    },
  };
}
