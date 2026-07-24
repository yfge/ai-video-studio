import { dom } from "./storyNovelAcceptanceTestDom";
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import React from "react";

import { StorySeedSection } from "../src/components/features/stories/StorySeedSection";
import type { Story } from "../src/utils/api/types";

describe("StorySeed planning inputs", () => {
  afterEach(() => cleanup());

  it("submits selected chapter count and planning model", async () => {
    const originalFetch = globalThis.fetch;
    const posts: Array<{ url: string; body: unknown }> = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/ai/models/available")) return modelResponse();
      if (url.includes("/story-seed/structure-async")) {
        posts.push({
          url,
          body: JSON.parse(String(init?.body || "{}")),
        });
        return jsonResponse({
          success: true,
          data: { task_id: 901, status: "completed" },
        });
      }
      throw new Error(`unexpected fetch ${url}`);
    };
    try {
      const utils = render(<StorySeedSection story={story} />, {
        container: dom.window.document.body,
      });

      assert.equal(
        (utils.getByLabelText("结构化章节数") as HTMLInputElement).value,
        "48",
      );
      fireEvent.input(utils.getByLabelText("结构化章节数"), {
        target: { value: "36" },
      });
      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("结构化规划模型") as HTMLSelectElement)
            .disabled,
          false,
        ),
      );
      fireEvent.change(utils.getByLabelText("结构化规划模型"), {
        target: { value: "codex:gpt-5.6" },
      });
      fireEvent.click(
        utils.getByRole("button", { name: "AI 生成结构化章节计划" }),
      );

      await waitFor(() => assert.equal(posts.length, 1));
      assert.deepEqual(posts[0].body, {
        chapter_count: 36,
        model: "codex:gpt-5.6",
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("restores chapter count and model from a generated outline", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => modelResponse();
    const latest = {
      ...story,
      story_seed: {
        ...story.story_seed,
        schema: "story_seed_v2" as const,
        outline_text: "第1章至第24章",
        structured_outline: {
          status: "draft" as const,
          version: 2,
          requested_chapter_count: 24,
          planning_model: "deepseek:deepseek-v4-pro",
          thread_schedule_version: 0,
          thread_payoffs: [],
          chapters: [chapter],
        },
      },
    } as Story;
    try {
      const utils = render(<StorySeedSection story={latest} />, {
        container: dom.window.document.body,
      });

      assert.equal(
        (utils.getByLabelText("结构化章节数") as HTMLInputElement).value,
        "24",
      );
      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("结构化规划模型") as HTMLSelectElement).value,
          "deepseek:deepseek-v4-pro",
        ),
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

function jsonResponse(payload: unknown) {
  return new Response(JSON.stringify(payload), {
    headers: { "content-type": "application/json" },
  });
}

function modelResponse() {
  return jsonResponse({
    success: true,
    data: {
      models: [
        {
          model_id: "codex:gpt-5.6",
          id: "gpt-5.6",
          name: "GPT-5.6",
          provider: "codex",
          type: "text_generation",
          capabilities: ["text_generation"],
        },
        {
          model_id: "deepseek:deepseek-v4-pro",
          id: "deepseek-v4-pro",
          name: "DeepSeek V4 Pro",
          provider: "deepseek",
          type: "text_generation",
          capabilities: ["text_generation"],
        },
      ],
    },
  });
}

const chapter = {
  position: 1,
  title: "第一章",
  goal: "推进",
  key_events: ["事件"],
  character_focus: [],
  open_threads: [],
  end_state: "继续",
};

const story = {
  id: 1,
  business_id: "story-business-id",
  title: "结构化测试",
  ai_model: "",
  story_seed_status: "draft",
  story_seed_version: 1,
  story_seed: {
    schema: "story_seed_v1",
    title: "结构化测试",
    premise: "测试规划",
    outline: "第1章至第48章",
    protagonists: [
      { virtual_ip_business_id: "vip-1", initial_state: "等待出发" },
    ],
    world_constraints: [],
    central_conflict: "完成测试",
    content_constraints: [],
  },
} as Story;
