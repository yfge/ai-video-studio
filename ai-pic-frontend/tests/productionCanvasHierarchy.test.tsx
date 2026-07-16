import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import {
  act,
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import {
  hierarchyPaths,
  installHierarchyFetch,
} from "./productionCanvasHierarchyFixture";
import {
  dom,
  expand,
  expectNode,
  hierarchyNode,
} from "./productionCanvasHierarchyTestDom";

let restoreFetch = () => {};

describe("ProductionCanvasHierarchy", () => {
  afterEach(() => {
    cleanup();
    restoreFetch();
    restoreFetch = () => {};
    dom.window.localStorage.clear();
    dom.window.document.body.replaceChildren();
  });

  it("loads and progressively explores the truthful six-column hierarchy", async () => {
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
    assert.deepEqual(
      [...utils.container.querySelectorAll("[data-hierarchy-column]")].map(
        (column) => column.textContent,
      ),
      ["IP", "环境", "故事", "剧集", "分镜", "视频"],
    );
    await expectNode(utils.container, "ip:1");
    assert.deepEqual(fetchStub.requests, [hierarchyPaths.roots]);

    expand(utils.container, "ip:1");
    await expectNode(utils.container, "environment:8");
    await expectNode(utils.container, "story:10");
    assert.equal(fetchStub.count(hierarchyPaths.environments), 1);
    assert.equal(fetchStub.count(hierarchyPaths.stories), 1);
    assert.ok(
      utils.container.querySelector(
        '[data-hierarchy-edge="participation:ip:1->story:10"]',
      ),
    );

    fireEvent.click(utils.getByLabelText("显示环境引用（虚线）"));
    const environmentStoryEdges = [
      ...utils.container.querySelectorAll<HTMLElement>("[data-hierarchy-edge]"),
    ].filter(
      (edge) => edge.dataset.hierarchyEdge?.includes("environment:8->story:10"),
    );
    assert.equal(environmentStoryEdges.length, 1);
    assert.equal(
      environmentStoryEdges[0]?.dataset.hierarchyRelation,
      "reference",
      "Environment → Story must remain a reusable reference, not ownership",
    );

    expand(utils.container, "story:10");
    await expectNode(utils.container, "episode:100");
    assert.equal(fetchStub.count(hierarchyPaths.episodes), 1);
    expand(utils.container, "episode:100");
    await expectNode(utils.container, "storyboard:100:clip-ready");
    assert.equal(fetchStub.count(hierarchyPaths.scripts), 1);
    assert.equal(fetchStub.count(hierarchyPaths.timelines), 1);
    assert.equal(fetchStub.count(hierarchyPaths.clipTasks), 0);
    assert.equal(
      utils.container.querySelector("[data-hierarchy-entity-type=video]"),
      null,
      "Episode expansion must stop at Timeline storyboards",
    );

    expand(utils.container, "storyboard:100:clip-ready");
    await expectNode(utils.container, "video:901");
    assert.equal(
      utils.container.querySelector('[data-hierarchy-node="video:900"]'),
      null,
      "stale Timeline-version assets must not leak into the graph",
    );
    expand(utils.container, "storyboard:100:clip-generating");
    await expectNode(
      utils.container,
      "video:empty:storyboard:100:clip-generating",
    );
    expand(utils.container, "storyboard:100:clip-missing");
    await expectNode(
      utils.container,
      "video:empty:storyboard:100:clip-missing",
    );
    for (const clipId of ["clip-ready", "clip-generating", "clip-missing"]) {
      assert.equal(
        fetchStub.count(hierarchyPaths.clipAssets(clipId)),
        1,
        `expected current-version asset request for ${clipId}`,
      );
    }
    assert.equal(fetchStub.count(hierarchyPaths.clipTasks), 3);
    assert.ok(utils.getByLabelText("视频 视频资产 #701"));
    assert.ok(utils.getByLabelText("视频 视频生成中"));
    assert.ok(utils.getByLabelText("视频 暂无当前版本视频"));

    fireEvent.click(utils.getByLabelText("分镜 雨幕中的信"));
    assert.ok(utils.getByText("stable clip"));
    assert.ok(utils.getByText("clip-ready"));

    const canvas = utils.getByRole("region", {
      name: "业务实体层级无限画布",
    });
    fireEvent.click(utils.getByTitle("参与故事 · 镜城来信"));
    await waitFor(() => {
      assert.equal(dom.window.document.activeElement, canvas);
      assert.equal(
        hierarchyNode(utils.container, "story:10").getAttribute("aria-current"),
        "true",
      );
    });

    const readyTop = hierarchyNode(utils.container, "video:901").style.top;
    const requestCountBeforeCollapse = fetchStub.requests.length;
    fireEvent.click(
      within(hierarchyNode(utils.container, "ip:1")).getByRole("button", {
        name: "收起",
      }),
    );
    assert.equal(
      utils.container.querySelector('[data-hierarchy-node="story:10"]'),
      null,
    );
    assert.match(
      within(hierarchyNode(utils.container, "ip:1")).getByRole("button", {
        name: /^展开 · 已加载 \d+ 项$/,
      }).textContent || "",
      /已加载 7 项/,
    );
    expand(utils.container, "ip:1");
    await expectNode(utils.container, "video:901");
    assert.equal(
      hierarchyNode(utils.container, "video:901").style.top,
      readyTop,
    );
    assert.equal(fetchStub.requests.length, requestCountBeforeCollapse);

    fireEvent.click(utils.getByRole("button", { name: "执行图" }));
    assert.ok(
      utils.container.querySelector(
        '[data-production-canvas="infinite-canvas"]',
      ),
    );
    fireEvent.click(utils.getByRole("button", { name: "业务层级" }));
    assert.ok(hierarchyNode(utils.container, "video:901"));
    assert.ok(
      within(hierarchyNode(utils.container, "ip:1")).getByRole("button", {
        name: "收起",
      }),
    );
    assert.equal(fetchStub.requests.length, requestCountBeforeCollapse);
  });

  it("does not let a pre-refresh branch request repopulate the graph", async () => {
    const fetchStub = installHierarchyFetch({ deferFirstEnvironments: true });
    restoreFetch = fetchStub.restore;
    const utils = render(
      <ProductionCanvasContent
        autosaveDelayMs={null}
        initialView="hierarchy"
        storageKey={null}
      />,
      { container: dom.window.document.body },
    );

    await expectNode(utils.container, "ip:1");
    expand(utils.container, "ip:1");
    await waitFor(() => {
      assert.equal(fetchStub.count(hierarchyPaths.environments), 1);
      assert.equal(fetchStub.count(hierarchyPaths.stories), 1);
    });
    fireEvent.click(utils.getByRole("button", { name: "刷新层级" }));
    await waitFor(() => assert.equal(fetchStub.count(hierarchyPaths.roots), 2));

    await act(async () => {
      fetchStub.resolveDeferredEnvironments();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    assert.equal(
      utils.container.querySelector('[data-hierarchy-node="environment:8"]'),
      null,
    );
    assert.equal(
      utils.container.querySelector('[data-hierarchy-node="story:10"]'),
      null,
    );
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
