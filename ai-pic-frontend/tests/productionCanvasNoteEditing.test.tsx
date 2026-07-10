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
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvas manual note editing", () => {
  afterEach(() => cleanup());

  it("updates a manual note title and detail from the side tools", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "手工风险确认" },
    });
    fireEvent.input(utils.getByLabelText("便签内容"), {
      target: { value: "需要人工确认付款镜头。" },
    });

    assert.ok(utils.getByLabelText("便签 手工风险确认"));
    assert.equal(utils.getAllByText("手工风险确认").length, 2);
    assert.equal(utils.getAllByText("需要人工确认付款镜头。").length, 2);
  });

  it("shows a stable placeholder while preserving a blank title value", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "   " },
    });

    assert.ok(utils.getByLabelText("便签 未命名便签"));
    assert.ok(utils.getAllByText("未命名便签").length >= 2);
    assert.equal(
      (utils.getByLabelText("便签标题") as HTMLInputElement).value,
      "   ",
    );
  });

  it("does not show manual note fields for production nodes", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    assert.equal(utils.queryByLabelText("便签标题"), null);
    fireEvent.click(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );
    assert.equal(utils.queryByLabelText("便签内容"), null);
  });
});
