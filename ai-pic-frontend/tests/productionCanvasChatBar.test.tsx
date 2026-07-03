import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasChatBar } from "../src/components/features/canvas/ProductionCanvasChatBar";
import { emptyProductionCanvasContext } from "../src/components/features/canvas/productionCanvasContext";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvasChatBar", () => {
  afterEach(() => cleanup());

  it("announces canvas creation errors", () => {
    const utils = render(
      <ProductionCanvasChatBar
        context={emptyProductionCanvasContext}
        error="整体创建失败"
        onCreate={() => {}}
        onContextChange={() => {}}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running={false}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getByRole("alert").textContent, "整体创建失败");
  });

  it("marks whole-canvas creation busy", () => {
    const utils = render(
      <ProductionCanvasChatBar
        context={emptyProductionCanvasContext}
        onCreate={() => {}}
        onContextChange={() => {}}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running
      />,
      { container: dom.window.document.body },
    );

    const button = utils.getByRole("button", { name: "执行中" });
    assert.equal(button.getAttribute("aria-busy"), "true");
    assert.equal(button.hasAttribute("disabled"), true);
  });

  it("keeps context id inputs numeric", () => {
    const changes: Array<[string, string]> = [];
    const utils = render(
      <ProductionCanvasChatBar
        context={emptyProductionCanvasContext}
        onCreate={() => {}}
        onContextChange={(key, value) => changes.push([key, value])}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running={false}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.input(utils.getByLabelText("剧集 ID"), {
      target: { value: "12a-3" },
    });

    assert.deepEqual(changes, [["episode_id", "123"]]);
  });
});
