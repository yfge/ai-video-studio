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

  it("falls back when copying a canvas restore link with the current run id", async () => {
    let copiedText = "";
    const originalExecCommand = dom.window.document.execCommand;
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: {
        writeText: async () => {
          throw new Error("clipboard blocked");
        },
      },
      configurable: true,
    });
    Object.defineProperty(dom.window.document, "execCommand", {
      value: (command: string) => {
        copiedText = dom.window.document.querySelector("textarea")?.value || "";
        return command === "copy";
      },
      configurable: true,
    });
    try {
      const utils = render(
        <ProductionCanvasRunControls
          busy={false}
          onRestore={() => {}}
          onRunIdChange={() => {}}
          onSave={() => {}}
          runId="canvas-run-1"
        />,
        { container: dom.window.document.body },
      );

      fireEvent.click(utils.getByRole("button", { name: "复制链接" }));

      await waitFor(() => {
        assert.equal(copiedText, "http://localhost/canvas?run_id=canvas-run-1");
        assert.equal(utils.getByRole("status").textContent, "已复制链接");
      });
    } finally {
      Object.defineProperty(dom.window.document, "execCommand", {
        value: originalExecCommand,
        configurable: true,
      });
    }
  });

  it("shows the restore link when copy primitives are unavailable", async () => {
    const originalClipboard = globalThis.navigator.clipboard;
    const originalExecCommand = dom.window.document.execCommand;
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: undefined,
      configurable: true,
    });
    Object.defineProperty(dom.window.document, "execCommand", {
      value: undefined,
      configurable: true,
    });
    try {
      const utils = render(
        <ProductionCanvasRunControls
          busy={false}
          onRestore={() => {}}
          onRunIdChange={() => {}}
          onSave={() => {}}
          runId="canvas-run-1"
        />,
        { container: dom.window.document.body },
      );

      fireEvent.click(utils.getByRole("button", { name: "复制链接" }));

      await waitFor(() => {
        assert.equal(
          utils.getByRole("status").textContent,
          "复制失败，链接已生成：http://localhost/canvas?run_id=canvas-run-1",
        );
      });
    } finally {
      Object.defineProperty(globalThis.navigator, "clipboard", {
        value: originalClipboard,
        configurable: true,
      });
      Object.defineProperty(dom.window.document, "execCommand", {
        value: originalExecCommand,
        configurable: true,
      });
    }
  });

  it("returns focus after a copy attempt", async () => {
    const container = dom.window.document.createElement("div");
    dom.window.document.body.appendChild(container);
    const canvas = dom.window.document.createElement("div");
    canvas.dataset.productionCanvas = "infinite-canvas";
    canvas.tabIndex = -1;
    dom.window.document.body.appendChild(canvas);
    const originalClipboard = globalThis.navigator.clipboard;
    const originalExecCommand = dom.window.document.execCommand;
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: undefined,
      configurable: true,
    });
    Object.defineProperty(dom.window.document, "execCommand", {
      value: undefined,
      configurable: true,
    });
    try {
      const utils = render(
        <ProductionCanvasRunControls
          busy={false}
          onRestore={() => {}}
          onRunIdChange={() => {}}
          onSave={() => {}}
          runId="canvas-run-1"
        />,
        { container },
      );

      fireEvent.click(utils.getByRole("button", { name: "复制 Run ID" }));

      await waitFor(() =>
        assert.equal(dom.window.document.activeElement, canvas),
      );
    } finally {
      canvas.remove();
      container.remove();
      Object.defineProperty(globalThis.navigator, "clipboard", {
        value: originalClipboard,
        configurable: true,
      });
      Object.defineProperty(dom.window.document, "execCommand", {
        value: originalExecCommand,
        configurable: true,
      });
    }
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
