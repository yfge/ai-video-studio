import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { createRef } from "react";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasSurface } from "../src/components/features/canvas/ProductionCanvasSurface";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import { createProductionCanvasState } from "../src/components/features/canvas/productionCanvasState";
import { getWorldBounds } from "../src/components/features/canvas/productionCanvasViewModel";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).Element = dom.window.Element;
(globalThis as any).SVGElement = dom.window.SVGElement;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const source: ProductionCanvasNode = {
  id: "source",
  label: "Source",
  title: "Source",
  status: "ready",
  x: 20,
  y: 20,
  width: 180,
  outputPorts: [{ id: "image", label: "图片", type: "image" }],
};
const target: ProductionCanvasNode = {
  id: "target",
  label: "Target",
  title: "Target",
  status: "draft",
  x: 300,
  y: 20,
  width: 180,
  inputPorts: [{ id: "start_frame", label: "起始帧", type: "image" }],
};

function renderSurface(onAddEdge: (edge: any) => void, onFocusNode = () => {}) {
  const state = createProductionCanvasState([source, target], []);
  const noop = () => {};
  const utils = render(
    <ProductionCanvasSurface
      canvasRef={createRef<HTMLDivElement>()}
      canvasState={state}
      worldBounds={getWorldBounds(state.nodes)}
      onAddEdge={onAddEdge}
      onCanvasDoubleClick={noop}
      onCanvasKeyDown={noop}
      onCanvasPointerDown={noop}
      onCanvasPointerMove={noop}
      onCanvasPointerUp={noop}
      onExecuteNode={noop}
      onFocusNode={onFocusNode}
      onNavigate={noop}
      onNodePointerDown={noop}
      onSelectNode={noop}
    />,
    { container: dom.window.document.body },
  );
  Object.assign(utils.getByRole("region", { name: "短剧生产链路无限画布" }), {
    getBoundingClientRect: () => ({
      bottom: 560,
      height: 560,
      left: 0,
      right: 800,
      top: 0,
      width: 800,
    }),
  });
  return utils;
}

describe("ProductionCanvas port connections", () => {
  afterEach(() => cleanup());

  it("connects compatible ports by direct drag", () => {
    let added: any;
    const utils = renderSurface((edge) => {
      added = edge;
    });
    const output = utils.getByLabelText("输出端口 图片 image");
    const input = utils.getByLabelText("输入端口 起始帧 image");

    fireEvent.pointerDown(output, { pointerId: 1, clientX: 200, clientY: 40 });
    assert.ok(utils.container.querySelector("[data-canvas-connection-draft]"));
    fireEvent.pointerUp(input, { pointerId: 1, clientX: 300, clientY: 40 });

    assert.equal(added?.fromPort, "image");
    assert.equal(added?.toPort, "start_frame");
  });

  it("discovers compatible nodes after dropping on blank canvas", () => {
    let added: any;
    let focused = "";
    const utils = renderSurface(
      (edge) => {
        added = edge;
      },
      (nodeId) => {
        focused = nodeId || "";
      },
    );
    const output = utils.getByLabelText("输出端口 图片 image");
    const canvas = utils.getByRole("region", {
      name: "短剧生产链路无限画布",
    });

    fireEvent.pointerDown(output, { pointerId: 2, clientX: 200, clientY: 40 });
    fireEvent.pointerUp(canvas, { pointerId: 2, clientX: 240, clientY: 160 });
    assert.ok(utils.getByRole("dialog", { name: "选择兼容节点" }));
    fireEvent.click(
      utils.getByRole("button", { name: "Target · start_frame" }),
    );

    assert.equal(added?.to, "target");
    assert.equal(focused, "target");
  });
});
