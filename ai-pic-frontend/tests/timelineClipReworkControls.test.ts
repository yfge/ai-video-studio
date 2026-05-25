import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildTimelineClipReworkPayload } from "../src/components/features/episode/TimelineClipReworkControls";

describe("timeline clip rework controls", () => {
  it("builds compact timeline clip rework payloads", () => {
    assert.deepEqual(
      buildTimelineClipReworkPayload({
        expectedVersion: 3,
        action: "re_render",
        mediaAssetId: 42,
        assetRole: " render_output ",
        reason: " cleaner export ",
      }),
      {
        expected_version: 3,
        action: "re_render",
        media_asset_id: 42,
        asset_role: "render_output",
        reason: "cleaner export",
      },
    );
  });
});
