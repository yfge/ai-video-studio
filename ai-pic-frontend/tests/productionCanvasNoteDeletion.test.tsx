import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { removeManualProductionCanvasNote } from "../src/components/features/canvas/productionCanvasNoteActions";
import {
  addProductionCanvasNote,
  createProductionCanvasState,
} from "../src/components/features/canvas/productionCanvasState";

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

describe("ProductionCanvas manual note deletion", () => {
  afterEach(() => cleanup());

  it("deletes a note from the side tools and returns focus", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const brief = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='brief']",
    );

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.click(utils.getByRole("button", { name: "删除便签" }));

    assert.equal(utils.queryByLabelText("便签标题"), null);
    assert.equal(
      utils.container.querySelectorAll("[data-canvas-node^='note-']").length,
      0,
    );
    assert.equal(dom.window.document.activeElement, canvas);
    assert.ok(canvas);
    assert.ok(brief);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(brief.style.left, "56px");
  });

  it("deletes selected notes with Delete and Backspace", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    assert.equal(fireEvent.keyDown(canvas, { key: "Delete" }), false);
    assert.equal(utils.queryByLabelText("便签标题"), null);

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    assert.equal(fireEvent.keyDown(canvas, { key: "Backspace" }), false);
    assert.equal(
      utils.container.querySelectorAll("[data-canvas-node^='note-']").length,
      0,
    );
  });

  it("preserves production nodes, task evidence, and connected graph state", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    assert.equal(fireEvent.keyDown(canvas, { key: "Delete" }), true);
    assert.equal(fireEvent.keyDown(canvas, { key: "Backspace" }), true);
    assert.ok(utils.getByLabelText("Brief IP、受众、题材和单集目标"));

    const state = createProductionCanvasState();
    const taskNote = {
      id: "task-note-77",
      label: "Task #77",
      title: "任务证据",
      status: "review" as const,
      x: 0,
      y: 0,
      width: 220,
      kind: "note" as const,
      outputs: { task_id: 77 },
    };
    const withTaskNote = {
      ...state,
      nodes: [...state.nodes, taskNote],
      selectedNodeId: taskNote.id,
    };
    assert.equal(
      removeManualProductionCanvasNote(withTaskNote, taskNote.id),
      withTaskNote,
    );

    const nodes = addProductionCanvasNote(state.nodes, 1);
    const withManualNote = {
      ...state,
      nodes,
      edges: [...state.edges, { from: "brief", to: "note-1" }],
      selectedNodeId: "note-1",
    };
    const removed = removeManualProductionCanvasNote(withManualNote, "note-1");
    assert.equal(
      removed.nodes.some((node) => node.id === "note-1"),
      false,
    );
    assert.equal(
      removed.edges.some((edge) => edge.to === "note-1"),
      false,
    );
    assert.equal(removed.selectedNodeId, "brief");
  });
});
