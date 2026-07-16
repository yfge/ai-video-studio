import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render, waitFor } from "@testing-library/react";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { installHierarchyFetch } from "./productionCanvasHierarchyFixture";
import { dom } from "./productionCanvasHierarchyTestDom";

let restoreFetch = () => {};

describe("ProductionCanvasHierarchy", () => {
  afterEach(() => {
    cleanup();
    restoreFetch();
    restoreFetch = () => {};
    dom.window.localStorage.clear();
    dom.window.document.body.replaceChildren();
  });

  it("starts prompt-first without listing or requesting the asset repository", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialView="hierarchy"
        storageKey={null}
      />,
      { container: dom.window.document.body },
    );

    await waitFor(() =>
      assert.ok(utils.getByRole("region", { name: "业务实体层级无限画布" })),
    );
    assert.ok(utils.getByText("先输入生产目标"));
    assert.equal(utils.container.querySelector("[data-hierarchy-node]"), null);
    assert.deepEqual(fetchStub.requests, []);
  });

  it("keeps the prompt-first hierarchy stable across a clean rerender", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialView="hierarchy"
        storageKey={null}
      />,
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(utils.getByText("先输入生产目标")));
    utils.rerender(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialView="hierarchy"
        storageKey={null}
      />,
    );
    assert.ok(utils.getByText("先输入生产目标"));
    assert.deepEqual(fetchStub.requests, []);
  });

  it("keeps the execution-first contract free of hierarchy requests", async () => {
    const fetchStub = installHierarchyFetch();
    restoreFetch = fetchStub.restore;
    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialView="execution"
        storageKey={null}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByRole("region", { name: "短剧生产链路无限画布" }));
    assert.equal(
      utils.queryByRole("region", { name: "业务实体层级无限画布" }),
      null,
    );
    await Promise.resolve();
    assert.equal(fetchStub.requests.length, 0);
  });
});
