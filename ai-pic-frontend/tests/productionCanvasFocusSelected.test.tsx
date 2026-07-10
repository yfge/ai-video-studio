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

describe("ProductionCanvas selected-node focus", () => {
  afterEach(() => cleanup());

  it("centers the viewport on the selected node with F", () => {
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
    fireEvent.click(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );
    fireEvent.keyDown(canvas, { key: "F" });

    assert.equal(
      world.style.transform,
      "translate(-495px, -43px) scale(1) translate(0px, 0px)",
    );
  });

  it("returns keyboard focus after using the toolbar command", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const focusButton = utils.getByRole("button", { name: "定位选中" });

    assert.ok(canvas);
    fireEvent.click(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );
    focusButton.focus();
    fireEvent.click(focusButton);

    assert.equal(dom.window.document.activeElement, canvas);
    assert.equal(
      utils.container.querySelector<HTMLElement>(
        "[data-production-canvas-world='true']",
      )?.style.transform,
      "translate(-495px, -43px) scale(1) translate(0px, 0px)",
    );
  });

  it("disables the command and leaves F untouched without a selection", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );
    const focusButton = utils.getByRole("button", { name: "定位选中" });

    assert.ok(canvas);
    assert.ok(world);
    fireEvent.keyDown(canvas, { key: "Escape" });
    assert.equal(focusButton.hasAttribute("disabled"), true);
    fireEvent.keyDown(canvas, { key: "f" });
    assert.equal(
      world.style.transform,
      "translate(0px, 0px) scale(1) translate(0px, 0px)",
    );
  });
});
