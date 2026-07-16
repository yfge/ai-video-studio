import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { productionNavItems } from "../src/components/shared/operator/OperatorShell";
import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvasBoard", () => {
  afterEach(() => cleanup());

  it("adds the creative canvas as a first-class production navigation entry", () => {
    const canvasIndex = productionNavItems.findIndex(
      (item) => item.href === "/canvas",
    );

    assert.equal(productionNavItems[canvasIndex]?.label, "创作画布");
    assert.equal(productionNavItems[canvasIndex]?.icon, "canvas");
    assert.equal(
      productionNavItems[canvasIndex - 1]?.href,
      "/",
      "canvas entry should sit immediately after the workbench",
    );
  });

  it("renders the short-drama production chain on an interactive canvas", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    assert.ok(utils.getByText("短剧生产链路"));
    assert.ok(
      utils.getByText(
        "Intent Model -> Production Brief -> Content Plan -> Asset Decision -> Script -> Audio + Timeline -> Clip Storyboard -> Video Candidates -> Timeline Place -> Render -> Export -> Report",
      ),
    );

    for (const label of [
      "Brief",
      "Assets",
      "Script",
      "Storyboard Candidates",
      "Video Candidates",
      "Timeline",
      "Timeline Place",
      "Render",
      "Export",
      "Report",
    ]) {
      assert.ok(utils.getAllByText(label).length >= 1);
    }

    const canvas = utils.container.querySelector(
      "[data-production-canvas='infinite-canvas']",
    );
    assert.ok(canvas);
    assert.equal(
      utils.getByRole("region", { name: "短剧生产链路无限画布" }),
      canvas,
    );
    assert.equal(canvas.getAttribute("tabindex"), "0");
    assert.match(canvas.className, /touch-none/);
    assert.ok(
      utils.container.querySelector(
        "[data-canvas-output-port='storyboard:approved_storyboard']",
      ),
    );
    assert.ok(
      utils.container.querySelector(
        "[data-canvas-input-port='video:approved_storyboard']",
      ),
    );
    assert.equal(
      utils.container.querySelector("[data-canvas-input-port$=':start_frame']"),
      null,
    );
    assert.ok(utils.getByRole("button", { name: "添加便签" }));
    assert.ok(utils.getByRole("button", { name: "适配" }));
    for (const label of ["运行详情", "更多生产参数", "节点筛选"]) {
      assert.equal(
        utils.getByLabelText(label).closest("details")?.hasAttribute("open"),
        false,
      );
    }
    for (const label of ["运行就绪节点", "继续运行", "取消运行"]) {
      assert.equal(
        utils.getByRole("button", { name: label }).hasAttribute("disabled"),
        true,
      );
    }
    assert.ok(utils.getByRole("navigation", { name: "画布小地图" }));
    assert.equal(
      utils.getByRole("button", { name: "定位选中" }).hasAttribute("disabled"),
      false,
    );
    assert.ok(utils.getByText("100%"));
  });

  it("undoes and redoes graph definition changes", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const undo = utils.getByRole("button", { name: "撤销图定义变更" });
    const redo = utils.getByRole("button", { name: "重做图定义变更" });
    assert.ok(canvas);
    assert.equal(undo.hasAttribute("disabled"), true);
    assert.equal(redo.hasAttribute("disabled"), true);

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    assert.ok(utils.container.querySelector("[data-canvas-node='note-1']"));
    assert.equal(undo.hasAttribute("disabled"), false);

    fireEvent.click(undo);
    assert.equal(
      utils.container.querySelector("[data-canvas-node='note-1']"),
      null,
    );
    assert.equal(redo.hasAttribute("disabled"), false);

    fireEvent.click(redo);
    assert.ok(utils.container.querySelector("[data-canvas-node='note-1']"));
    fireEvent.keyDown(canvas, { key: "z", metaKey: true });
    assert.equal(
      utils.container.querySelector("[data-canvas-node='note-1']"),
      null,
    );
    fireEvent.keyDown(canvas, { key: "z", metaKey: true, shiftKey: true });
    assert.ok(utils.container.querySelector("[data-canvas-node='note-1']"));
  });

  it("inserts a reusable domain subflow as one undoable definition change", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    fireEvent.change(utils.getByLabelText("领域模板"), {
      target: { value: "shot-review" },
    });
    fireEvent.click(utils.getByRole("button", { name: "插入子流程" }));

    assert.ok(utils.getByRole("region", { name: "镜头评审子流程" }));
    assert.ok(
      utils.container.querySelector(
        "[data-canvas-node='template-shot-review-1-storyboard-candidates']",
      ),
    );
    assert.ok(
      utils.container.querySelector(
        "[data-canvas-node='template-shot-review-1-video-candidates']",
      ),
    );

    fireEvent.click(utils.getByRole("button", { name: "撤销图定义变更" }));
    assert.equal(
      utils.container.querySelector(
        "[data-canvas-node='template-shot-review-1-storyboard-candidates']",
      ),
      null,
    );
  });

  it("navigates to nodes from the minimap", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );

    assert.ok(world);
    fireEvent.click(utils.getByRole("button", { name: "小地图定位 Timeline" }));
    assert.equal(
      utils.container
        .querySelector("[data-canvas-node='timeline']")
        ?.getAttribute("aria-current"),
      "true",
    );
    assert.notEqual(
      world.style.transform,
      "translate(0px, 0px) scale(1) translate(0px, 0px)",
    );
  });

  it("multi-selects, aligns, and duplicates production nodes", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const brief = utils.getByLabelText("Brief IP、受众、题材和单集目标");
    const script = utils.getByLabelText("Script 短剧节拍、对白和质量门禁");

    fireEvent.click(brief);
    fireEvent.click(script, { shiftKey: true });
    assert.ok(utils.getByText("已选 2 个节点"));
    fireEvent.click(utils.getByRole("button", { name: "左对齐" }));
    assert.equal(
      brief.parentElement?.style.left,
      script.parentElement?.style.left,
    );
    fireEvent.click(utils.getByRole("button", { name: "复制生产节点" }));
    assert.ok(
      utils.container.querySelector("[data-canvas-node='brief-copy-1']"),
    );
    assert.ok(
      utils.container.querySelector("[data-canvas-node='script-copy-1']"),
    );
  });

  it("creates and collapses scene sections from selected nodes", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    fireEvent.click(utils.getByLabelText("Brief IP、受众、题材和单集目标"));
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"), {
      shiftKey: true,
    });
    fireEvent.click(utils.getByRole("button", { name: "创建场景分区" }));
    const section = utils.getByRole("region", { name: "场景分区 1" });
    assert.ok(section);
    fireEvent.click(utils.getByRole("button", { name: "场景分区 1" }));
    assert.equal(
      utils.container.querySelector("[data-canvas-node='brief']"),
      null,
    );
    fireEvent.click(utils.getByRole("button", { name: "场景分区 1" }));
    assert.ok(utils.container.querySelector("[data-canvas-node='brief']"));
  });
});
