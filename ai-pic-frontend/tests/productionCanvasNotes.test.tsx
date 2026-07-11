import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { ProductionCanvasNoteControls } from "../src/components/features/canvas/ProductionCanvasNoteControls";
import { notePositionFromCanvasDoubleClick } from "../src/components/features/canvas/productionCanvasDoubleClick";
import { isManualProductionCanvasNote } from "../src/components/features/canvas/productionCanvasSkillNodes";

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

describe("ProductionCanvasNotes", () => {
  afterEach(() => cleanup());

  it("places a manual note at the double-clicked canvas location", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector(
      "[data-production-canvas='infinite-canvas']",
    );
    assert.ok(canvas);
    Object.defineProperty(canvas, "getBoundingClientRect", {
      configurable: true,
      value: () => ({
        bottom: 440,
        height: 420,
        left: 10,
        right: 730,
        top: 20,
        width: 720,
        x: 10,
        y: 20,
      }),
    });

    fireEvent.doubleClick(canvas, { clientX: 260, clientY: 300 });

    const note = utils.getByLabelText("便签 记录这个项目下一步的人工判断");
    assert.equal(note.parentElement?.style.left, "155px");
    assert.equal(note.parentElement?.style.top, "232px");
  });

  it("keeps double-click note positions finite when viewport zoom is invalid", () => {
    const position = notePositionFromCanvasDoubleClick(
      {
        clientX: 260,
        clientY: 300,
        currentTarget: {
          getBoundingClientRect: () => ({
            bottom: 440,
            height: 420,
            left: 10,
            right: 730,
            top: 20,
            width: 720,
            x: 10,
            y: 20,
          }),
        },
      } as unknown as Parameters<typeof notePositionFromCanvasDoubleClick>[0],
      { x: 0, y: 0, zoom: 0 },
    );

    assert.deepEqual(position, { x: 405, y: 512 });
  });

  it("edits manual note text from the side tools", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const briefNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='brief']",
    );

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "手工风险确认" },
    });
    fireEvent.input(utils.getByLabelText("便签内容"), {
      target: { value: "需要人工确认付款镜头。" },
    });

    assert.ok(utils.getByLabelText("便签 手工风险确认"));
    assert.equal(utils.getAllByText("需要人工确认付款镜头。").length, 2);

    const deleteButton = utils.getByRole("button", { name: "删除便签" });
    deleteButton.focus();
    fireEvent.click(deleteButton);
    assert.equal(utils.queryByLabelText("便签 手工风险确认"), null);
    assert.equal(dom.window.document.activeElement, canvas);
    assert.ok(briefNode);
    fireEvent.keyDown(canvas!, { key: "ArrowRight" });
    assert.equal(briefNode.style.left, "56px");
    assert.ok(utils.getAllByText("IP、受众、题材和单集目标").length >= 1);
  });

  it("keeps a blank manual note named on the canvas", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "   " },
    });

    const note = utils.getByLabelText("便签 未命名便签");
    assert.ok(note);
    assert.ok(utils.getAllByText("未命名便签").length >= 1);
    assert.equal(
      (utils.getByLabelText("便签标题") as HTMLInputElement).value,
      "   ",
    );
  });

  it("duplicates the selected manual note with its text", () => {
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

  it("duplicates the selected manual note from the canvas keyboard", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "快捷复制" },
    });

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "d", ctrlKey: true });

    const notes = utils.getAllByLabelText("便签 快捷复制");
    assert.equal(notes.length, 2);
    assert.equal(notes[1].parentElement?.style.left, "289px");
    assert.equal(notes[1].parentElement?.style.top, "186px");
  });

  it("deletes the selected manual note from the canvas keyboard", async () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    fireEvent.input(utils.getByLabelText("便签标题"), {
      target: { value: "键盘删除便签" },
    });
    assert.ok(utils.getByLabelText("便签 键盘删除便签"));

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "Delete" });

    await waitFor(() =>
      assert.equal(utils.queryByLabelText("便签 键盘删除便签"), null),
    );
    assert.ok(utils.getAllByText("IP、受众、题材和单集目标").length >= 1);
  });

  it("keeps task evidence notes out of the manual note editor", () => {
    const taskNote = {
      id: "task-note",
      label: "Task #77",
      title: "任务证据",
      status: "review" as const,
      x: 0,
      y: 0,
      width: 220,
      kind: "note" as const,
      outputs: { task_id: 77 },
    };
    const utils = render(
      <ProductionCanvasNoteControls
        node={taskNote}
        onDuplicateNote={() => {}}
        onRemoveNode={() => {}}
        onUpdateNode={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(isManualProductionCanvasNote(taskNote), false);
    assert.equal(utils.queryByLabelText("便签标题"), null);
  });
});
