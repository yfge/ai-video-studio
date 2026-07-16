import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import {
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";
import { useState } from "react";

import { ProductionCanvasHierarchyView } from "../src/components/features/canvas/ProductionCanvasHierarchyView";
import {
  emptyProductionCanvasContext,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "../src/components/features/canvas/productionCanvasContext";
import {
  hierarchyPaths,
  installHierarchyFetch,
} from "./productionCanvasHierarchyFixture";
import { dom, expand, expectNode } from "./productionCanvasHierarchyTestDom";

function ContextHarness() {
  const [context, setContext] = useState<ProductionCanvasContextDraft>(
    emptyProductionCanvasContext,
  );
  const setContextValue = (key: ProductionCanvasContextKey, value: string) => {
    setContext((current) => ({ ...current, [key]: value }));
  };
  return (
    <>
      <ProductionCanvasHierarchyView
        context={context}
        onContextChange={setContextValue}
      />
      <output aria-label="当前 IP 上下文">{context.virtual_ip_id}</output>
      <output aria-label="当前领域上下文">{JSON.stringify(context)}</output>
    </>
  );
}

describe("ProductionCanvasHierarchy shared context", () => {
  let restoreFetch = () => {};

  afterEach(() => {
    cleanup();
    restoreFetch();
    restoreFetch = () => {};
    dom.window.document.body.replaceChildren();
  });

  it("uses the second IP context when its outline selects a shared Story", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const utils = render(<ContextHarness />, {
      container: dom.window.document.body,
    });

    await expectNode(utils.container, "ip:1");
    await expectNode(utils.container, "ip:2");
    expand(utils.container, "ip:1");
    await expectNode(utils.container, "story:10");
    expand(utils.container, "ip:2");
    await waitFor(() =>
      assert.equal(fetchStub.count(hierarchyPaths.secondEnvironments), 1),
    );

    const outline = utils.getByText("层级大纲").parentElement?.parentElement;
    assert.ok(outline);
    const secondIp = outline.querySelector<HTMLButtonElement>(
      'button[title="业务实体 · 镜城副角"]',
    );
    assert.ok(secondIp);
    const secondBranch = secondIp.closest("li");
    assert.ok(secondBranch);
    fireEvent.click(within(secondBranch).getByTitle("参与故事 · 镜城来信"));

    await waitFor(() =>
      assert.equal(utils.getByLabelText("当前 IP 上下文").textContent, "2"),
    );
  });

  it("writes the full video lineage and preserves a same-IP environment", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const utils = render(<ContextHarness />, {
      container: dom.window.document.body,
    });

    await expectNode(utils.container, "ip:1");
    expand(utils.container, "ip:1");
    await expectNode(utils.container, "environment:8");
    await expectNode(utils.container, "story:10");
    fireEvent.click(utils.getByLabelText("环境 雨夜天台"));
    expand(utils.container, "story:10");
    await expectNode(utils.container, "episode:100");
    expand(utils.container, "episode:100");
    await expectNode(utils.container, "storyboard:100:clip-ready");
    expand(utils.container, "storyboard:100:clip-ready");
    await expectNode(utils.container, "video:901");
    fireEvent.click(utils.getByLabelText("视频 视频资产 #701"));

    await waitFor(() => {
      const context = JSON.parse(
        utils.getByLabelText("当前领域上下文").textContent || "{}",
      );
      assert.deepEqual(context, {
        virtual_ip_id: "1",
        environment_id: "8",
        story_id: "10",
        episode_id: "100",
        script_id: "300",
        timeline_id: "501",
        timeline_version: "7",
        clip_id: "clip-ready",
        task_id: "",
      });
    });
  });
});
