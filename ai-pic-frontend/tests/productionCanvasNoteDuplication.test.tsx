import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { duplicateManualProductionCanvasNote } from "../src/components/features/canvas/productionCanvasNoteActions";
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
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvas manual note duplication", () => {
  afterEach(() => cleanup());

  it("duplicates note text and dimensions with a visible offset", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "复用检查点" },
    });
    fireEvent.input(utils.getByLabelText("便签内容"), {
      target: { value: "复制后继续记录第二轮判断。" },
    });
    fireEvent.click(utils.getByRole("button", { name: "复制便签" }));

    const notes = utils.getAllByLabelText("便签 复用检查点");
    assert.equal(notes.length, 2);
    assert.equal(notes[1].parentElement?.style.left, "289px");
    assert.equal(notes[1].parentElement?.style.top, "186px");
    assert.equal(
      (utils.getByLabelText("便签内容") as HTMLTextAreaElement).value,
      "复制后继续记录第二轮判断。",
    );
    assert.equal(dom.window.document.activeElement, canvas);
  });

  it("duplicates the selected note with Cmd+D", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    assert.ok(canvas);
    const allowed = fireEvent.keyDown(canvas, { key: "d", metaKey: true });

    assert.equal(allowed, false);
    assert.equal(
      utils.getAllByLabelText("便签 记录这个项目下一步的人工判断").length,
      2,
    );
  });

  it("leaves Cmd+D untouched for production and task evidence nodes", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    assert.equal(fireEvent.keyDown(canvas, { key: "d", metaKey: true }), true);
    assert.equal(
      utils.container.querySelectorAll("[data-canvas-node^='note-']").length,
      0,
    );

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
      duplicateManualProductionCanvasNote(withTaskNote, taskNote.id),
      withTaskNote,
    );
  });
});
