import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import {
  StoryNovelGenerationStatus,
  storyNovelResumeLabel,
} from "../src/components/features/story-detail/StoryNovelGenerationStatus";
import type {
  StoryNovelContinuityLedger,
  StoryNovelRevision,
} from "../src/utils/api/types";

describe("story novel state-pending recovery", () => {
  it("prioritizes extraction-only recovery when both checkpoint signals agree", () => {
    assert.equal(
      storyNovelResumeLabel(pendingLedger),
      "恢复状态提取（保留已保存正文）",
    );
    assert.equal(
      storyNovelResumeLabel({
        ...pendingLedger,
        recovery_from_position: undefined,
      }),
      "从第 1 章续写至结尾",
    );
    assert.equal(
      storyNovelResumeLabel({
        ...pendingLedger,
        chapters: { "1": { status: "gate_failed" } },
      }),
      "从第 1 章续写至结尾",
    );
  });

  it("counts the saved body and renders pending extraction as amber, not failed", () => {
    const html = renderToStaticMarkup(
      <StoryNovelGenerationStatus revision={pendingRevision} />,
    );

    assert.match(html, /正文 1\/1/);
    assert.match(html, /1 章正文已保存，仅状态提取待恢复/);
    assert.match(html, /text-amber-700/);
    assert.doesNotMatch(html, /章门禁失败|门禁失败：/);
  });
});

const pendingLedger: StoryNovelContinuityLedger = {
  state_status: "failed",
  stale_from_position: 1,
  recovery_from_position: 1,
  chapters: {
    "1": {
      status: "state_pending",
      extraction_status: "blocked",
      char_count: 880,
      state_validation: {
        status: "failed",
        violations: [{ code: "source_evidence", message: "状态提取证据不足" }],
      },
    },
  },
};

const pendingRevision: StoryNovelRevision = {
  id: 1,
  business_id: "revision-1",
  style: "prose",
  target_words: 1000,
  revision_number: 1,
  lifecycle_status: "draft",
  continuity_status: "review_required",
  adaptation_plan_status: "empty",
  generation_plan: {
    status: "ready",
    chapter_count: 1,
    target_chars: 1000,
    chapters: [],
  },
  continuity_ledger: pendingLedger,
  created_at: "2026-07-24T00:00:00Z",
  chapters: [],
};
