import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  emptyProductionCanvasFilters,
  filterProductionCanvasNodes,
  productionCanvasFilterFacets,
} from "../src/components/features/canvas/productionCanvasFilters";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const nodes: ProductionCanvasNode[] = [
  {
    id: "image-scene-12",
    label: "Image Candidates",
    title: "办公室关键帧",
    status: "stale",
    x: 0,
    y: 0,
    width: 200,
    kind: "skill_result",
    outputs: { scene_id: 12, owner_name: "林导" },
  },
  {
    id: "video-scene-13",
    label: "Video Candidates",
    title: "天台镜头",
    status: "running",
    x: 240,
    y: 0,
    width: 200,
    kind: "skill_result",
    outputs: { scene_ids: [13], reviewed_by: "周制片" },
  },
];

describe("production canvas filters", () => {
  it("builds scene, type, status, and owner facets", () => {
    assert.deepEqual(productionCanvasFilterFacets(nodes), {
      scenes: ["12", "13"],
      types: ["Image Candidates", "Video Candidates"],
      statuses: ["生成中", "已过期"],
      owners: ["林导", "周制片"],
    });
  });

  it("combines text and production metadata filters", () => {
    assert.deepEqual(
      filterProductionCanvasNodes(nodes, {
        ...emptyProductionCanvasFilters,
        query: "办公室",
        scene: "12",
        type: "Image Candidates",
        status: "已过期",
        owner: "林导",
      }).map((node) => node.id),
      ["image-scene-12"],
    );
    assert.deepEqual(
      filterProductionCanvasNodes(nodes, {
        ...emptyProductionCanvasFilters,
        status: "生成中",
        owner: "林导",
      }),
      [],
    );
  });
});
