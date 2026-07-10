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
(globalThis as any).Event = dom.window.Event;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvas toolbar focus", () => {
  afterEach(() => cleanup());

  it("keeps keyboard control after zoom, fit, and reset commands", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const script = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );
    const brief = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='brief']",
    );

    assert.ok(canvas);
    assert.ok(script);
    assert.ok(brief);
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));

    const zoomButton = utils.getByRole("button", { name: "放大" });
    zoomButton.focus();
    fireEvent.click(zoomButton);
    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(script.style.left, "286px");

    const fitButton = utils.getByRole("button", { name: "适配" });
    fitButton.focus();
    fireEvent.click(fitButton);
    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(script.style.left, "302px");

    const resetButton = utils.getByRole("button", { name: "重置" });
    resetButton.focus();
    fireEvent.click(resetButton);
    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(brief.style.left, "56px");
  });
});
