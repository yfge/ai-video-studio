import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import {
  hasProductionCanvasDomainContext,
  isProductionCanvasAuthoritativeContext,
  productionCanvasTaskResultContext,
  resolveProductionCanvasTaskResultContext,
} from "../src/components/features/canvas/productionCanvasTaskResultContext";
import type { Task } from "../src/utils/api/types";

const originalFetch = globalThis.fetch;

function task(patch: Partial<Task>): Task {
  return {
    id: 77,
    business_id: "task-77",
    title: "剧本生成",
    status: "completed",
    created_at: "2026-07-15T00:00:00Z",
    user_id: 1,
    ...patch,
  };
}

afterEach(() => {
  globalThis.fetch = originalFetch;
});

describe("production canvas task result context", () => {
  it("prefers typed result context over agent-run and result-path fallbacks", () => {
    const context = productionCanvasTaskResultContext(
      task({
        result_file_path: "timeline:41:v2",
        parameters: {
          agent_run: {
            result_ref: { script_id: 31, timeline_id: 51, timeline_version: 3 },
          },
        },
        result_context: {
          story_id: 11,
          episode_id: 21,
          script_id: 31,
          timeline_id: 61,
          timeline_version: 4,
          clip_id: "clip-7",
        },
      }),
    );

    assert.deepEqual(context, {
      story_id: 11,
      episode_id: 21,
      script_id: 31,
      timeline_id: 61,
      timeline_version: 4,
      clip_id: "clip-7",
    });
  });

  it("uses the single clip emitted by an agent-run result", () => {
    const context = productionCanvasTaskResultContext(
      task({
        parameters: {
          agent_run: {
            result_ref: { timeline_id: 61, clip_ids: ["clip-only"] },
          },
        },
      }),
    );

    assert.equal(context.timeline_id, 61);
    assert.equal(context.clip_id, "clip-only");
  });

  it("does not retain legacy lineage omitted by typed result context", () => {
    const context = productionCanvasTaskResultContext(
      task({
        result_file_path: "timeline:41:v2",
        parameters: {
          agent_run: {
            result_ref: {
              timeline_id: 51,
              timeline_version: 3,
              clip_id: "legacy-clip",
            },
          },
        },
        result_context: { timeline_id: 61, timeline_version: 4 },
      }),
    );

    assert.deepEqual(context, {
      timeline_id: 61,
      timeline_version: 4,
    });
  });

  it("preserves authoritative clears while resolving typed task context", async () => {
    const context = await resolveProductionCanvasTaskResultContext(
      task({
        parameters: { kind: "production_canvas_run" },
        result_context: {
          virtual_ip_id: null,
          environment_id: null,
          story_id: 61,
          episode_id: null,
          script_id: null,
          timeline_id: null,
          timeline_version: null,
          clip_id: null,
          task_id: null,
        },
      }),
    );

    assert.deepEqual(context, {
      virtual_ip_id: null,
      environment_id: null,
      story_id: 61,
      episode_id: null,
      script_id: null,
      timeline_id: null,
      timeline_version: null,
      clip_id: null,
      task_id: null,
    });
    assert.equal(isProductionCanvasAuthoritativeContext(context), true);
    assert.equal(hasProductionCanvasDomainContext(context), true);
    assert.equal(
      hasProductionCanvasDomainContext({
        virtual_ip_id: null,
        environment_id: null,
        story_id: null,
        episode_id: null,
        script_id: null,
        timeline_id: null,
        timeline_version: null,
        clip_id: null,
        task_id: null,
      }),
      true,
    );
  });

  it("hydrates story and Timeline lineage from a script result", async () => {
    const requests: string[] = [];
    globalThis.fetch = async (input) => {
      const url = String(input);
      requests.push(url);
      if (url === "/api/v1/scripts/321") {
        return new Response(
          JSON.stringify({
            id: 321,
            business_id: "script-321",
            episode_id: 123,
            title: "第 4 集",
            format_type: "short_drama",
            language: "zh-CN",
            status: "completed",
            version: "1",
            extra_metadata: {
              production_pipeline: {
                auto_timeline_pipeline: {
                  timeline_spec: { id: 71, version: 6 },
                },
              },
            },
            created_at: "2026-07-15T00:00:00Z",
            updated_at: "2026-07-15T00:00:00Z",
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      assert.equal(url, "/api/v1/episodes/123");
      return new Response(JSON.stringify({ id: 123, story_id: 10 }), {
        headers: { "content-type": "application/json" },
      });
    };

    const context = await resolveProductionCanvasTaskResultContext(
      task({ result_file_path: "script:321" }),
    );

    assert.deepEqual(context, {
      script_id: 321,
      episode_id: 123,
      timeline_id: 71,
      timeline_version: 6,
      story_id: 10,
    });
    assert.deepEqual(requests, ["/api/v1/scripts/321", "/api/v1/episodes/123"]);
  });

  it("hydrates full lineage from a historical Timeline-only result", async () => {
    const requests: string[] = [];
    globalThis.fetch = async (input) => {
      const url = String(input);
      requests.push(url);
      if (url === "/api/v1/timelines/71") {
        return new Response(
          JSON.stringify({
            id: 71,
            business_id: "timeline-71",
            episode_id: 123,
            script_id: 321,
            title: "Timeline",
            status: "ready",
            spec: { id: 71, version: 6, tracks: [] },
            version: 6,
            created_at: "2026-07-15T00:00:00Z",
            updated_at: "2026-07-15T00:00:00Z",
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url === "/api/v1/scripts/321") {
        return new Response(
          JSON.stringify({
            id: 321,
            business_id: "script-321",
            episode_id: 123,
            title: "Script",
            format_type: "short_drama",
            language: "zh-CN",
            status: "completed",
            version: "1",
            created_at: "2026-07-15T00:00:00Z",
            updated_at: "2026-07-15T00:00:00Z",
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      assert.equal(url, "/api/v1/episodes/123");
      return new Response(JSON.stringify({ id: 123, story_id: 10 }), {
        headers: { "content-type": "application/json" },
      });
    };

    const context = await resolveProductionCanvasTaskResultContext(
      task({ result_file_path: "timeline:71:v6" }),
    );

    assert.deepEqual(context, {
      timeline_id: 71,
      timeline_version: 6,
      script_id: 321,
      episode_id: 123,
      story_id: 10,
    });
    assert.deepEqual(requests, [
      "/api/v1/timelines/71",
      "/api/v1/scripts/321",
      "/api/v1/episodes/123",
    ]);
  });
});
