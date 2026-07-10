import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

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
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("production canvas keyboard navigation", () => {
  afterEach(() => cleanup());

  it("moves selected nodes and pans the empty selection", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.getByRole("region", {
      name: "短剧生产链路无限画布",
    });
    const script = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );
    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );

    assert.ok(script);
    assert.ok(world);
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    assert.equal(dom.window.document.activeElement, canvas);

    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(script.style.left, "286px");
    fireEvent.keyDown(canvas, { key: "ArrowRight", shiftKey: true });
    assert.equal(script.style.left, "350px");
    fireEvent.keyDown(canvas, { key: "ArrowRight", metaKey: true });
    assert.equal(script.style.left, "350px");

    fireEvent.keyDown(canvas, { key: "Escape" });
    assert.doesNotMatch(script.className, /ring-2/);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    fireEvent.keyDown(canvas, { key: "ArrowDown", shiftKey: true });
    assert.equal(
      world.style.transform,
      "translate(16px, 64px) scale(1) translate(0px, 0px)",
    );
  });
});
