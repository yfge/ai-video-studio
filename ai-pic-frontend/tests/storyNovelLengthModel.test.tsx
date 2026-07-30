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

  it("hydrates and saves the frozen three-stage model policy", async () => {
    const originalFetch = globalThis.fetch;
    const updates: StoryNovelUpdateLengthSpecPayload[] = [];
    globalThis.fetch = async (input) =>
      response(
        String(input).includes("/ai/models/available")
          ? {
              models: [
                {
                  model_id: "deepseek:deepseek-v4-flash",
                  id: "deepseek-v4-flash",
                  name: "DeepSeek V4 Flash",
                  provider: "deepseek",
                  type: "text_generation",
                  capabilities: ["text_generation"],
                },
              ],
            }
          : {
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
      const modelInput = await waitFor(() => {
        const field = utils.getByLabelText("正文生成模型（可选）");
        assert.equal(
          (field as HTMLSelectElement).value,
          "deepseek:deepseek-v4-flash",
        );
        return field;
      });
      assert.equal(
        (modelInput as HTMLSelectElement).value,
        "deepseek:deepseek-v4-flash",
      );
      assert.equal(
        (utils.getByLabelText("章前规划模型") as HTMLSelectElement).value,
        "deepseek:deepseek-v4-flash",
      );
      assert.equal(
        (utils.getByLabelText("状态审计模型（可选）") as HTMLSelectElement)
          .value,
        "",
      );
      fireEvent.change(utils.getByLabelText("状态审计模型（可选）"), {
        target: { value: "deepseek:deepseek-v4-flash" },
      });
      fireEvent.click(utils.getByRole("button", { name: "保存到当前版本" }));
      await waitFor(() => assert.equal(updates.length, 1));
      assert.equal(updates[0].model, "deepseek:deepseek-v4-flash");
      assert.deepEqual(updates[0].model_policy, {
        planning_model: "deepseek:deepseek-v4-flash",
        prose_model: "deepseek:deepseek-v4-flash",
        audit_model: "deepseek:deepseek-v4-flash",
      });
      assert.equal(updates[0].expected_plan_version, 4);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    headers: { "content-type": "application/json" },
  });
}

const story = {
  business_id: "story-1",
  story_seed: {
    schema: "story_seed_v2",
    structured_outline: {
      status: "confirmed",
      version: 7,
      planning_model: "deepseek:deepseek-v4-flash",
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
} as unknown as Story;

const revision = {
  business_id: "revision-1",
  lifecycle_status: "draft",
  model: "deepseek:deepseek-v4-flash",
  generation_plan: {
    version: 4,
    status: "ready",
    model_policy: {
      planning_model: "deepseek:deepseek-v4-flash",
      prose_model: "deepseek:deepseek-v4-flash",
      audit_model: null,
    },
    length_profile: {
      profile_id: "standard_serial",
      default_min_chars: 3000,
      default_target_chars: 4000,
      default_max_chars: 5000,
    },
    chapter_length_overrides: {},
    chapters: [],
  },
} as unknown as StoryNovelRevision;
