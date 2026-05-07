import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  firstTimelineItemId,
  resolveTimelineSelection,
} from "../src/components/features/Timeline/timelineViewModel";
import type { TimelineTrack } from "../src/components/features/Timeline/Timeline";
import { episodeWorkspaceHref } from "../src/utils/routes";

const tracks: TimelineTrack[] = [
  {
    id: "dialogue",
    label: "对白",
    items: [
      {
        id: "beat-1",
        startMs: 0,
        endMs: 1200,
        label: "开场对白",
      },
    ],
  },
  {
    id: "storyboard",
    label: "分镜",
    items: [
      {
        id: "frame-1",
        startMs: 0,
        endMs: 1200,
        label: "主角推门",
      },
    ],
  },
];

describe("timeline workspace helpers", () => {
  it("defaults episode workspace links to the timeline tab", () => {
    assert.equal(
      episodeWorkspaceHref("episode_123"),
      "/episodes/episode_123/workspace?tab=timeline",
    );
  });

  it("resolves the selected timeline item and first fallback item", () => {
    const selection = resolveTimelineSelection(tracks, "frame-1");

    assert.equal(firstTimelineItemId(tracks), "beat-1");
    assert.equal(selection.item?.label, "主角推门");
    assert.equal(selection.track?.id, "storyboard");
    assert.deepEqual(resolveTimelineSelection(tracks, "missing"), {
      item: null,
      track: null,
    });
  });
});
