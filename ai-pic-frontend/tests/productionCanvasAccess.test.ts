import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasCapabilities } from "../src/components/features/canvas/productionCanvasAccess";

describe("production canvas access capabilities", () => {
  it("maps every collaboration role to the backend capability contract", () => {
    assert.deepEqual(productionCanvasCapabilities("viewer"), {
      approve: false,
      comment: false,
      edit: false,
      execute: false,
      manage: false,
      view: true,
    });
    assert.equal(productionCanvasCapabilities("commenter").comment, true);
    assert.equal(productionCanvasCapabilities("commenter").edit, false);
    assert.equal(productionCanvasCapabilities("editor").edit, true);
    assert.equal(productionCanvasCapabilities("editor").execute, false);
    assert.equal(productionCanvasCapabilities("approver").approve, true);
    assert.equal(productionCanvasCapabilities("approver").edit, false);
    assert.deepEqual(productionCanvasCapabilities("owner"), {
      approve: true,
      comment: true,
      edit: true,
      execute: true,
      manage: true,
      view: true,
    });
    assert.equal(productionCanvasCapabilities(null).view, false);
  });
});
