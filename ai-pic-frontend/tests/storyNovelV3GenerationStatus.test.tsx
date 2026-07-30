import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import {
  StoryNovelGenerationStatus,
  storyNovelChapterProgress,
} from "../src/components/features/story-detail/StoryNovelGenerationStatus";
import type {
  StoryNovelGenerationStage,
  StoryNovelRevision,
} from "../src/utils/api/types";

describe("StoryNovelGenerationStatus v3", () => {
  it("renders every v3 stage plus chapter calls, tokens, latency, and failed blocks", () => {
    const stages: StoryNovelGenerationStage[] = [
      "chapter_planning",
      "prose",
      "audit",
      "local_repair",
      "memory_ready",
      "ready",
    ];
    const chapters = Object.fromEntries(
      stages.map((stage, index) => [
        String(index + 1),
        {
          status: stage === "ready" ? "ready" : "body_ready",
          stage,
          char_count: 3000 + index,
          stage_metrics: {
            [stage]: {
              calls: 1,
              input_tokens: 100,
              output_tokens: 200,
              latency_ms: 500,
            },
          },
          failed_block_ids: stage === "local_repair" ? ["B03"] : [],
        },
      ]),
    );
    const revision = {
      id: 31,
      business_id: "revision-v3",
      style: "prose",
      target_words: 0,
      revision_number: 1,
      lifecycle_status: "draft",
      continuity_status: "review_required",
      adaptation_plan_status: "empty",
      generation_plan: {
        schema: "story_novel_generation_plan.v3",
        status: "ready",
        chapter_count: stages.length,
        planned_target_chars: 24000,
        chapters: stages.map((_, index) => ({
          position: index + 1,
          title: `第${index + 1}章`,
          goal: "推进当前章",
          target_chars: 4000,
        })),
      },
      continuity_ledger: {
        schema: "story_novel_continuity.v4",
        chapters,
      },
      chapters: [],
      created_at: "2026-07-27T00:00:00Z",
    } as StoryNovelRevision;

    assert.deepEqual(
      storyNovelChapterProgress(revision).map(({ stage }) => stage),
      stages,
    );
    const html = renderToStaticMarkup(
      <StoryNovelGenerationStatus revision={revision} />,
    );
    for (const stage of stages) assert.match(html, new RegExp(stage));
    assert.match(html, /模型调用 6/);
    assert.match(html, /Tokens 1,800/);
    assert.match(html, /延迟 3\.0s/);
    assert.match(html, /失败 blocks B03/);
  });
});
