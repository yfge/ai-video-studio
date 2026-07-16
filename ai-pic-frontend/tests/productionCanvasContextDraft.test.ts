import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { ProductionCanvasContextDraft } from "../src/components/features/canvas/productionCanvasContext";
import {
  mergeProductionCanvasResolvedContext,
  productionCanvasContextOutputPatch,
  setProductionCanvasContextValue,
} from "../src/components/features/canvas/productionCanvasContextMerge";
import { mergeProductionCanvasHierarchySyncContext } from "../src/components/features/canvas/productionCanvasHierarchySync";

const fullContext: ProductionCanvasContextDraft = {
  virtual_ip_id: "1",
  environment_id: "8",
  story_id: "10",
  episode_id: "100",
  script_id: "300",
  timeline_id: "501",
  timeline_version: "7",
  clip_id: "clip-old",
  task_id: "99",
};

describe("production canvas context lineage merge", () => {
  it("clears stale Timeline and clip descendants for a new Script task", () => {
    assert.deepEqual(
      mergeProductionCanvasResolvedContext(fullContext, { script_id: 301 }),
      {
        ...fullContext,
        script_id: "301",
        timeline_id: "",
        timeline_version: "",
        clip_id: "",
        task_id: "",
      },
    );
  });

  it("keeps the Story chain when only the same-IP environment changes", () => {
    assert.deepEqual(
      mergeProductionCanvasResolvedContext(fullContext, {
        environment_id: 9,
      }),
      { ...fullContext, environment_id: "9", task_id: "" },
    );
  });

  it("clears environment and Story descendants when IP changes", () => {
    assert.deepEqual(
      mergeProductionCanvasResolvedContext(fullContext, { virtual_ip_id: 2 }),
      {
        virtual_ip_id: "2",
        environment_id: "",
        story_id: "",
        episode_id: "",
        script_id: "",
        timeline_id: "",
        timeline_version: "",
        clip_id: "",
        task_id: "",
      },
    );
  });

  it("clears hidden Timeline and clip fields when the form changes Episode", () => {
    assert.deepEqual(
      setProductionCanvasContextValue(fullContext, "episode_id", "101"),
      {
        ...fullContext,
        episode_id: "101",
        script_id: "",
        timeline_id: "",
        timeline_version: "",
        clip_id: "",
        task_id: "",
      },
    );
  });

  it("emits explicit removals when a Task changes Timeline without a clip", () => {
    const patch = productionCanvasContextOutputPatch(
      {
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "clip-old",
        task_id: 99,
      },
      { timeline_id: 502, timeline_version: 1, task_id: 200 },
    );
    assert.equal(patch.timeline_id, 502);
    assert.equal(patch.timeline_version, 1);
    assert.equal(patch.clip_id, undefined);
    assert.equal(patch.task_id, 200);
  });

  it("clears the hierarchy reveal clip on a partial Timeline update", () => {
    assert.deepEqual(
      mergeProductionCanvasHierarchySyncContext(
        {
          story_id: 10,
          episode_id: 100,
          script_id: 300,
          timeline_id: 501,
          timeline_version: 7,
          clip_id: "clip-old",
          task_id: 99,
        },
        { timeline_id: 502, timeline_version: 1 },
        false,
      ),
      {
        story_id: 10,
        episode_id: 100,
        script_id: 300,
        timeline_id: 502,
        timeline_version: 1,
      },
    );
  });

  it("replaces the hierarchy with an explicitly empty context", () => {
    assert.deepEqual(
      mergeProductionCanvasHierarchySyncContext(
        {
          story_id: 10,
          episode_id: 100,
          script_id: 300,
          timeline_id: 501,
          timeline_version: 7,
          clip_id: "clip-old",
        },
        {
          virtual_ip_id: null,
          environment_id: null,
          story_id: null,
          episode_id: null,
          script_id: null,
          timeline_id: null,
          timeline_version: null,
          clip_id: null,
          task_id: null,
        },
        true,
      ),
      {},
    );
  });
});
