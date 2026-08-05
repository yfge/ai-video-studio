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

  it("renders the v4 current arc, frozen snapshots, and dynamic proposals", () => {
    const revision = {
      id: 41,
      business_id: "revision-v4",
      style: "prose",
      target_words: 0,
      revision_number: 1,
      lifecycle_status: "draft",
      continuity_status: "review_required",
      adaptation_plan_status: "empty",
      generation_plan: {
        schema: "story_novel_generation_plan.v4",
        status: "ready",
        chapter_count: 1,
        frozen_through_position: 16,
        current_arc_plan: {
          arc_id: "arc-1",
          title: "开篇卷",
          start_position: 1,
          end_position: 16,
          instantiated_character_slots: [{ slot_id: "slot-rival" }],
          instantiated_scope_slots: [{ slot_id: "slot-market" }],
        },
        scope_graph: { nodes: [{ scope_id: "scope-home" }] },
        chapters: [
          { position: 1, title: "初见", goal: "推进", target_chars: 2500 },
        ],
      },
      continuity_ledger: {
        schema: "story_novel_continuity.v5",
        chapters: {
          "1": {
            status: "ready",
            planner_snapshot_hash: "planner1234567890",
            arc_planner_snapshot_hash: "arc1234567890",
            model_call_snapshots: {
              "chapter_planning.1": {
                snapshot_hash: "call",
                input_hash: "input",
              },
            },
            chapter_intent: {
              entity_proposals: [
                { kind: "character", name: "迟岚", transient: false },
              ],
            },
          },
        },
      },
      chapters: [],
      created_at: "2026-07-31T00:00:00Z",
    } as StoryNovelRevision;
    const html = renderToStaticMarkup(
      <StoryNovelGenerationStatus revision={revision} />,
    );
    assert.match(html, /当前卷 开篇卷/);
    assert.match(html, /第 1–16 章/);
    assert.match(html, /调用快照 1/);
    assert.match(html, /动态提案 1（已落账 1）/);
    assert.match(html, /本卷角色槽 1 · 范围槽 1 · 初始范围 1/);
    assert.match(html, /迟岚\(character，已进入 Revision 世界\)/);
  });
});
