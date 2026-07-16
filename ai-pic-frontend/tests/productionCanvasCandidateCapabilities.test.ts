import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  canBranchProductionCanvasCandidate,
  canDirectlyPlaceProductionCanvasVideo,
  isProductionCanvasReviewNode,
} from "../src/components/features/canvas/productionCanvasCandidateCapabilities";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const node = (
  skill: string,
  outputs?: Record<string, unknown>,
): ProductionCanvasNode => ({
  id: skill,
  label: skill,
  title: skill,
  status: "review",
  x: 0,
  y: 0,
  width: 220,
  skill,
  outputs,
});

describe("production canvas candidate capabilities", () => {
  it("reviews storyboards without exposing candidate branching", () => {
    const storyboard = node("storyboard.candidates");

    assert.equal(isProductionCanvasReviewNode(storyboard), true);
    assert.equal(canBranchProductionCanvasCandidate(storyboard, true), false);
  });

  it("uses the explicit placement node for clip-storyboard videos", () => {
    const explicit = node("video.candidates", {
      candidate_branching: "disabled",
      placement_mode: "explicit_node",
    });
    const legacy = node("video.candidates");

    assert.equal(canBranchProductionCanvasCandidate(explicit, true), false);
    assert.equal(canDirectlyPlaceProductionCanvasVideo(explicit), false);
    assert.equal(canDirectlyPlaceProductionCanvasVideo(legacy), true);
  });
});
