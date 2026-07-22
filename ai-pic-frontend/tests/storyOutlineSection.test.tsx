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

  it("renders the production contract for a new story", () => {
    const utils = render(<StoryOutlineSection story={newStory()} />, {
      container: dom.window.document.body,
    });

    assert.ok(utils.getByText("1. 故事合同"));
    assert.ok(utils.getByText("都市职场短剧用户"));
    assert.ok(utils.getByText("前三集拿到会议录音"));
    assert.ok(utils.getByText("手机录音反击"));
  });

  it("stays hidden for a legacy story without a production contract", () => {
    const utils = render(<StoryOutlineSection story={legacyStory()} />, {
      container: dom.window.document.body,
    });

    assert.equal(utils.queryByText("1. 故事合同"), null);
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
    extra_metadata: {
      structured_story_contract: {
        target_audience: "都市职场短剧用户",
        core_emotional_pain: "信任被团队背叛",
        big_expectation: "查清数据篡改真相",
        small_expectation_ladder: ["前三集拿到会议录音"],
        protagonist_goal: "三天内拿到证据",
        structural_conflict: "必须借对手资源调查对手",
        information_gap: "观众知道录音存在，对手不知道",
        first_three_episode_spine: "身份、证据、核心冲突",
        stage_highs: ["会议室反击"],
        shootability: "办公室、会议室、走廊可拍",
        compliance_risks: [],
        traffic_hooks: ["手机录音反击"],
      },
    },
  };
}
