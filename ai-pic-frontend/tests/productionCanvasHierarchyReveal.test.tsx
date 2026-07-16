import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { useState } from "react";

import { ProductionCanvasHierarchyView } from "../src/components/features/canvas/ProductionCanvasHierarchyView";
import {
  emptyProductionCanvasContext,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "../src/components/features/canvas/productionCanvasContext";
import {
  revealProductionCanvasHierarchy,
  type ProductionCanvasHierarchySyncRequest,
} from "../src/components/features/canvas/productionCanvasHierarchyReveal";
import {
  hierarchyPaths,
  installHierarchyFetch,
} from "./productionCanvasHierarchyFixture";
import { dom, hierarchyNode } from "./productionCanvasHierarchyTestDom";

let restoreFetch = () => {};

function SyncHarness({
  isActive = true,
  request,
}: {
  isActive?: boolean;
  request: ProductionCanvasHierarchySyncRequest;
}) {
  const [context, setContext] = useState<ProductionCanvasContextDraft>(
    emptyProductionCanvasContext,
  );
  const setContextValue = (key: ProductionCanvasContextKey, value: string) => {
    setContext((current) => ({ ...current, [key]: value }));
  };
  return (
    <ProductionCanvasHierarchyView
      context={context}
      isActive={isActive}
      syncRequest={request}
      onContextChange={setContextValue}
    />
  );
}

describe("ProductionCanvasHierarchy result reveal", () => {
  afterEach(() => {
    cleanup();
    restoreFetch();
    restoreFetch = () => {};
    dom.window.document.body.replaceChildren();
  });

  it("loads every ancestor and returns the generated video target", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;

    const result = await revealProductionCanvasHierarchy({
      virtual_ip_id: 1,
      story_id: 10,
      episode_id: 100,
      script_id: 300,
      timeline_id: 501,
      timeline_version: 7,
      clip_id: "clip-ready",
    });

    assert.equal(result.targetNodeId, "video:901");
    assert.deepEqual(
      [...result.expandedIds],
      ["ip:1", "story:10", "episode:100", "storyboard:100:clip-ready"],
    );
    assert.ok(result.graph.nodes.some((node) => node.id === "video:901"));
    assert.equal(fetchStub.count(hierarchyPaths.clipAssets("clip-ready")), 1);
    assert.equal(fetchStub.count(hierarchyPaths.clipTasks), 1);
  });

  it("reveals an explicitly bound non-latest Script Timeline", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;

    const result = await revealProductionCanvasHierarchy({
      virtual_ip_id: 1,
      story_id: 10,
      episode_id: 100,
      script_id: 299,
      timeline_id: 599,
      timeline_version: 99,
    });

    assert.equal(result.targetNodeId, "storyboard:100:clip-ready");
    const target = result.graph.nodes.find(
      (node) => node.id === result.targetNodeId,
    );
    assert.equal(target?.scriptId, 299);
    assert.equal(target?.timelineId, 599);
    assert.equal(target?.timelineVersion, 99);
  });

  it("selects and focuses a task result without manual expansion", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const request: ProductionCanvasHierarchySyncRequest = {
      revision: 1,
      context: {
        virtual_ip_id: 1,
        story_id: 10,
        episode_id: 100,
        script_id: 300,
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "clip-ready",
      },
    };
    const utils = render(<SyncHarness request={request} />, {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.equal(
        hierarchyNode(utils.container, "video:901").getAttribute(
          "aria-current",
        ),
        "true",
      );
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(
      dom.window.document.activeElement,
      utils.getByRole("region", { name: "业务实体层级无限画布" }),
    );
  });

  it("does not let an older reveal replace a newer revision", async () => {
    const fetchStub = installHierarchyFetch({ deferFirstEnvironments: true });
    restoreFetch = fetchStub.restore;
    const firstRequest: ProductionCanvasHierarchySyncRequest = {
      revision: 1,
      context: { virtual_ip_id: 1, environment_id: 8, story_id: 10 },
    };
    const utils = render(
      <SyncHarness isActive={false} request={firstRequest} />,
      { container: dom.window.document.body },
    );
    await waitFor(() =>
      assert.equal(fetchStub.count(hierarchyPaths.environments), 1),
    );

    utils.rerender(
      <SyncHarness
        isActive={false}
        request={{ revision: 2, context: { virtual_ip_id: 2 } }}
      />,
    );
    await waitFor(() => {
      assert.equal(
        hierarchyNode(utils.container, "ip:2").getAttribute("aria-current"),
        "true",
      );
    });
    fetchStub.resolveDeferredEnvironments();
    await new Promise((resolve) => setTimeout(resolve, 0));

    assert.equal(
      hierarchyNode(utils.container, "ip:2").getAttribute("aria-current"),
      "true",
    );
    assert.equal(
      utils.container.querySelector('[data-hierarchy-node="environment:8"]'),
      null,
    );
  });

  it("does not let a pending reveal replace a manual hierarchy selection", async () => {
    const fetchStub = installHierarchyFetch({ deferFirstEnvironments: true });
    restoreFetch = fetchStub.restore;
    const utils = render(
      <SyncHarness
        isActive={false}
        request={{ revision: 1, context: { virtual_ip_id: 2 } }}
      />,
      { container: dom.window.document.body },
    );
    await waitFor(() => assert.ok(hierarchyNode(utils.container, "ip:2")));

    utils.rerender(
      <SyncHarness
        isActive={false}
        request={{
          revision: 2,
          context: { virtual_ip_id: 1, environment_id: 8, story_id: 10 },
        }}
      />,
    );
    await waitFor(() =>
      assert.equal(fetchStub.count(hierarchyPaths.environments), 1),
    );
    fireEvent.click(utils.getByLabelText("IP 镜城副角"));
    fetchStub.resolveDeferredEnvironments();
    await new Promise((resolve) => setTimeout(resolve, 0));

    assert.equal(
      hierarchyNode(utils.container, "ip:2").getAttribute("aria-current"),
      "true",
    );
    assert.equal(
      utils.container.querySelector('[data-hierarchy-node="environment:8"]'),
      null,
    );
  });
});
