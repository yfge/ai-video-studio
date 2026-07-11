import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { loadProductionCanvasCandidates } from "../src/components/features/canvas/productionCanvasCandidateLoading";

describe("production canvas candidate loading", () => {
  it("retries one not-found response while a new template node autosaves", async () => {
    let requests = 0;
    let waits = 0;
    const response = await loadProductionCanvasCandidates(
      "run-1",
      "template-node",
      async () => {
        requests += 1;
        return requests === 1
          ? { success: false, error: "HTTP 404: Not Found" }
          : {
              success: true,
              data: {
                candidates: [],
                node_id: "template-node",
                stale_impact: [],
              },
            };
      },
      async () => {
        waits += 1;
      },
    );

    assert.equal(response.success, true);
    assert.equal(requests, 2);
    assert.equal(waits, 1);
  });

  it("does not retry non-transient failures", async () => {
    let requests = 0;
    const response = await loadProductionCanvasCandidates(
      "run-1",
      "node-1",
      async () => {
        requests += 1;
        return { success: false, error: "HTTP 403: Forbidden" };
      },
      async () => assert.fail("wait should not run"),
    );

    assert.equal(response.success, false);
    assert.equal(requests, 1);
  });
});
