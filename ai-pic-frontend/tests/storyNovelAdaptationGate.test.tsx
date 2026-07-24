import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { StoryNovelAdaptationPanel } from "../src/components/features/story-detail/StoryNovelAdaptationPanel";
import type {
  AdaptationPlanStatus,
  StoryNovelRevision,
} from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

describe("StoryNovelAdaptationPanel downstream gate", () => {
  afterEach(() => cleanup());

  it("shows the authoritative chain and locks unapproved novels", () => {
    const utils = renderPanel(revision("empty", false));
    assert.ok(utils.getByText("故事大纲 → 小说审批 → 改编计划 → 剧集 → 剧本"));
    assert.ok(utils.getByText("小说修订版尚未审批", { exact: false }));
    assert.equal(
      utils
        .getByRole("button", { name: "生成分集改编计划" })
        .hasAttribute("disabled"),
      true,
    );
    assert.equal(
      utils.getByRole("button", { name: "创建剧集" }).hasAttribute("disabled"),
      true,
    );
  });

  it("regenerates a stale plan while keeping Episode locked", () => {
    let generated = 0;
    const utils = renderPanel(revision("stale"), {
      onGenerate: () => {
        generated += 1;
      },
    });
    assert.ok(utils.getByText("改编计划已过期", { exact: false }));
    fireEvent.click(
      utils.getByRole("button", { name: "重新生成分集改编计划" }),
    );
    assert.equal(generated, 1);
    assert.equal(
      utils.getByRole("button", { name: "创建剧集" }).hasAttribute("disabled"),
      true,
    );
  });

  it("enables Episode only after plan approval", () => {
    let applied = 0;
    const utils = renderPanel(revision("approved"), {
      onApply: () => {
        applied += 1;
      },
    });
    assert.ok(utils.getByText("小说与改编计划均已审批", { exact: false }));
    fireEvent.click(utils.getByRole("button", { name: "创建剧集" }));
    assert.equal(applied, 1);
  });

  it("locks legacy approved plans that lack frozen hash evidence", () => {
    const value = revision("applied");
    value.adaptation_plan = {
      version: 1,
      novel_content_hash: "revision-hash",
      episodes: value.adaptation_plan!.episodes,
    };
    const utils = renderPanel(value);
    assert.ok(utils.getByText("改编计划缺少", { exact: false }));
    assert.equal(
      utils
        .getByRole("button", { name: "返回既有剧集" })
        .hasAttribute("disabled"),
      true,
    );
  });
});

function renderPanel(
  value: StoryNovelRevision,
  overrides: Partial<
    React.ComponentProps<typeof StoryNovelAdaptationPanel>
  > = {},
) {
  return render(
    <StoryNovelAdaptationPanel
      revision={value}
      busy={false}
      onGenerate={() => undefined}
      onSave={() => undefined}
      onApprove={() => undefined}
      onApply={() => undefined}
      {...overrides}
    />,
    { container: dom.window.document.body },
  );
}

function revision(
  status: AdaptationPlanStatus,
  approved = true,
): StoryNovelRevision {
  const hasPlan = status !== "empty";
  const contentHash = "revision-hash";
  return {
    id: 1,
    business_id: "revision-1",
    style: "prose",
    target_words: 9000,
    revision_number: 1,
    lifecycle_status: approved ? "approved" : "draft",
    continuity_status: "passed",
    adaptation_plan_status: status,
    adaptation_plan: hasPlan
      ? ({
          version: 1,
          novel_content_hash: contentHash,
          novel_revision_business_id: "revision-1",
          generation_plan_version: 1,
          generation_plan_hash: "generation-plan-hash",
          plan_hash: "adaptation-plan-hash",
          chapter_sources: [
            {
              business_id: "chapter-1",
              body_hash: "chapter-body-hash",
              source_hash: "chapter-source-hash",
            },
          ],
          episodes: [
            {
              episode_number: 1,
              title: "第一集",
              source_chapter_business_ids: ["chapter-1"],
              adaptation_goal: "建立冲突",
              summary: "概要",
              plot_points: [],
              conflicts: [],
              character_arcs: {},
            },
          ],
        } as StoryNovelRevision["adaptation_plan"])
      : null,
    content_hash: contentHash,
    generation_plan: {
      version: 1,
      status: "ready",
      plan_hash: "generation-plan-hash",
      chapters: [],
    },
    created_at: "2026-07-24T00:00:00Z",
    chapters: [
      {
        business_id: "chapter-1",
        position: 1,
        title: "第一章",
        content_text: "正文",
        content_hash: "chapter-body-hash",
        review_status: "ready",
        updated_at: "2026-07-24T00:00:00Z",
      },
    ],
  };
}
