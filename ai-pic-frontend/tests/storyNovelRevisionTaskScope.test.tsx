import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryNovelWorkflowPanel } from "../src/components/features/story-detail/StoryNovelWorkflowPanel";
import type { Story, StoryNovelRevision } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).localStorage = dom.window.localStorage;

describe("StoryNovelWorkflow revision task scope", () => {
  afterEach(() => cleanup());

  it("drops a failed task when selecting another revision and starts that revision", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; method?: string }> = [];
    const revisions = [failedV2, planningV3];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({ url, method: init?.method });
      if (url.includes("/api/v1/tasks/6560")) {
        return response({
          id: 6560,
          status: "failed",
          error_message: "v2 任务失败",
        });
      }
      if (init?.method === "POST" && url.endsWith("/rev-v3/generate-async")) {
        return response({
          task_id: 6556,
          status: "pending",
          revision_business_id: "rev-v3",
        });
      }
      if (url.includes("/api/v1/tasks/6556")) {
        return response({ id: 6556, status: "pending" });
      }
      return response({ items: revisions, canonical_business_id: null });
    };
    try {
      const utils = render(
        <StoryNovelWorkflowPanel
          story={story}
          onEpisodesApplied={async () => undefined}
        />,
        { container: dom.window.document.body },
      );
      await waitFor(() => assert.ok(utils.getByText("任务 #6560 · failed")));
      assert.ok(utils.getByRole("alert").textContent?.includes("v2 任务失败"));

      fireEvent.change(utils.getByLabelText("当前小说版本"), {
        target: { value: "rev-v3" },
      });
      assert.equal(utils.queryByText("任务 #6560 · failed"), null);
      assert.equal(utils.queryByRole("alert"), null);
      await waitFor(() => {
        assert.equal(
          utils
            .getByRole("button", { name: "继续规划并生成正文" })
            .hasAttribute("disabled"),
          false,
        );
      });

      fireEvent.click(
        utils.getByRole("button", { name: "继续规划并生成正文" }),
      );
      await waitFor(() =>
        assert.ok(
          requests.some(
            ({ url, method }) =>
              method === "POST" && url.endsWith("/rev-v3/generate-async"),
          ),
        ),
      );
      await waitFor(() => assert.ok(utils.getByText("任务 #6556 · pending")));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  for (const terminalStatus of ["failed", "cancelled"]) {
    it(`allows retry after a ${terminalStatus} task`, async () => {
      const originalFetch = globalThis.fetch;
      const requests: Array<{ url: string; method?: string }> = [];
      let current = {
        ...failedPlanningV3,
        task_id: terminalStatus === "failed" ? 6557 : 6558,
      };
      globalThis.fetch = async (input, init) => {
        const url = String(input);
        requests.push({ url, method: init?.method });
        if (url.includes(`/api/v1/tasks/${current.task_id}`)) {
          return response({
            id: current.task_id,
            status: terminalStatus,
            error_message:
              terminalStatus === "failed" ? "规划失败，可重试" : null,
          });
        }
        if (init?.method === "POST" && url.endsWith("/rev-v3/generate-async")) {
          current = { ...current, task_id: 6561 };
          return response({
            task_id: 6561,
            status: "pending",
            revision_business_id: "rev-v3",
          });
        }
        return response({ items: [current], canonical_business_id: null });
      };
      try {
        const utils = render(
          <StoryNovelWorkflowPanel
            story={story}
            onEpisodesApplied={async () => undefined}
          />,
          { container: dom.window.document.body },
        );
        await waitFor(() =>
          assert.ok(
            utils.getByText(
              `任务 #${
                terminalStatus === "failed" ? 6557 : 6558
              } · ${terminalStatus}`,
            ),
          ),
        );
        const retry = utils.getByRole("button", {
          name: "重试规划并生成正文",
        });
        assert.equal(retry.hasAttribute("disabled"), false);
        fireEvent.click(retry);
        await waitFor(() =>
          assert.ok(
            requests.some(
              ({ url, method }) =>
                method === "POST" && url.endsWith("/rev-v3/generate-async"),
            ),
          ),
        );
      } finally {
        globalThis.fetch = originalFetch;
      }
    });
  }
});

const story: Story = {
  id: 1,
  business_id: "story-business-id",
  title: "链路故事",
  genre: "drama",
  workflow_mode: "novel_adaptation_v1",
  story_seed_status: "confirmed",
  status: "draft",
  is_public: false,
  created_at: "2026-07-23T00:00:00Z",
  updated_at: "2026-07-23T00:00:00Z",
};

const baseRevision: StoryNovelRevision = {
  id: 1,
  business_id: "rev-v3",
  story_business_id: story.business_id,
  style: "prose",
  target_words: 0,
  chapter_count: 48,
  total_words: 0,
  revision_number: 3,
  lifecycle_status: "draft",
  continuity_status: "unchecked",
  adaptation_plan_status: "empty",
  generation_plan: {
    schema: "story_novel_generation_plan.v2",
    version: 4,
    status: "planning",
    phase: "chapters",
    chapter_count: 48,
    chapters: [],
  },
  chapters: [],
  created_at: "2026-07-23T00:00:00Z",
  updated_at: "2026-07-23T00:00:00Z",
};

const failedV2: StoryNovelRevision = {
  ...baseRevision,
  id: 2,
  business_id: "rev-v2",
  task_id: 6560,
  revision_number: 2,
  generation_plan: {
    ...baseRevision.generation_plan!,
    status: "failed",
  },
};

const planningV3: StoryNovelRevision = { ...baseRevision };
const failedPlanningV3: StoryNovelRevision = {
  ...baseRevision,
  generation_plan: {
    ...baseRevision.generation_plan!,
    status: "failed",
  },
};

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    headers: { "content-type": "application/json" },
  });
}
