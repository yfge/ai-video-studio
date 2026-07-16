import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
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

describe("ProductionCanvasBoard interactions", () => {
  afterEach(() => cleanup());

  it("selects a node and exposes its details in the inspector", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));

    assert.ok(utils.getByText("节点详情"));
    assert.ok(utils.getAllByText("Script").length >= 1);
    assert.ok(utils.getAllByText("短剧节拍、对白和质量门禁").length >= 1);
    assert.equal(
      utils.getByRole("button", { name: "定位选中" }).hasAttribute("disabled"),
      false,
    );
    assert.equal(
      utils.container
        .querySelector("[data-canvas-node='script']")
        ?.getAttribute("aria-current"),
      "true",
    );
    assert.equal(
      utils
        .getByLabelText("Script 短剧节拍、对白和质量门禁")
        .getAttribute("aria-pressed"),
      "true",
    );
    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "Escape" });
    assert.equal(
      utils.container
        .querySelector("[data-canvas-node='script']")
        ?.hasAttribute("aria-current"),
      false,
    );
    assert.equal(
      utils
        .getByLabelText("Script 短剧节拍、对白和质量门禁")
        .getAttribute("aria-pressed"),
      "false",
    );
    assert.equal(
      utils.getByRole("button", { name: "定位选中" }).hasAttribute("disabled"),
      true,
    );
    assert.equal(utils.queryByText("节点详情"), null);
  });

  it("searches and filters nodes without changing the graph definition", async () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const originalNodeCount =
      utils.container.querySelectorAll("[data-canvas-node]").length;

    fireEvent.change(utils.getByLabelText("节点状态"), {
      target: { value: "生成中" },
    });
    assert.equal(
      utils.container.querySelectorAll("[data-canvas-node]").length,
      1,
    );
    assert.ok(utils.container.querySelector("[data-canvas-node='video']"));

    fireEvent.click(utils.getByRole("button", { name: "清除筛选" }));
    await waitFor(() =>
      assert.equal(
        utils.container.querySelectorAll("[data-canvas-node]").length,
        originalNodeCount,
      ),
    );
    fireEvent.input(utils.getByLabelText("节点搜索"), {
      target: { value: "镜头顺序" },
    });
    await waitFor(() =>
      assert.equal(
        utils.container.querySelectorAll("[data-canvas-node]").length,
        1,
      ),
    );
    fireEvent.click(utils.getByRole("button", { name: "定位首项" }));
    assert.equal(
      utils.container
        .querySelector("[data-canvas-node='timeline']")
        ?.getAttribute("aria-current"),
      "true",
    );

    fireEvent.click(utils.getByRole("button", { name: "清除筛选" }));
    await waitFor(() =>
      assert.equal(
        utils.container.querySelectorAll("[data-canvas-node]").length,
        originalNodeCount,
      ),
    );
  });

  it("pans the canvas with horizontal wheel gestures", () => {
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
    fireEvent.wheel(canvas, { deltaX: 40, deltaY: 5 });
    assert.equal(
      world.style.transform,
      "translate(-40px, -5px) scale(1) translate(0px, 0px)",
    );
    fireEvent.wheel(canvas, { deltaY: 20, shiftKey: true });
    assert.equal(
      world.style.transform,
      "translate(-60px, -5px) scale(1) translate(0px, 0px)",
    );
  });

  it("pans from a node with the middle mouse button", () => {
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
    Object.assign(canvas, {
      hasPointerCapture: () => true,
      releasePointerCapture: () => undefined,
      setPointerCapture: () => undefined,
    });
    utils.getByLabelText("Script 短剧节拍、对白和质量门禁").click();
    fireEvent.pointerDown(
      utils.getByLabelText("Script 短剧节拍、对白和质量门禁"),
      {
        button: 1,
        clientX: 200,
        clientY: 200,
        pointerId: 1,
      },
    );
    fireEvent.pointerMove(canvas, { clientX: 240, clientY: 230, pointerId: 1 });
    fireEvent.pointerUp(canvas, { pointerId: 1 });

    assert.equal(
      world.style.transform,
      "translate(40px, 30px) scale(1) translate(0px, 0px)",
    );
    assert.ok(utils.getAllByText("短剧节拍、对白和质量门禁").length);
  });

  it("pans from a node with alt drag", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );

    assert.ok(canvas);
    assert.ok(world);
    assert.ok(scriptNode);
    Object.assign(canvas, {
      hasPointerCapture: () => true,
      releasePointerCapture: () => undefined,
      setPointerCapture: () => undefined,
    });
    utils.getByLabelText("Script 短剧节拍、对白和质量门禁").click();
    fireEvent.pointerDown(
      utils.getByLabelText("Script 短剧节拍、对白和质量门禁"),
      {
        altKey: true,
        button: 0,
        clientX: 200,
        clientY: 200,
        pointerId: 1,
      },
    );
    fireEvent.pointerMove(canvas, { clientX: 232, clientY: 218, pointerId: 1 });
    fireEvent.pointerUp(canvas, { pointerId: 1 });

    assert.equal(
      world.style.transform,
      "translate(32px, 18px) scale(1) translate(0px, 0px)",
    );
    assert.equal(scriptNode.style.left, "270px");
    assert.ok(utils.getAllByText("短剧节拍、对白和质量门禁").length);
  });
});
