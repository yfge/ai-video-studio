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

describe("ProductionCanvasKeyboard", () => {
  afterEach(() => cleanup());

  it("centers the viewport on the selected node", () => {
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
    fireEvent.keyDown(canvas, { key: "Escape" });
    fireEvent.keyDown(canvas, { key: "F" });
    assert.equal(
      world.style.transform,
      "translate(0px, 0px) scale(1) translate(0px, 0px)",
    );

    fireEvent.click(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );
    fireEvent.keyDown(canvas, { key: "F" });

    assert.equal(
      world.style.transform,
      "translate(-495px, -43px) scale(1) translate(0px, 0px)",
    );
  });

  it("keeps keyboard control after using the focus selected toolbar button", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const world = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas-world='true']",
    );
    const focusButton = utils.getByRole("button", { name: "定位选中" });

    assert.ok(canvas);
    assert.ok(world);
    fireEvent.click(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );
    focusButton.focus();
    fireEvent.click(focusButton);

    assert.equal(
      world.style.transform,
      "translate(-495px, -43px) scale(1) translate(0px, 0px)",
    );
    assert.equal(dom.window.document.activeElement, canvas);
  });

  it("keeps keyboard control after keyboard-activating a node card", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );
    const scriptButton = utils.getByLabelText(
      "Script 短剧节拍、对白和质量门禁",
    );

    assert.ok(canvas);
    assert.ok(scriptNode);
    scriptButton.focus();
    fireEvent.click(scriptButton);

    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(scriptNode.style.left, "286px");
  });

  it("centers the viewport when a node is double clicked", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });

    fireEvent.doubleClick(
      utils.getByLabelText("Report 成本、质量、provider lineage"),
    );

    assert.equal(
      utils.container.querySelector<HTMLElement>(
        "[data-production-canvas-world='true']",
      )?.style.transform,
      "translate(-495px, -43px) scale(1) translate(0px, 0px)",
    );
  });

  it("zooms the canvas with keyboard shortcuts", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "=" });
    assert.ok(utils.getByText("110%"));
    fireEvent.keyDown(canvas, { key: "-" });
    assert.ok(utils.getByText("100%"));
  });

  it("keeps keyboard control after wheel zooming the canvas", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );
    const addButton = utils.getByRole("button", { name: "添加便签" });

    assert.ok(canvas);
    assert.ok(scriptNode);
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    addButton.focus();
    fireEvent.wheel(canvas, { deltaY: -20 });

    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(scriptNode.style.left, "286px");
  });

  it("keeps keyboard control after using the zoom toolbar button", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );
    const zoomInButton = utils.getByRole("button", { name: "放大" });

    assert.ok(canvas);
    assert.ok(scriptNode);
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    zoomInButton.focus();
    fireEvent.click(zoomInButton);

    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(scriptNode.style.left, "286px");
  });

  it("fits the canvas with the keyboard reset shortcut", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "=" });
    fireEvent.keyDown(canvas, { key: "0" });
    assert.ok(utils.getByText("79%"));
    fireEvent.keyDown(canvas, { key: "=" });
    fireEvent.keyDown(canvas, { key: "Home" });
    assert.equal(
      utils.container.querySelector<HTMLElement>(
        "[data-production-canvas-world='true']",
      )?.style.transform,
      "translate(24px, 24px) scale(0.79) translate(0px, 0px)",
    );
  });

  it("keeps keyboard control after using the fit toolbar button", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );
    const fitButton = utils.getByRole("button", { name: "适配" });

    assert.ok(canvas);
    assert.ok(scriptNode);
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    fitButton.focus();
    fireEvent.click(fitButton);

    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(scriptNode.style.left, "286px");
  });

  it("keeps keyboard control after using the reset toolbar button", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const briefNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='brief']",
    );
    const resetButton = utils.getByRole("button", { name: "重置" });

    assert.ok(canvas);
    assert.ok(briefNode);
    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    resetButton.focus();
    fireEvent.click(resetButton);

    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(briefNode.style.left, "56px");
  });

  it("resets the canvas and run id with the keyboard", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/plan")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-keyboard-reset",
              task_id: 91,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      window.history.replaceState(null, "", "/canvas");
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const scriptNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='script']",
      );

      assert.ok(canvas);
      assert.ok(scriptNode);
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "键盘重置画布" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));
      await waitFor(() =>
        assert.equal(
          window.location.href,
          "http://localhost/canvas?run_id=canvas-run-keyboard-reset",
        ),
      );
      fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(scriptNode.style.left, "286px");

      fireEvent.keyDown(canvas, { key: "r" });

      assert.equal(
        (utils.getByLabelText("Run ID") as HTMLInputElement).value,
        "",
      );
      assert.equal(window.location.href, "http://localhost/canvas");
      assert.equal(scriptNode.style.left, "270px");
      assert.equal(dom.window.document.activeElement, canvas);
    } finally {
      globalThis.fetch = originalFetch;
      window.history.replaceState(null, "", "/");
    }
  });

  it("keeps keyboard control after saving the canvas from the toolbar", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/canvas-run-focus/state")) {
        assert.ok(init?.body);
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-focus",
              task_id: 77,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: JSON.parse(String(init.body)),
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      const utils = render(<ProductionCanvasContent storageKey={null} />, {
        container: dom.window.document.body,
      });
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const scriptNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='script']",
      );
      const runIdInput = utils.getByLabelText("Run ID") as HTMLInputElement;
      const saveButton = utils.getByRole("button", { name: "保存画布" });

      assert.ok(canvas);
      assert.ok(scriptNode);
      fireEvent.change(runIdInput, { target: { value: "canvas-run-focus" } });
      fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
      saveButton.focus();
      fireEvent.click(saveButton);

      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(scriptNode.style.left, "286px");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("keeps keyboard control after restoring the canvas from the toolbar", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/canvas-run-restore-focus")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "canvas-run-restore-focus",
              task_id: 88,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
              saved_state: {
                nodes: [
                  {
                    id: "skill-brief",
                    label: "Brief",
                    title: "恢复后的 brief",
                    status: "ready",
                    x: 80,
                    y: 360,
                    width: 210,
                    kind: "skill_result",
                    skill: "brief.compose",
                  },
                ],
                edges: [],
                viewport: { x: 0, y: 0, zoom: 1 },
                selected_node_id: "skill-brief",
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      throw new Error(`Unexpected request ${url}`);
    };

    try {
      const utils = render(
        <ProductionCanvasContent
          autosaveDelayMs={null}
          initialRunId="canvas-run-restore-focus"
          storageKey={null}
        />,
        { container: dom.window.document.body },
      );
      const canvas = utils.container.querySelector<HTMLElement>(
        "[data-production-canvas='infinite-canvas']",
      );
      const restoreButton = utils.getByRole("button", { name: "恢复画布" });

      assert.ok(canvas);
      await waitFor(() =>
        assert.ok(utils.getAllByText("恢复后的 brief").length),
      );
      restoreButton.focus();
      fireEvent.click(restoreButton);

      await waitFor(() => {
        assert.ok(utils.getAllByText("恢复后的 brief").length);
      });
      const restoredNode = utils.container.querySelector<HTMLElement>(
        "[data-canvas-node='skill-brief']",
      );

      assert.ok(restoredNode);
      assert.equal(dom.window.document.activeElement, canvas);
      fireEvent.keyDown(canvas, { key: "ArrowRight" });
      assert.equal(restoredNode.style.left, "96px");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("fits nodes that have moved into negative canvas space", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    assert.ok(canvas);
    for (let index = 0; index < 5; index += 1) {
      fireEvent.keyDown(canvas, { key: "ArrowLeft", shiftKey: true });
    }
    fireEvent.keyDown(canvas, { key: "Home" });

    assert.match(
      utils.container
        .querySelector("[data-canvas-edge='script-timeline']")
        ?.getAttribute("d") || "",
      /^M 190 107 /,
    );
    assert.equal(
      utils.container.querySelector<HTMLElement>(
        "[data-production-canvas-world='true']",
      )?.style.transform,
      "translate(64px, 24px) scale(0.79) translate(-50px, 0px)",
    );
  });

  it("nudges the selected node with arrow keys", async () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );

    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    assert.ok(canvas);
    assert.ok(scriptNode);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    fireEvent.keyDown(canvas, { key: "ArrowDown" });
    fireEvent.keyDown(canvas, { key: "ArrowRight", shiftKey: true });

    await waitFor(() => {
      assert.equal(scriptNode.style.left, "350px");
      assert.equal(scriptNode.style.top, "80px");
    });
  });

  it("pans the canvas with arrow keys when no node is selected", () => {
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
    fireEvent.keyDown(canvas, { key: "Escape" });
    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(
      world.style.transform,
      "translate(16px, 0px) scale(1) translate(0px, 0px)",
    );

    fireEvent.keyDown(canvas, { key: "ArrowDown", shiftKey: true });
    assert.equal(
      world.style.transform,
      "translate(16px, 64px) scale(1) translate(0px, 0px)",
    );
  });

  it("does not hijack browser-modified arrow shortcuts", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );
    const scriptNode = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='script']",
    );

    fireEvent.click(utils.getByLabelText("Script 短剧节拍、对白和质量门禁"));
    assert.ok(canvas);
    assert.ok(scriptNode);
    fireEvent.keyDown(canvas, { key: "ArrowRight", altKey: true });
    fireEvent.keyDown(canvas, { key: "ArrowRight", ctrlKey: true });
    fireEvent.keyDown(canvas, { key: "ArrowRight", metaKey: true });

    assert.equal(scriptNode.style.left, "270px");
    assert.equal(scriptNode.style.top, "64px");
  });

  it("keeps keyboard control after adding a toolbar note", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.click(utils.getByRole("button", { name: "添加便签" }));
    assert.equal(dom.window.document.activeElement, canvas);
    fireEvent.keyDown(canvas, { key: "ArrowRight" });

    const note = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='note-1']",
    );
    assert.equal(note?.style.left, "281px");
    assert.equal(note?.style.top, "162px");
  });

  it("adds a note with the N keyboard shortcut", () => {
    const utils = render(<ProductionCanvasContent storageKey={null} />, {
      container: dom.window.document.body,
    });
    const canvas = utils.container.querySelector<HTMLElement>(
      "[data-production-canvas='infinite-canvas']",
    );

    assert.ok(canvas);
    fireEvent.keyDown(canvas, { key: "n" });
    const note = utils.container.querySelector<HTMLElement>(
      "[data-canvas-node='note-1']",
    );
    assert.equal(note?.style.left, "265px");
    assert.equal(note?.style.top, "162px");

    fireEvent.keyDown(canvas, { key: "ArrowRight" });
    assert.equal(note?.style.left, "281px");
  });
});
