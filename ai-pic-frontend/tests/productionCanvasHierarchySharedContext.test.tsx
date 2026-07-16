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
  productionCanvasContextDraftFromResolved,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "../src/components/features/canvas/productionCanvasContext";
import type { ProductionCanvasHierarchySyncRequest } from "../src/components/features/canvas/productionCanvasHierarchyReveal";
import { installHierarchyFetch } from "./productionCanvasHierarchyFixture";
import { dom, expectNode } from "./productionCanvasHierarchyTestDom";

function ContextHarness({
  request,
}: {
  request: ProductionCanvasHierarchySyncRequest;
}) {
  const [context, setContext] = useState<ProductionCanvasContextDraft>(
    request.revision
      ? productionCanvasContextDraftFromResolved(request.context)
      : emptyProductionCanvasContext,
  );
  const setContextValue = (key: ProductionCanvasContextKey, value: string) => {
    setContext((current) => ({ ...current, [key]: value }));
  };
  return (
    <>
      <ProductionCanvasHierarchyView
        context={context}
        syncRequest={request}
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

  it("keeps the prompt-selected IP when a shared Story is selected", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const utils = render(
      <ContextHarness
        request={{
          revision: 1,
          context: { virtual_ip_id: 2, story_id: 10 },
        }}
      />,
      { container: dom.window.document.body },
    );

    await expectNode(utils.container, "ip:2");
    await expectNode(utils.container, "story:10");

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
    const utils = render(
      <ContextHarness
        request={{
          revision: 1,
          context: {
            virtual_ip_id: 1,
            environment_id: 8,
            story_id: 10,
            episode_id: 100,
            script_id: 300,
            timeline_id: 501,
            timeline_version: 7,
            clip_id: "clip-ready",
          },
        }}
      />,
      { container: dom.window.document.body },
    );

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
