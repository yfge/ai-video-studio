import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";

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

const storageKey = "canvas-fit-world-bounds-test";

describe("production canvas fit", () => {
  afterEach(() => {
    cleanup();
    localStorage.removeItem(storageKey);
  });

  it("fits nodes across negative and positive world coordinates", () => {
    const state = createProductionCanvasState();
    state.nodes = state.nodes.map((node) => {
      if (node.id === "brief") return { ...node, x: -50 };
      return node;
    });
    localStorage.setItem(storageKey, JSON.stringify(state));

    const utils = render(<ProductionCanvasContent storageKey={storageKey} />, {
      container: dom.window.document.body,
    });
    fireEvent.click(utils.getByRole("button", { name: "适配" }));

    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );
    const brief = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='brief']",
    );
    const edge = utils.container.querySelector<SVGPathElement>(
      "[data-canvas-edge='brief-script']",
    );
    assert.equal(
      world?.style.transform,
      "translate(64px, 24px) scale(0.79) translate(-50px, 0px)",
    );
    assert.equal(brief?.style.left, "0px");
    assert.equal(
      edge?.getAttribute("d"),
      "M 170 171 C 245 171 245 107 320 107",
    );
  });
});
