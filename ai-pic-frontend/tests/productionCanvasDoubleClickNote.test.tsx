import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { notePositionFromCanvasDoubleClick } from "../src/components/features/canvas/productionCanvasDoubleClick";

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

const canvasRect = {
  bottom: 440,
  height: 420,
  left: 10,
  right: 730,
  top: 20,
  width: 720,
  x: 10,
  y: 20,
};

describe("ProductionCanvas blank double-click notes", () => {
  afterEach(() => cleanup());

  it("centers a new note at the double-clicked canvas location", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    Object.defineProperty(canvas, "getBoundingClientRect", {
      configurable: true,
      value: () => canvasRect,
    });
    fireEvent.doubleClick(canvas, { clientX: 260, clientY: 300 });

    const note = utils.getByLabelText("便签 记录这个项目下一步的人工判断");
    assert.equal(note.parentElement?.style.left, "155px");
    assert.equal(note.parentElement?.style.top, "232px");
    assert.equal(dom.window.document.activeElement, canvas);
  });

  it("accounts for pan and clamps invalid zoom", () => {
    const position = notePositionFromCanvasDoubleClick(
      {
        clientX: 260,
        clientY: 300,
        currentTarget: { getBoundingClientRect: () => canvasRect },
      } as unknown as Parameters<typeof notePositionFromCanvasDoubleClick>[0],
      { x: 40, y: -20, zoom: 2 },
    );

    assert.deepEqual(position, { x: 36.25, y: 139.5 });
  });

  it("keeps toolbar note creation independent from click events", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    const note = utils.getByLabelText("便签 记录这个项目下一步的人工判断");
    assert.equal(note.parentElement?.style.left, "265px");
    assert.equal(note.parentElement?.style.top, "162px");
    assert.equal(dom.window.document.activeElement, canvas);
  });
});
