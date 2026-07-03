import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasRunControls } from "../src/components/features/canvas/ProductionCanvasRunControls";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

describe("ProductionCanvasRunControls", () => {
  afterEach(() => cleanup());

  it("marks run save and restore controls busy", () => {
    const utils = render(
      <ProductionCanvasRunControls
        busy
        onRestore={() => {}}
        onRunIdChange={() => {}}
        onSave={() => {}}
        runId="canvas-run-1"
      />,
      { container: dom.window.document.body },
    );

    assert.equal(
      utils.getByRole("button", { name: "保存画布" }).getAttribute("aria-busy"),
      "true",
    );
    assert.equal(
      utils.getByRole("button", { name: "恢复画布" }).getAttribute("aria-busy"),
      "true",
    );
    assert.equal(utils.getByLabelText("Run ID").hasAttribute("disabled"), true);
  });
});
