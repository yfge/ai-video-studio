import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasRunControls } from "../src/components/features/canvas/ProductionCanvasRunControls";

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

describe("ProductionCanvasRunControls", () => {
  afterEach(() => cleanup());

  it("clears stale copy status when the run id changes", async () => {
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText: async () => {} },
      configurable: true,
    });
    const controls = (runId: string) => (
      <ProductionCanvasRunControls
        busy={false}
        onRestore={() => {}}
        onRunIdChange={() => {}}
        onSave={() => {}}
        runId={runId}
      />
    );
    const utils = render(controls("canvas-run-1"), {
      container: dom.window.document.body,
    });

    fireEvent.click(utils.getByRole("button", { name: "复制 Run ID" }));
    await waitFor(() =>
      assert.equal(utils.getByRole("status").textContent, "已复制 Run ID"),
    );
    utils.rerender(controls("canvas-run-2"));

    await waitFor(() => assert.equal(utils.queryByText("已复制 Run ID"), null));
  });

  it("uses one live status when run and copy status are both visible", async () => {
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText: async () => {} },
      configurable: true,
    });
    const utils = render(
      <ProductionCanvasRunControls
        busy={false}
        onRestore={() => {}}
        onRunIdChange={() => {}}
        onSave={() => {}}
        runId="canvas-run-1"
        status="已恢复"
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "复制 Run ID" }));

    await waitFor(() => {
      const statuses = utils.getAllByRole("status");
      assert.equal(statuses.length, 1);
      assert.equal(statuses[0]?.textContent, "已恢复 · 已复制 Run ID");
    });
  });

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
