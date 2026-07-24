import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryNovelLengthPanel } from "../src/components/features/story-detail/StoryNovelLengthPanel";
import type {
  Story,
  StoryNovelRevision,
  StoryNovelUpdateLengthSpecPayload,
} from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).HTMLInputElement = dom.window.HTMLInputElement;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).localStorage = dom.window.localStorage;

describe("StoryNovelLengthPanel model", () => {
  afterEach(() => cleanup());

  it("hydrates and saves the current revision model", async () => {
    const originalFetch = globalThis.fetch;
    const updates: StoryNovelUpdateLengthSpecPayload[] = [];
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          success: true,
          data: {
            items: [
              {
                profile_id: "standard_serial",
                name: "标准连载",
                min_chars: 3000,
                target_chars: 4000,
                max_chars: 5000,
              },
            ],
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    try {
      const utils = render(
        <StoryNovelLengthPanel
          story={story}
          revision={revision}
          locked={false}
          busy={false}
          onCreate={async () => true}
          onUpdate={async (_revisionId, payload) => {
            updates.push(payload);
            return true;
          }}
        />,
        { container: dom.window.document.body },
      );
      const modelInput = await waitFor(() =>
        utils.getByDisplayValue("deepseek:deepseek-v4-flash"),
      );
      assert.equal(
        (modelInput as HTMLInputElement).value,
        "deepseek:deepseek-v4-flash",
      );
      fireEvent.click(utils.getByRole("button", { name: "保存到当前版本" }));
      await waitFor(() => assert.equal(updates.length, 1));
      assert.equal(updates[0].model, "deepseek:deepseek-v4-flash");
      assert.equal(updates[0].expected_plan_version, 4);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

const story = {
  business_id: "story-1",
  story_seed: {
    schema: "story_seed_v2",
    structured_outline: {
      status: "confirmed",
      version: 7,
      thread_schedule_version: 1,
      thread_payoffs: [],
      chapters: [
        {
          position: 1,
          title: "第一章",
          goal: "开始",
          key_events: ["事件"],
          character_focus: ["主角"],
          open_threads: [],
          end_state: "继续",
        },
      ],
    },
  },
} as Story;

const revision = {
  business_id: "revision-1",
  lifecycle_status: "draft",
  model: "deepseek:deepseek-v4-flash",
  generation_plan: {
    version: 4,
    status: "ready",
    length_profile: {
      profile_id: "standard_serial",
      default_min_chars: 3000,
      default_target_chars: 4000,
      default_max_chars: 5000,
    },
    chapter_length_overrides: {},
    chapters: [],
  },
} as StoryNovelRevision;
