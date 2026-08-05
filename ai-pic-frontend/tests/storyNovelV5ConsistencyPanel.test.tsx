import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import { StoryNovelV5ConsistencyPanel } from "../src/components/features/story-detail/StoryNovelV5ConsistencyPanel";
import type { StoryNovelRevision } from "../src/utils/api/types";

describe("StoryNovelV5ConsistencyPanel", () => {
  it("renders frozen generic counts, hashes, and chapter quality without an editor", () => {
    const revision = {
      id: 51,
      business_id: "revision-v5",
      style: "prose",
      target_words: 3000,
      revision_number: 1,
      lifecycle_status: "draft",
      continuity_status: "review_required",
      adaptation_plan_status: "empty",
      generation_plan: {
        schema: "story_novel_generation_plan.v5",
        status: "ready",
        schema_compile_status: "frozen",
        consistency_schema_hash: "schema1234567890",
        initial_snapshot_hash: "before1234567890",
        causal_graph_hash: "causal1234567890",
        canon_view: {
          counts: {
            entity_types: 3,
            predicates: 5,
            event_types: 4,
            constraints: 2,
            perspectives: 1,
          },
          entities: [],
          facts: [],
        },
        chapters: [
          { position: 1, title: "抵达", goal: "推进", target_chars: 3000 },
        ],
      },
      continuity_ledger: {
        schema: "story_novel_continuity.v6",
        chapters: {
          "1": {
            status: "ready",
            snapshot_before_hash: "before1234567890",
            snapshot_after_hash: "after1234567890",
            consistency_report: { status: "passed" },
            readability_report: { status: "passed", score: 8 },
            repair_records: [{ kind: "sentence_span", sentence_ids: ["S0004"] }],
          },
        },
      },
      chapters: [],
      created_at: "2026-08-03T00:00:00Z",
    } as StoryNovelRevision;

    const html = renderToStaticMarkup(
      <StoryNovelV5ConsistencyPanel revision={revision} />,
    );

    assert.match(html, /一致性模型/);
    assert.match(html, /Schema frozen/);
    assert.match(html, /实体类型/);
    assert.match(html, />3</);
    assert.match(html, /一致性 passed/);
    assert.match(html, /可读性 passed 8\/10/);
    assert.match(html, /返修 1/);
    assert.doesNotMatch(html, /textarea|保存 Schema/);
  });
});
