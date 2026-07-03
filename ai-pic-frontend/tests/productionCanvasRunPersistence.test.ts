import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { productionCanvasRunIdFromInput } from "../src/components/features/canvas/useProductionCanvasRunPersistence";

describe("productionCanvasRunIdFromInput", () => {
  it("normalizes raw run ids and pasted canvas links", () => {
    assert.equal(
      productionCanvasRunIdFromInput(" canvas-run-123 "),
      "canvas-run-123",
    );
    assert.equal(
      productionCanvasRunIdFromInput(
        "http://localhost/canvas?run_id=canvas-run-123",
      ),
      "canvas-run-123",
    );
    assert.equal(
      productionCanvasRunIdFromInput("/canvas?run_id=canvas-run-456"),
      "canvas-run-456",
    );
    assert.equal(productionCanvasRunIdFromInput("/canvas?run_id="), "");
    assert.equal(productionCanvasRunIdFromInput("/canvas"), "");
    assert.equal(productionCanvasRunIdFromInput("http://localhost/canvas"), "");
    assert.equal(productionCanvasRunIdFromInput("http://["), "http://[");
  });
});
