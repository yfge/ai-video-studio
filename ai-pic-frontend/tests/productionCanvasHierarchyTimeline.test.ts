import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { currentHierarchyTimelines } from "../src/components/features/canvas/productionCanvasHierarchyData";
import {
  buildHierarchyRoots,
  buildIpHierarchyBranch,
  buildStoryHierarchyBranch,
  hierarchyContextPatch,
  mergeHierarchyGraphs,
  selectLatestTimeline,
} from "../src/components/features/canvas/productionCanvasHierarchyModel";
import { hierarchyNodeActionHref } from "../src/components/features/canvas/productionCanvasHierarchyRoutes";
import {
  buildEpisodeHierarchyBranch,
  buildStoryboardVideoBranch,
} from "../src/components/features/canvas/productionCanvasHierarchyTimeline";
import {
  assetLink,
  clip,
  clipTask,
  episode,
  scriptVersion,
  story,
  timelineResponse,
  virtualIp,
} from "./productionCanvasHierarchyModelFixture";

describe("production canvas hierarchy Timeline model", () => {
  it("keeps an explicitly selected non-latest Script Timeline", () => {
    const timelines = [
      timelineResponse(599, 99, 100, [], 299),
      timelineResponse(600, 100, 100, [], 300),
    ];
    const scripts = [
      scriptVersion(299, "1", "2026-01-01T00:00:00Z"),
      scriptVersion(300, "2", "2026-01-02T00:00:00Z"),
    ];
    const selected = currentHierarchyTimelines(timelines, scripts, {
      script_id: 299,
      timeline_id: 599,
      timeline_version: 99,
    });

    assert.deepEqual(
      selected.map((timeline) => timeline.id),
      [599],
    );
  });

  it("selects the latest Script by version, then created_at, then id", () => {
    const timelines = [
      timelineResponse(500, 1, 100, [], 300),
      timelineResponse(501, 1, 100, [], 301),
      timelineResponse(502, 1, 100, [], 302),
      timelineResponse(503, 1, 100, [], 303),
    ];
    const byVersion = currentHierarchyTimelines(timelines, [
      scriptVersion(300, "1", "2026-01-03T00:00:00Z"),
      scriptVersion(301, "2", "2026-01-01T00:00:00Z"),
    ]);
    const byCreatedAt = currentHierarchyTimelines(timelines, [
      scriptVersion(301, "2", "2026-01-01T00:00:00Z"),
      scriptVersion(302, "2", "2026-01-02T00:00:00Z"),
    ]);
    const byId = currentHierarchyTimelines(timelines, [
      scriptVersion(302, "2", "2026-01-02T00:00:00Z"),
      scriptVersion(303, "2", "2026-01-02T00:00:00Z"),
    ]);

    assert.deepEqual(
      byVersion.map((item) => item.script_id),
      [301],
    );
    assert.deepEqual(
      byCreatedAt.map((item) => item.script_id),
      [302],
    );
    assert.deepEqual(
      byId.map((item) => item.script_id),
      [303],
    );
  });

  it("selects the latest Timeline by version, then id", () => {
    const olderVersion = timelineResponse(999, 6, 100, []);
    olderVersion.updated_at = "2030-01-01T00:00:00Z";
    assert.equal(
      selectLatestTimeline([
        olderVersion,
        timelineResponse(500, 7, 100, []),
        timelineResponse(501, 7, 100, []),
      ])?.id,
      501,
    );
  });

  it("loads videos only from real current-version clip assets", () => {
    const timeline = timelineResponse(501, 7, 100, [
      clip("clip-ready"),
      clip("clip-generating"),
      clip("clip-missing"),
    ]);
    const episodeBranch = buildEpisodeHierarchyBranch(100, [timeline]);
    assert.deepEqual(
      episodeBranch.nodes.map((node) => node.id),
      [
        "storyboard:100:clip-ready",
        "storyboard:100:clip-generating",
        "storyboard:100:clip-missing",
      ],
    );
    assert.equal(
      episodeBranch.nodes.some((node) => node.entityType === "video"),
      false,
    );

    const [readyStoryboard, generatingStoryboard, missingStoryboard] =
      episodeBranch.nodes;
    const readyBranch = buildStoryboardVideoBranch(readyStoryboard, [
      assetLink(900, 700, 6, "clip-ready"),
      assetLink(901, 701, 7, "clip-ready"),
    ]);
    const generatingBranch = buildStoryboardVideoBranch(
      generatingStoryboard,
      [],
      [clipTask("clip-generating")],
    );
    const missingBranch = buildStoryboardVideoBranch(missingStoryboard, []);

    assert.deepEqual(
      readyBranch.nodes.map((node) => node.id),
      ["video:901"],
    );
    assert.equal(readyBranch.nodes[0].assetLinkId, 901);
    assert.equal(readyBranch.nodes[0].entityId, 701);
    assert.equal(readyBranch.nodes[0].videoUrl, "https://cdn.test/701.mp4");
    assert.deepEqual(
      [generatingBranch.nodes[0].empty, generatingBranch.nodes[0].status],
      [true, "generating"],
    );
    assert.deepEqual(
      [missingBranch.nodes[0].empty, missingBranch.nodes[0].status],
      [true, "missing"],
    );
  });

  it("propagates scriptId into execution context and workspace routes", () => {
    const timeline = timelineResponse(501, 7, 100, [clip("clip-ready")], 300);
    const episodeBranch = buildEpisodeHierarchyBranch(100, [timeline]);
    const videoBranch = buildStoryboardVideoBranch(episodeBranch.nodes[0], [
      assetLink(901, 701, 7, "clip-ready"),
    ]);
    const graph = mergeHierarchyGraphs(
      buildHierarchyRoots([virtualIp(1)]),
      buildIpHierarchyBranch(1, [], [story(10, [1])]),
      buildStoryHierarchyBranch(10, [episode(100, 10)]),
      episodeBranch,
      videoBranch,
    );
    const video = videoBranch.nodes[0];

    assert.deepEqual(hierarchyContextPatch(graph, "video:901"), {
      virtual_ip_id: 1,
      story_id: 10,
      episode_id: 100,
      script_id: 300,
      timeline_id: 501,
      timeline_version: 7,
      clip_id: "clip-ready",
    });
    assert.equal(
      hierarchyNodeActionHref(video),
      "/episodes/100/workspace?tab=timeline&scriptId=300&clipId=clip-ready",
    );
  });
});
