import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { parseCharacterArcs } from "../src/components/features/story-detail/StoryNovelAdaptationEpisodeCard";
import { applyCanonSuggestion } from "../src/components/features/story-detail/StoryNovelCanonPanel";
import { StoryNovelWorkflowPanel } from "../src/components/features/story-detail/StoryNovelWorkflowPanel";
import { updateStoryNovelCanon } from "../src/utils/api/endpoints/story-novel.endpoints";
import type {
  Story,
  StoryNovelCanon,
  StoryNovelRevision,
} from "../src/utils/api/types";

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
      assert.ok(utils.getByText("3. 小说版本与正文生成"));
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

  it("starts prose generation without legacy word or chapter targets", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({ url, init });
      if (init?.method === "POST" && url.endsWith("/generate-async")) {
        return response({
          task_id: 88,
          status: "pending",
          revision_business_id: plannedRevision.business_id,
        });
      }
      if (url.includes("/api/v1/tasks/88")) {
        return response({ id: 88, status: "pending" });
      }
      return response({
        items: [plannedRevision],
        canonical_business_id: null,
      });
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
          utils.getByRole("button", {
            name: "开始生成正文",
          }),
        ),
      );
      assert.equal(utils.queryByLabelText("目标字数"), null);
      assert.equal(utils.queryByLabelText("章节数"), null);
      fireEvent.click(utils.getByRole("button", { name: "开始生成正文" }));
      await waitFor(() =>
        assert.ok(
          requests.some(
            (item) =>
              item.init?.method === "POST" &&
              item.url.endsWith("/generate-async"),
          ),
        ),
      );
      const request = requests.find((item) =>
        item.url.endsWith("/generate-async"),
      );
      assert.equal(request?.init?.body, undefined);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("resumes an empty Canon checkpoint without discarding it", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    const failedPlanningRevision: StoryNovelRevision = {
      ...plannedRevision,
      generation_plan: {
        ...plannedRevision.generation_plan!,
        status: "planning",
        phase: "chapters",
      },
    };
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({ url, init });
      if (init?.method === "POST" && url.endsWith("/generate-async")) {
        return response({
          task_id: 91,
          status: "pending",
          revision_business_id: failedPlanningRevision.business_id,
        });
      }
      if (url.includes("/api/v1/tasks/91")) {
        return response({ id: 91, status: "pending" });
      }
      return response({
        items: [failedPlanningRevision],
        canonical_business_id: null,
      });
    };
    try {
      const utils = render(
        <StoryNovelWorkflowPanel
          story={story}
          onEpisodesApplied={async () => undefined}
        />,
        { container: dom.window.document.body },
      );
      await waitFor(() => {
        const button = utils.getByRole("button", {
          name: "继续规划并生成正文",
        });
        assert.equal(button.hasAttribute("disabled"), false);
      });
      (
        utils.getByRole("button", {
          name: "继续规划并生成正文",
        }) as HTMLButtonElement
      ).click();
      await waitFor(() =>
        assert.ok(
          requests.some(
            ({ url, init }) =>
              init?.method === "POST" && url.endsWith("/generate-async"),
          ),
        ),
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("shows Canon repair controls and state quality evidence", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input, init) => {
      void input;
      void init;
      return response({ items: [v2Revision], canonical_business_id: null });
    };
    try {
      const utils = render(
        <StoryNovelWorkflowPanel
          story={story}
          onEpisodesApplied={async () => undefined}
        />,
        { container: dom.window.document.body },
      );
      await waitFor(() => assert.ok(utils.getByLabelText("Canon 结构化草稿")));
      assert.ok(utils.getByText("状态门禁 1/1", { exact: false }));
      assert.ok(utils.getByRole("button", { name: "填入 Canon 草稿" }));
      assert.ok(utils.getByRole("button", { name: "人工确认并保存 Canon" }));
      assert.ok(utils.getByText("结构"));
      assert.ok(utils.getByText("8.0/10"));
      fireEvent.click(utils.getByRole("button", { name: "填入 Canon 草稿" }));
      await waitFor(() => assert.ok(utils.getByText("Canon 草稿有未保存修改")));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("applies a Canon suggestion only to its persisted target", () => {
    const changed = applyCanonSuggestion(canon, {
      id: "repair-1",
      canon_target: {
        section: "initial_state",
        item_id: "char-a",
        field: "status",
      },
      suggested_value: "怀疑规则",
    });
    assert.equal(changed.initial_state["char-a"].status, "怀疑规则");
    assert.equal(canon.initial_state["char-a"].status, "守规");
  });

  it("sends the optimistic Canon update contract", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; body: unknown }> = [];
    globalThis.fetch = async (input, init) => {
      requests.push({
        url: String(input),
        body: JSON.parse(String(init?.body)),
      });
      return response({
        revision: v2Revision,
        canon_hash: "b".repeat(64),
        stale_from_position: 1,
      });
    };
    try {
      await updateStoryNovelCanon("revision-business-id", {
        expected_plan_version: 2,
        expected_canon_hash: "a".repeat(64),
        canon,
      });
      assert.ok(requests[0].url.endsWith("/canon"));
      assert.deepEqual(requests[0].body, {
        expected_plan_version: 2,
        expected_canon_hash: "a".repeat(64),
        canon,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("shows the failed checkpoint and resumes from the earliest stale chapter", async () => {
    const originalFetch = globalThis.fetch;
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      requests.push({ url, init });
      if (init?.method === "POST" && url.endsWith("/resume-async")) {
        return response({
          task_id: 89,
          status: "pending",
          revision_business_id: failedRevision.business_id,
        });
      }
      if (url.includes("/api/v1/tasks/89")) {
        return response({ id: 89, status: "pending" });
      }
      return response({
        items: [failedRevision],
        canonical_business_id: null,
      });
    };
    try {
      const utils = render(
        <StoryNovelWorkflowPanel
          story={story}
          onEpisodesApplied={async () => undefined}
        />,
        { container: dom.window.document.body },
      );
      const resume = await waitFor(() =>
        utils.getByRole("button", { name: "从第 1 章续写至结尾" }),
      );
      assert.ok(utils.getByText("1 章门禁失败"));
      assert.ok(utils.getByText("门禁失败：主角提前知道密钥"));
      assert.ok(utils.getByText("当前从第 1 章起待重生成。"));
      fireEvent.click(resume);
      await waitFor(() =>
        assert.ok(
          requests.some(
            ({ url, init }) =>
              init?.method === "POST" && url.endsWith("/resume-async"),
          ),
        ),
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
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

const canon: StoryNovelCanon = {
  timeline: [],
  entities: [
    { id: "char-a", kind: "character", name: "主角" },
    { id: "loc-gate", kind: "location", name: "城门" },
  ],
  world_rules: [],
  milestones: [],
  character_arcs: [],
  initial_state: {
    "char-a": { location: "loc-gate", status: "守规", knowledge: [] },
  },
  canon_hash: "a".repeat(64),
};

const v2Revision: StoryNovelRevision = {
  ...revision,
  generation_plan: {
    schema: "story_novel_generation_plan.v2",
    version: 2,
    status: "ready",
    phase: "ready",
    canon,
    canon_hash: "a".repeat(64),
    chapter_count: 1,
    target_chars: 3000,
    chapters: [
      {
        position: 1,
        title: "第一章",
        goal: "发现裂缝",
        target_chars: 3000,
        required_event_ids: ["event-1"],
        canon_refs: ["char-a"],
      },
    ],
  },
  continuity_ledger: {
    schema: "story_novel_continuity.v3",
    state_status: "ready",
    chapters: {
      "1": {
        status: "ready",
        extraction_status: "ready",
        state_validation: { status: "passed", violations: [] },
      },
    },
  },
  continuity_report: {
    schema: "story_novel_continuity_review.v3",
    summary: "需要确认一个 Canon 值",
    hard_metrics: { canon_violation_count: 0, chapter_repair_rate: 0 },
    quality_scores: {
      structure: { score: 8, rationale: "结构稳定" },
    },
    repair_groups: [
      {
        id: "repair-1",
        title: "主角立场",
        canon_target: {
          section: "initial_state",
          item_id: "char-a",
          field: "status",
        },
        suggested_value: "怀疑规则",
      },
    ],
    issues: [],
  },
};

const plannedRevision: StoryNovelRevision = {
  ...v2Revision,
  chapters: [],
  total_words: 0,
  generation_plan: {
    ...v2Revision.generation_plan!,
    status: "ready",
  },
  continuity_ledger: {
    schema: "story_novel_continuity.v3",
    state_status: "empty",
    chapters: {},
  },
  continuity_report: null,
};

const failedRevision: StoryNovelRevision = {
  ...v2Revision,
  continuity_ledger: {
    ...v2Revision.continuity_ledger,
    state_status: "failed",
    stale_from_position: 1,
    chapters: {
      "1": {
        status: "gate_failed",
        extraction_status: "blocked",
        state_validation: {
          status: "failed",
          violations: [
            { code: "illegal_knowledge", message: "主角提前知道密钥" },
          ],
        },
      },
    },
  },
};

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    headers: { "content-type": "application/json" },
  });
}
