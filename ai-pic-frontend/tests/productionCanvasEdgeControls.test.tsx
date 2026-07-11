import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasEdgeControls } from "../src/components/features/canvas/ProductionCanvasEdgeControls";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "../src/components/features/canvas/productionCanvasModel";

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

const node = (
  id: string,
  label: string,
  patch: Partial<ProductionCanvasNode> = {},
): ProductionCanvasNode => ({
  id,
  label,
  title: label,
  status: "review",
  x: 0,
  y: 0,
  width: 220,
  ...patch,
});

function optionLabels(select: HTMLElement) {
  return [...select.querySelectorAll("option")].map(
    (option) => option.textContent,
  );
}

describe("ProductionCanvasEdgeControls", () => {
  afterEach(() => cleanup());

  it("filters connected and task evidence targets, then resets stale selection", () => {
    const source = node("source", "Source");
    const script = node("script", "Script");
    const report = node("report", "Report");
    const task = node("task-77", "Task #77", {
      kind: "note",
      outputs: { task_id: 77 },
    });
    const edges: ProductionCanvasEdge[] = [{ from: "source", to: "script" }];

    const utils = render(
      <ProductionCanvasEdgeControls
        edges={edges}
        node={source}
        nodes={[source, script, report, task]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    const select = utils.getByLabelText("连线目标") as HTMLSelectElement;
    assert.deepEqual(optionLabels(select), [
      "选择兼容端口",
      "输出 → Report· 输入",
    ]);
    const reportBinding = select.options[1]?.value;
    fireEvent.change(select, { target: { value: reportBinding } });
    assert.equal(select.value, reportBinding);

    utils.rerender(
      <ProductionCanvasEdgeControls
        edges={edges}
        node={script}
        nodes={[source, script, report, task]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
    );

    assert.equal(
      (utils.getByLabelText("连线目标") as HTMLSelectElement).value,
      "",
    );
  });

  it("disables the picker when all targets are already connected", () => {
    const source = node("source", "Source");
    const target = node("target", "Target");
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[{ from: "source", to: "target" }]}
        node={source}
        nodes={[source, target]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    const select = utils.getByLabelText("连线目标") as HTMLSelectElement;
    assert.equal(select.disabled, true);
    assert.equal(select.options[0]?.textContent, "没有兼容端口");
    assert.equal(
      utils.getByRole("button", { name: "添加连线" }).hasAttribute("disabled"),
      true,
    );
  });

  it("shows an empty state when the selected node has no outgoing edges", () => {
    const source = node("source", "Source");
    const target = node("target", "Target");
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[]}
        node={source}
        nodes={[source, target]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("暂无连线"));
    assert.equal(utils.queryByRole("button", { name: /移除连线/ }), null);
  });

  it("disambiguates duplicate target and outgoing labels", () => {
    const source = node("source", "Source");
    const pipelineImage = node("pipeline-image", "Image Candidates", {
      title: "角色、环境和关键帧候选",
    });
    const skillImage = node("skill-image", "Image Candidates", {
      title: "Create or reuse storyboard/keyframe image candidates.",
    });
    const video = node("video", "Video Candidates");

    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[]}
        node={source}
        nodes={[source, pipelineImage, skillImage, video]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.deepEqual(optionLabels(utils.getByLabelText("连线目标")), [
      "选择兼容端口",
      "输出 → Image Candidates · 角色、环境和关键帧候选· 输入",
      "输出 → Image Candidates · Create or reuse storyboard/keyframe image candidates.· 输入",
      "输出 → Video Candidates· 输入",
    ]);

    utils.rerender(
      <ProductionCanvasEdgeControls
        edges={[
          { from: "source", to: "pipeline-image" },
          { from: "source", to: "skill-image" },
        ]}
        node={source}
        nodes={[source, pipelineImage, skillImage]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
    );

    assert.ok(
      utils.getByRole("button", {
        name: "移除 默认 → Image Candidates · 角色、环境和关键帧候选· 默认",
      }),
    );
    assert.ok(
      utils.getByRole("button", {
        name: "移除 默认 → Image Candidates · Create or reuse storyboard/keyframe image candidates.· 默认",
      }),
    );
  });

  it("hides edge controls for task evidence nodes", () => {
    const task = node("task-77", "Task #77", {
      kind: "note",
      outputs: { task_id: 77 },
    });
    const utils = render(
      <ProductionCanvasEdgeControls
        edges={[]}
        node={task}
        nodes={[task, node("target", "Target")]}
        onAddEdge={() => {}}
        onRemoveEdge={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.queryByText("连线编辑"), null);
  });
});
