import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildHierarchyRoots,
  buildIpHierarchyBranch,
  buildStoryHierarchyBranch,
  countLoadedDescendants,
  hierarchyContextPatch,
  mergeHierarchyGraphs,
  projectVisibleHierarchy,
} from "../src/components/features/canvas/productionCanvasHierarchyModel";
import { visibleEnvironmentReferenceEdges } from "../src/components/features/canvas/productionCanvasHierarchyReferences";
import {
  buildEpisodeHierarchyBranch,
  buildStoryboardVideoBranch,
} from "../src/components/features/canvas/productionCanvasHierarchyTimeline";
import {
  assetLink,
  clip,
  environmentLink,
  episode,
  story,
  timelineResponse,
  virtualIp,
} from "./productionCanvasHierarchyModelFixture";

describe("production canvas hierarchy model", () => {
  it("models environments as reusable IP resources, not Story ownership", () => {
    const graph = mergeHierarchyGraphs(
      buildHierarchyRoots([virtualIp(1)]),
      buildIpHierarchyBranch(
        1,
        [environmentLink(1, 8, 1), environmentLink(1, 8, 2)],
        [story(10, [1]), story(20, [2])],
      ),
    );
    const projection = projectVisibleHierarchy(graph, ["ip:1"]);
    const references = visibleEnvironmentReferenceEdges(graph, projection);

    assert.deepEqual(
      graph.nodes.map((node) => node.id),
      ["ip:1", "environment:8", "story:10"],
    );
    assert.equal(
      graph.edges.some(
        (edge) => edge.from === "environment:8" && edge.to === "story:10",
      ),
      false,
    );
    assert.deepEqual(
      graph.edges.map((edge) => [edge.relationType, edge.label]),
      [
        ["resource", "环境资源"],
        ["participation", "参与故事"],
      ],
    );
    assert.deepEqual(
      references.map((edge) => [edge.relationType, edge.label, edge.contextId]),
      [["reference", "可用环境", "ip:1"]],
    );
  });

  it("deduplicates shared entities and keeps the preferred current IP", () => {
    const shared = story(10, [1, 2]);
    const graph = mergeHierarchyGraphs(
      buildHierarchyRoots([virtualIp(1), virtualIp(2)]),
      buildIpHierarchyBranch(
        1,
        [environmentLink(1, 8)],
        [story(9, [1]), shared],
      ),
      buildIpHierarchyBranch(2, [environmentLink(2, 8)], [shared]),
    );

    assert.equal(
      graph.nodes.filter((node) => node.id === "story:10").length,
      1,
    );
    assert.deepEqual(
      graph.nodes.find((node) => node.id === "story:10")?.parentIds,
      ["ip:1", "ip:2"],
    );
    assert.equal(
      graph.nodes.filter((node) => node.id === "environment:8").length,
      1,
    );
    assert.deepEqual(hierarchyContextPatch(graph, "story:10", 2), {
      virtual_ip_id: 2,
      story_id: 10,
    });
  });

  it("projects fixed columns progressively and preserves y after collapse", () => {
    const timeline = timelineResponse(501, 7, 100, [clip("clip-a")]);
    const episodeBranch = buildEpisodeHierarchyBranch(100, [timeline]);
    const storyboard = episodeBranch.nodes[0];
    const videoBranch = buildStoryboardVideoBranch(storyboard, [
      assetLink(901, 701, 7, "clip-a"),
    ]);
    const graph = mergeHierarchyGraphs(
      buildHierarchyRoots([virtualIp(1)]),
      buildIpHierarchyBranch(1, [environmentLink(1, 8)], [story(10, [1])]),
      buildStoryHierarchyBranch(10, [episode(100, 10)]),
      episodeBranch,
      videoBranch,
    );

    const collapsed = projectVisibleHierarchy(graph, []);
    assert.deepEqual(
      collapsed.nodes.map((node) => node.id),
      ["ip:1"],
    );
    assert.deepEqual(
      [
        collapsed.nodes[0].x,
        collapsed.nodes[0].y,
        collapsed.nodes[0].width,
        collapsed.nodes[0].height,
      ],
      [40, 88, 220, 116],
    );
    assert.equal(collapsed.nodes[0].hiddenDescendantCount, 5);
    assert.equal(countLoadedDescendants(graph, "story:10"), 3);

    const throughEpisode = projectVisibleHierarchy(graph, [
      "ip:1",
      "story:10",
      "episode:100",
    ]);
    assert.equal(
      throughEpisode.nodes.find((node) => node.id === "environment:8")?.x,
      320,
    );
    assert.equal(
      throughEpisode.nodes.find((node) => node.id === "story:10")?.x,
      600,
    );
    assert.equal(
      throughEpisode.nodes.find((node) => node.id === "episode:100")?.x,
      880,
    );
    const storyboardBefore = throughEpisode.nodes.find(
      (node) => node.id === "storyboard:100:clip-a",
    );
    assert.equal(storyboardBefore?.x, 1160);
    assert.equal(
      throughEpisode.nodes.some((node) => node.entityType === "video"),
      false,
    );

    const expanded = projectVisibleHierarchy(graph, [
      "ip:1",
      "story:10",
      "episode:100",
      "storyboard:100:clip-a",
    ]);
    const videoBefore = expanded.nodes.find((node) => node.id === "video:901");
    const reopened = projectVisibleHierarchy(graph, [
      "ip:1",
      "story:10",
      "episode:100",
      "storyboard:100:clip-a",
    ]);
    assert.equal(videoBefore?.x, 1440);
    assert.equal(
      throughEpisode.nodes.find((node) => node.id === storyboardBefore?.id)?.y,
      reopened.nodes.find((node) => node.id === storyboardBefore?.id)?.y,
    );
    assert.equal(
      videoBefore?.y,
      reopened.nodes.find((node) => node.id === "video:901")?.y,
    );
  });

  it("keeps empty results behind their expanded parent", () => {
    const graph = mergeHierarchyGraphs(
      buildHierarchyRoots([virtualIp(1)]),
      buildIpHierarchyBranch(1, [], []),
    );
    assert.deepEqual(
      projectVisibleHierarchy(graph, []).nodes.map((node) => node.id),
      ["ip:1"],
    );
    assert.equal(
      projectVisibleHierarchy(graph, ["ip:1"]).nodes.filter(
        (node) => node.empty,
      ).length,
      2,
    );
  });
});
