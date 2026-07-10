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

describe("ProductionCanvas node double-click focus", () => {
  afterEach(() => cleanup());

  it("selects and centers a double-clicked node", () => {
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
    fireEvent.doubleClick(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );

    assert.equal(
      world.style.transform,
      "translate(-495px, -43px) scale(1) translate(0px, 0px)",
    );
    assert.equal(dom.window.document.activeElement, canvas);
    assert.ok(utils.getAllByText("Report").length >= 2);
  });

  it("does not add a note when double-clicking a node", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    fireEvent.doubleClick(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );

    assert.equal(
      utils.container.querySelectorAll("[data-canvas-node^='note-']").length,
      0,
    );
  });
});
