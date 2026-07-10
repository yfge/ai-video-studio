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

describe("ProductionCanvas keyboard viewport controls", () => {
  afterEach(() => cleanup());

  it("zooms with plus, equals, and minus", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "=" });
    assert.ok(utils.getByText("110%"));
    fireEvent.keyDown(canvas, { key: "+", shiftKey: true });
    assert.ok(utils.getByText("120%"));
    fireEvent.keyDown(canvas, { key: "-" });
    assert.ok(utils.getByText("110%"));
  });

  it("fits all nodes with zero and Home", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );

    assert.ok(canvas);
    assert.ok(world);
    fireEvent.keyDown(canvas, { key: "=" });
    fireEvent.keyDown(canvas, { key: "0" });
    assert.ok(utils.getByText("79%"));

    fireEvent.keyDown(canvas, { key: "=" });
    fireEvent.keyDown(canvas, { key: "Home" });
    assert.equal(
      world.style.transform,
      "translate(24px, 24px) scale(0.79) translate(0px, 0px)",
    );
  });

  it("leaves browser-modified viewport shortcuts untouched", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "=", ctrlKey: true });
    fireEvent.keyDown(canvas, { key: "-", metaKey: true });
    fireEvent.keyDown(canvas, { key: "Home", altKey: true });
    assert.ok(utils.getByText("100%"));
  });
});
